import httpx
import pandas as pd
import random
import time
from datetime import datetime, timezone

def get_posts_from_2024(endpoint, category='/hot', last_after=None, onlyId=False):
    '''
    This function gathers up to 1000 posts from a specified subreddit endpoint on Reddit. 
    It retrieves posts made within the year 2024 from the current runtime, excluding those posted before 2024. 
    The function can optionally return only the IDs of the posts.

    :param endpoint: String representing the subreddit endpoint in the format '/r/subreddit_name'.
    :param category: Optional string specifying the category of posts to retrieve ('/new', '/hot', or '/top', default is '/hot').
    :param last_after: Optional string indicating the after_post_id to continue scraping from a specific point.
    :param onlyId: Optional boolean. If True, returns a DataFrame with only the post IDs.
    :return: A pandas DataFrame containing all post information or only the IDs if onlyId is True,
             along with the last after_post_id for continuation of scraping.
    '''

    base_url = 'https://www.reddit.com'
    url = base_url + endpoint + category + '.json'
    if category == 'top/?t=year':
        url = base_url + endpoint + '/top/' + '.json?t=year'
    dataset = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    df = None

    for i in range(10): 
        params = {
            'limit' : 100,  # Max. amount of items per round, limited by the offical endpoint
            't' : 'year',  # Only get posts that have been made during the last year (starting at runtime)
            'after' : last_after  # after_post_id for next search iteration (each search is only about 25 items)
        }
        try:
            response = httpx.get(url, params = params, headers=headers)
            json_data = response.json()
            dataset.extend([rec['data'] for rec in json_data['data']['children']])
            last_after = json_data['data']['after']
            print(f'Fetched {100 * i + 100} posts :)')
            # Filtering out all posts made before 01.01.2024
            df = pd.DataFrame(dataset)
            start_date = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
            df['created'] = df['created'].astype(float) 
            df = df[df['created'] >= start_date]
            if onlyId:
                df = df[['id']]
        except: 
            print('Failed to fetch posts :(')
            #raise
        
        sleeptime = float(random.randrange(2, 5))  # random sleeptime to be "less suspicious"
        time.sleep(sleeptime)
    
    return df


def get_comments(post_id):
    '''
    'Retrieves top-level comments associated with a Reddit post identified by post_id, excluding nested replies.'

    :param post_id: String representing the unique identifier of the Reddit post.
    :return: A pandas DataFrame containing subreddit and main comment body for each retrieved comment.
    '''
    base_url = 'https://www.reddit.com/comments/'
    url = base_url + post_id + '.json'
    dataset = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    df = None

    try:
        response = httpx.get(url, headers=headers)
        json_data = response.json() 
        comments_data = json_data[1]['data']['children']
        dataset.extend([comment['data'] for comment in comments_data])
        df = pd.DataFrame(dataset)[['subreddit', 'body']]
        print('Fetched comments :)')
    except:
        print('Failed to fetch comments :(')

    return df
