import pandas as pd
import re

def keyword_based_segmentation(df):  
    '''
    Segments each sentence based on keywords in it. Cuts of information that isn't necessary for semantic analysis.
    
    :param df: DataFrame with columns 'subreddit', 'keyword', 'matched_word', 'comment' and 'mulitple'
    '''
    df_single, df_multiple = df[~df['multiple']], df[df['multiple']]
    segmented_rows = []
    # identify all unique keywords (brands) for detection
    unique_keywords = df_multiple['matched_word'].unique()
    brand_pattern = re.compile('|'.join(re.escape(kw) for kw in unique_keywords), re.IGNORECASE)
    for _, row in df_multiple.iterrows():
        comment = row['comment']
        matched_word = row['matched_word']
        # split comment into sentences using regex to handle different punctuation
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', comment)
        current_segment = []
        current_brand = None
        for sentence in sentences:
            brands_in_sentence = brand_pattern.findall(sentence)
            if matched_word.lower() in map(str.lower, brands_in_sentence):
                if current_brand and current_brand.lower() != matched_word.lower():
                    segmented_rows.append({
                        'subreddit': row['subreddit'],
                        'keyword': row['keyword'],
                        'matched_word': current_brand,
                        'comment': ' '.join(current_segment),
                        'multiple': row['multiple']
                    })
                    current_segment = []
                current_brand = matched_word
                current_segment.append(sentence.strip())
            elif not brands_in_sentence and current_segment:
                current_segment.append(sentence.strip())
        # append the last segment if not empty
        if current_brand and current_segment:
            segmented_rows.append({
                'subreddit': row['subreddit'],
                'keyword': row['keyword'],
                'matched_word': current_brand,
                'comment': ' '.join(current_segment),
                'multiple': row['multiple']
            })

    df_multiple_segmented = pd.DataFrame(segmented_rows)
    df_all = pd.concat([df_single, df_multiple_segmented], ignore_index=True)
    return df_all.sort_values('keyword')


if __name__ == '__main__':
    RUNNABLE = False  # prevent faulty execution and data overwriting

    if RUNNABLE: 
        data = pd.read_json(r'data/filtered.json', orient='records', lines=True)
        segmented = keyword_based_segmentation(data)
        segmented.to_json(r'data/segmented.json', orient='records', lines=True)
        