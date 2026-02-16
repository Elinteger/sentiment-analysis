import pandas as pd
import random
import re
import reddit_scraper as reddit
import time
import unicodedata
from rapidfuzz import fuzz

def reformat_old_comments_to_df():
    '''
    Reformat old comments from specified files into a single DataFrame.
    The comments are read from .ndjson files and concatenated into a unified DataFrame.

    :return: DataFrame containing the reformatted comments with columns 'subreddit' and 'body'.
    '''
    file_paths = ['bicycling_comments.ndjson', 'cycling_comments.ndjson', 'roadBikes_comments.ndjson']
    all_comments_df = pd.DataFrame()

    for file_path in file_paths:
        df = pd.read_json('data/subreddits08-23/' + file_path, lines=True)
        all_comments_df = pd.concat([all_comments_df, df], ignore_index=True)
    
    all_comments_df = all_comments_df[['subreddit', 'body']]
    return all_comments_df


def get_comments_from_2024():
    '''
    Retrieve comments from Reddit posts in specified subreddits for the year 2024.
    Due to Reddit endpoint limitations, only comments from up to 9000 posts can be fetched.

    :return: DataFrame containing the comments from the retrieved posts.
    '''
    endpoints = ['/r/bicycling', '/r/cycling', '/r/RoadBikes']
    categories = ['/hot', '/new', 'top/?t=year']
    all_post_ids = pd.DataFrame()
    for endpoint in endpoints:
        for category in categories:
            current_post_ids = reddit.get_posts_from_2024(endpoint, category, onlyId=True)
            all_post_ids = pd.concat([all_post_ids, current_post_ids]).reset_index(drop=True)
            time.sleep(20)

    all_post_ids = all_post_ids.drop_duplicates(subset='id').reset_index(drop=True)
    all_post_ids.to_json(r'data/subreddits24/ids.json')

    time.sleep(120)  # snoozing time, wait before starting to fetch comments

    ids_list = all_post_ids['id'].tolist()
    all_comments_df = pd.DataFrame()
    for number, id in enumerate(ids_list):
        if number % 5 == 0:
            time.sleep(30)
        comments = reddit.get_comments(id)
        all_comments_df = pd.concat([all_comments_df, comments]).reset_index(drop=True)
        if number % 25 == 0:
            all_comments_df.to_json(r'data/subreddits24/new_comments_temp.json')
        sleeptime = float(random.randrange(0, 2))  # random sleeptime to be less suspicious
        time.sleep(sleeptime)
    return all_comments_df


def prepare_for_analysis(keywords_to_include, no_lowercase_keywords, dataframe_to_filter):
    '''
    Filter comments in a DataFrame to include only those mentioning specific keywords.
    This process also normalizes unicode characters and removes URLs from the comments.
    Comments mentioning multiple keywords are returned multiple times, once for each keyword found.
    Comments of Keywords which are found less than 100 times are removed.

    :param keywords_to_include: List of keywords to search for in the comments.
    :param dataframe_to_filter: DataFrame containing the comments to be filtered.
                                Must have columns 'body' and 'subreddit'.
    :return: DataFrame with rows representing comments that mention at least one of the keywords.
             Columns include 'subreddit', 'keyword', 'matched_word', and 'comment'.
    '''
    df = dataframe_to_filter.copy()
    df['body'].fillna('', inplace=True)
    df['body'] = df['body'].apply(lambda b: preprocess_text(b))
  
    # filter comments that mention any of the specified keywords
    # if multiple keywords are found, comments are returned multiple times with a different keyword each time
    all_matches = []
    for _, row in df.iterrows():
        comment = row['body']
        subreddit = row['subreddit']
        matches = contains_keyword(subreddit, comment, keywords_to_include.copy())
        all_matches.extend(matches)
    match_df = pd.DataFrame(all_matches)
    cleared_df = clear_of_lowercase(match_df, no_lowercase_keywords)
    threshed_df = remove_brand_by_threshold(cleared_df)
    return_df = threshed_df
    comment_counts = return_df['comment'].value_counts()
    return_df['multiple'] = return_df['comment'].apply(lambda x: comment_counts[x] > 1)

    return return_df

# --- helper functions --- 
def preprocess_text(text):
    '''
    Preprocess text by normalizing unicode characters, removing URLs, and cleaning up special characters.

    :param text: String containing the text to be preprocessed.
    :return: String with the text preprocessed.
    '''
    text = normalize_unicode(text)
    text = remove_urls(text)
    text = remove_special_chars(text)
    return text


def normalize_unicode(text):
    '''
    Normalize unicode characters in a given text to ASCII.
    
    :param text: String containing the text to be normalized.
    :return: String with unicode characters normalized to ASCII.
    '''
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')


def remove_urls(text):
    '''
    Remove all URLs from a given text.

    :param text: String containing the text from which URLs will be removed.
    :return: String with all URLs removed.
    '''
    return re.sub(r'http\S+', '', text)


