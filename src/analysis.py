import pandas as pd
from reddit_scraper import remove_brand_by_threshold
from tqdm import tqdm
from transformers import pipeline

def analyse_sentiment(data):
    '''
    Analyze sentiment of comments using a pre-trained model from Hugging Face.

    :param data: DataFrame containing comments.
    :return: DataFrame with sentiment analysis results.
    '''
    batch_size = 256
    results = []

    for i in tqdm(range(0, len(data), batch_size)):
        batch = data['comment'][i:i+batch_size].tolist()
        batch_results = sentiment_task(batch)
        results.extend(batch_results)

    analytics = pd.DataFrame(data)
    analytics['sentiment'] = [result['label'] for result in results]
    analytics['score'] = [result['score'] for result in results]
    
    return analytics


def filter_sentiment(data):
    '''
    Filter sentiment analysis results based on score and neutrality.

    :param data: DataFrame with sentiment analysis results.
    :return: Filtered DataFrame.
    '''
    filtered = data[(data['score'] >= 0.500) & (data['sentiment'] != 'neutral')]
    filtered = remove_brand_by_threshold(filtered)
    return filtered


if __name__ == '__main__':
    RUNNABLE = False  # prevent faulty execution and data overwriting

    if RUNNABLE:
        model_path = 'cardiffnlp/twitter-roberta-base-sentiment-latest'
        sentiment_task = pipeline("sentiment-analysis", model=model_path, tokenizer=model_path, device=0, max_length=512, truncation=True)
        
        data = pd.read_json(r'data/segmented.json', orient='records', lines=True)
        sentiment = analyse_sentiment(data)

        filtered = filter_sentiment(sentiment)
        filtered.to_json(r'data/sentiment_filtered.json', orient='records', lines=True)
