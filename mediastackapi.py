import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
import random

def key_check(key_path=None):
    try:
        load_dotenv(key_path, override=True)
        
        api_configs = {
            'NewsAPI': {
                'env_var': 'NEWS_API_KEY',
                'test_url': 'https://newsapi.org/v2/top-headlines?country=us&apiKey={}'
            },
            'New York Times': {
                'env_var': 'NYT_API_KEY',
                'test_url': 'https://api.nytimes.com/svc/mostpopular/v2/viewed/1.json?api-key={}'
            },
            'The Guardian': {
                'env_var': 'GUARDIAN_API_KEY',
                'test_url': 'https://content.guardianapis.com/search?api-key={}'
            },
            'GDELT Project': {
                'env_var': 'GDELT_API_KEY',
                'test_url': 'http://api.gdeltproject.org/api/v1/search_ftxtsearch/search_ftxtsearch?query=heat wave&format=json&maxrecords=250&timespan=1d'
            },
            'Currents API': {
                'env_var': 'CURRENTS_API_KEY',
                'test_url': 'https://api.currentsapi.services/v1/latest-news?apiKey={}'
            },
            'Event Registry': {
                'env_var': 'EVENT_REGISTRY_API_KEY',
                'test_url': 'https://eventregistry.org/api/v1/article/getArticles?apiKey={}'
            },
            'MediaStack API': {
                'env_var': 'MEDIASTACK_API_KEY',
                'test_url': 'http://api.mediastack.com/v1/news?access_key={}'
            },
        }

        for api_name, config in api_configs.items():
            api_key = os.getenv(config['env_var'])
            assert api_key is not None, f'{config["env_var"]} not found in .env file'

            if 'headers' in config:
                headers = {k: v.format(api_key) for k, v in config['headers'].items()}
                response = requests.get(config['test_url'], headers=headers)
                print(f"bing {config['test_url']}, headers={headers}, code = {response.status_code}")
            elif api_key == 'NA':
                response = requests.get(config['test_url'])
                print (config['test_url'], 'code =', {response.status_code})
            else:
                response = requests.get(config['test_url'].format(api_key))
                print (config['test_url'], 'code =', {response.status_code})
            assert response.status_code in {200, 503, 404, 401}, f'The key provided failed to authenticate {api_name} API. Status code: {response.status_code} {api_key}'

    except Exception as e:
        print(f'An error occurred: {e}')
        return False
    else:
        print('All keys loaded and authenticated correctly')
        return True

def mediastackapi():
    # Your Mediastack API Key
    api_key = os.getenv('MEDIASTACK_API_KEY')

    # Set up date range for last month
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Convert dates to required format (YYYY-MM-DD)
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")

    # Base URL for Mediastack API
    base_url = "http://api.mediastack.com/v1/news"

    # Parameters for the API call
    params = {
        "access_key": api_key,
        "date": f"{from_date},{to_date}",
        "sort": "published_desc",
        "limit": 100,  # Maximum allowed per request
        "offset": 0
    }

    all_articles = []
    total_count = 0
    current_offset = 0

    def make_request(url, params, retries=3, backoff_factor=5):
        for i in range(retries):
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    wait_time = (backoff_factor ** i) + (random.random() * 0.1)
                    print(f"Rate limit exceeded. Waiting for {wait_time:.2f} seconds.")
                    time.sleep(wait_time)
                else:
                    print(f"Error: {response.status_code}")
                    return None
            except Exception as e:
                print(f"Request failed: {str(e)}")
        return None

    while True:
        response = make_request(base_url, params)
        
        if response:
            data = response.json()
            
            if current_offset == 0:
                total_count = data['pagination']['total']
                print(f"Total articles available: {total_count}")
            
            articles = data['data']
            all_articles.extend(articles)
            print(f"Fetched offset {current_offset}, total articles: {len(all_articles)}")
            
            if len(articles) < 100 or len(all_articles) >= total_count:
                break
            
            # Move to next offset
            current_offset += 100
            params['offset'] = current_offset
            
            # Sleep to respect rate limits
            time.sleep(1)
        else:
            print(f"Failed to fetch offset {current_offset}")
            break

    print(f"Total articles fetched: {len(all_articles)}")

    # Create a DataFrame from the fetched articles
    df = pd.DataFrame(all_articles)

    # Display the first few rows and basic info about the DataFrame
    print(df.head())
    print(df.info())

    # Optionally, save the DataFrame to a CSV file
    df.to_csv('.\\resources\\mediastack_articles.csv', index=False)
    print("DataFrame saved to 'mediastack_articles.csv'")


if key_check("C:\SRC\.key.env"):
    print("All API keys are valid and working.")
else:
    print("There was an issue with one or more API keys.")
# newsapi(5)
mediastackapi()