def remove_special_chars(text):
    '''
    Remove special characters that are not useful for sentiment analysis.

    :param text: String containing the text from which special characters will be removed.
    :return: String with special characters removed.
    '''
    text = re.sub(r'\\n', ' ', text)  # replace '\n' with space
    text = re.sub(r'\\r', ' ', text)  # replace '\r' with space
    text = re.sub(r'[\/]', ' ', text) # replace '/' with space
    text = re.sub(r'\s+', ' ', text)  # normalize whitespace
    return text


def contains_keyword(subreddit, comment, keywords):
    '''
    Recursively searches for all keywords in a given comment.
    Allows for typos and is not case-sensitive.

    :param subreddit: String representing the subreddit the comment is taken from.
    :param comment: String to be parsed for keywords.
    :param keywords: List of keywords to search for.
    :return: List of dictionaries in JSON-like format with the shape 
             [{'subreddit': subreddit, 'keyword': keyword, 'matched_word': matched_word, 'comment': comment}]. 
             One dictionary for each keyword found.
    '''
    MIN_SCORE = 85
    words = comment.lower().split()
    best_score = 0
    best_match = None
    matched_word = None

    for keyword in keywords:
        for word in words:
            score = fuzz.ratio(word, keyword.lower())
            if score > MIN_SCORE and score > best_score:
                best_score = score
                best_match = keyword
                matched_word = word
    
    if best_match:
        keywords.remove(best_match) 
        # recursively call contains_keyword to find the second match
        second_match = contains_keyword(subreddit, comment, keywords)
        match_data = [{'subreddit': subreddit, 'keyword': best_match, 'matched_word': matched_word, 'comment': comment}]
        if second_match:
            match_data.extend(second_match)
        return match_data
    return []


def clear_of_lowercase(df, keywords):
    '''
    Removes rows from the DataFrame if a lowercase version of the matched_word 
    is found in the comment for the specified keywords.

    :param df: DataFrame with columns 'keyword', 'matched_word', and 'comment'
    :param keywords: List of keywords to check
    :return: DataFrame with specified rows removed
    '''
    indices_to_drop = []

    for idx, row in df.iterrows():
        if row['keyword'] in keywords and row['matched_word'] in row['comment']: 
            indices_to_drop.append(idx)

    df = df.drop(indices_to_drop).reset_index(drop=True)
    return df


def remove_brand_by_threshold(df):
    '''
    Removes rows of keywords that appear fewer than 100 times in the DataFrame.

    :param df: DataFrame with columns 'keyword', 'matched_word', and 'comment'
    :return: DataFrame with rows of infrequent keywords removed
    '''
    THRESHOLD = 100
    counts = df['keyword'].value_counts()
    rare_brands = counts[counts < THRESHOLD].index
    print(f'Deleted brands: {rare_brands.tolist()}')
    filtered_df = df[~df['keyword'].isin(rare_brands)]
    return filtered_df


def calculate_percentage_with_brands(filtered_df, brands):
    '''
    Calculate the percentage of comments that mention any of the specified brands.
    This function is case-sensitive.

    :param filtered_df: DataFrame containing a column named 'comment'.
    :param brands: List of brands to search for within the comments.
    :return: The percentage of comments that mention at least one of the specified brands.
    '''
    num_total_comments = filtered_df.shape[0]
    num_comments_with_brands = sum(filtered_df['comment'].apply(lambda b: any(word in b.split() for word in brands)))
    percentage_with_brands = (num_comments_with_brands / num_total_comments) * 100
    return percentage_with_brands


if __name__ == '__main__':
    RUNNABLE = False  # prevent faulty execution and data overwriting

    if RUNNABLE:
        brands = ['Argon 18',
                   'Bianchi', 'BMC',
                     'Cannondale', 'Canyon', 'Cervelo', 'Cinelli', 'Colnago', 'Cube',
                       'Giant',
                         'Merida',
                           'Orbea',
                             'Pinarello',
                               'Ridley', 'Rose',
                                 'Scott', 'Specialized',
                                   'Trek',
                                     'Ventum',
                                       'Wilier']
        
        no_lowercase = ['Cube', 'Giant', 'Rose']  # found by testing
        # load and save Reddit comments from June 2005 to June 2024
        old_comments_df = reformat_old_comments_to_df()
        old_comments_df.to_json(r'data/old_comments.json')  # better safe than sorry
        new_comments_df = get_comments_from_2024()
        new_comments_df.to_json(r'data/new_comments_temp.json')  # better safe than sorry
        combined_df = pd.concat([old_comments_df, new_comments_df], ignore_index=True)
        filtered_df = prepare_for_analysis(brands, no_lowercase, combined_df)
        filtered_df.to_json(r'data/filtered.json', orient='records', lines=True)
        
        print(calculate_percentage_with_brands(filtered_df, brands)) 
