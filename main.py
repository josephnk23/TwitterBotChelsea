import tweepy
import schedule
import requests
from PIL import Image
import io
import time
import os
import random
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
bearer_token = os.getenv("BEARER_TOKEN")
access_token =os.getenv("ACCESS_TOKEN")
access_token_secret =os.getenv("ACCESS_TOKEN_SECRET")

openapikey = os.getenv("OPENAPIKEY")
userid = os.getenv("USERID")
football_data_api_key = os.getenv("FOOTBALL_DATA_API_KEY")



#Function to fetch and post tweets
tweeted_titles = set()
def fetch_news_and_tweet():
    # Keep track of the number of tweets posted today
    if not hasattr(fetch_news_and_tweet, "daily_tweet_count"):
        fetch_news_and_tweet.daily_tweet_count = 0

    if fetch_news_and_tweet.daily_tweet_count >= 20:
        return

    url = ('https://newsapi.org/v2/everything?'
        'q=Chelsea&'
        'from=2023-08-23'
        'sortBy=popularity&'
        'language=en&'
         f'apiKey={football_data_api_key}')


    response = requests.get(url)

    articles = response.json()['articles'][0:6]
   
    for article in articles:
         title = article['title']
         if "Chelsea" in title and title not in tweeted_titles:
            tweet = f"{article['title']} {article['url']}"
            client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
            try:
                client.create_tweet(text=tweet)
                # Increment the daily tweet count
                fetch_news_and_tweet.daily_tweet_count += 1
                # Add the article title to the set of tweeted titles
                tweeted_titles.add(title)
            except tweepy.TweepError as e:
                print("Error:", e)


# Function to fetch Chelsea news, process, and post tweets
def fetch_and_post_news():
    # Keep track of the number of tweets posted today
    if not hasattr(fetch_and_post_news, "daily_tweet_count"):
        fetch_and_post_news.daily_tweet_count = 0

    if fetch_and_post_news.daily_tweet_count >= 15:
        return

    feed_urls = [
        "https://weaintgotnohistory.sbnation.com/rss/current",
        "https://talkchelsea.net/feed/",
    ]

    for feed_url in feed_urls:
        # Parse the RSS feed
        feed = feedparser.parse(feed_url)

        # Iterate over the entries in reverse order (oldest to newest)
        for entry in reversed(feed.entries):
            # Check if the daily tweet count limit has been reached
            if fetch_and_post_news.daily_tweet_count >= 15:
                return

            # Extract the title of the entry
            title = entry.title

            # Remove the "Opinion:" prefix if present
            if "Opinion:" in title:
                title = title.split("Opinion:", 1)[1].strip()

            # Compose the tweet text
            tweet_text = f"{title} {entry.link}"

            # Authenticate with Twitter API
            client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)

            # Post the tweet
            try:
                client.create_tweet(text=tweet_text)
                # Increment the daily tweet count
                fetch_and_post_news.daily_tweet_count += 1
            except tweepy.TweepError as e:
                print("Error:", e)



def get_random_image_from_folder(folder_path):
    photo_files = [file for file in os.listdir(folder_path) if file.endswith(('.jpg', '.png', '.jpeg'))]
    if not photo_files:
        return None
    random_image = random.choice(photo_files)
    return os.path.join(folder_path, random_image)


def get_twitter_conn_v1(api_key, api_secret, access_token, access_token_secret) -> tweepy.API:
    

    auth = tweepy.OAuth1UserHandler(api_key, api_secret)
    auth.set_access_token(
        access_token,
        access_token_secret,
    )
    return tweepy.API(auth)

def get_twitter_conn_v2(api_key, api_secret, access_token, access_token_secret) -> tweepy.Client:
   

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )

    return client

client_v1 = get_twitter_conn_v1(api_key, api_secret, access_token, access_token_secret)
client_v2 = get_twitter_conn_v2(api_key, api_secret, access_token, access_token_secret)

# Set the path to your photos folder
photos_folder = "photos"

# Get a random image from the photos folder
image_path = get_random_image_from_folder(photos_folder)
file_name_with_extension = os.path.basename(image_path)
name_without_extension = os.path.splitext(file_name_with_extension)[0]
extracted_name = name_without_extension

def tweetfunc():
    media = client_v1.media_upload(filename=image_path)
    media_id = media.media_id
    client_v2.create_tweet(text=extracted_name, media_ids=[media_id])



# Function to check if it's a matchday based on the schedule in the text file
def is_matchday():
    txt_file_name = "matches.txt"
    try:
        with open(txt_file_name, "r") as file:
            schedule_data = file.read().splitlines()

        current_day = time.strftime("%Y-%m-%d", time.gmtime())

        if any(current_day in line for line in schedule_data):
            return True

    except FileNotFoundError:
        print(f"{txt_file_name} not found. Please run the script to fetch the schedule.")
    except Exception as e:
        print("Error reading text file:", e)

    return False

# Function to get live scores for Chelsea FC from the Football Data API and tweet them
def get_live_scores():
    url = f"https://api.football-data.org/v2/teams/61/matches?status=LIVE"
    headers = {"X-Auth-Token": football_data_api_key}

    previous_score = None
    previous_status = None

    try:
        while True:
            response = requests.get(url, headers=headers)
            data = response.json()
            matches = data["matches"]

            for match in matches:
                home_team = match["homeTeam"]["name"]
                away_team = match["awayTeam"]["name"]
                status = match["status"]
                
                home_team_score = match["score"]["fullTime"]["homeTeam"]
                away_team_score = match["score"]["fullTime"]["awayTeam"]
                live_score = f"{home_team_score} - {away_team_score}"

                
               
                client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
               
                score = f"{home_team} {live_score} {away_team}"

                if status == "SCHEDULED" or status == "TIMED":
                        # Match is scheduled to start, you can tweet the kick-off score
                        tweet = f"🔵 Kick-off Score: {score} 🔵 #ChelseaFC #PL"
                        client.create_tweet(text=tweet)
                        client.create_tweet(text='Who will win?🤔',poll_options=[f"{home_team}", f"{away_team}"],poll_duration_minutes=30)                         
                elif status == "IN_PLAY" and status != previous_status:
                        # Match starts
                        tweet = f"🔵 Match Starts: {score} 🔵 #ChelseaFC #PL"
                        client.create_tweet(text=tweet)

                elif status == "PAUSED" and status != previous_status:
                        # Half time
                        tweet = f"🔵 Half Time: f'{home_team} {match['score']['halfTime']['homeTeam']} - {match['score']['halfTime']['awayTeam']} {away_team}'🔵 #ChelseaFC #PL"
                        client.create_tweet(text=tweet)

                elif status == "FINISHED" and status != previous_status:
                        # Full time
                        tweet = f"🔵 Full Time: {score} 🔵 #ChelseaFC #PL"
                        client.create_tweet(text=tweet)

                elif status == "IN_PLAY" and live_score != previous_score:
                        # Score changes during the match
                        tweet = f"🔵 Live Score Update: {score} 🔵 #ChelseaFC #PL"
                        client.create_tweet(text=tweet)

                previous_status = status
                previous_score = live_score

            # Wait for a minute before checking the live scores again
            time.sleep(60)

    except requests.exceptions.RequestException as e:
        print("Error fetching live scores:", e)

# Schedule the fetch_news_and_tweet task to run every 80 minutes
schedule.every(80).minutes.do(fetch_news_and_tweet)
# Schedule the fetch_and_post_news task to run every hour at 00:00
schedule.every().hour.at(":00").do(fetch_and_post_news)
schedule.every().day.at("22:13").do(tweetfunc)


def run_scheduled_tasks():
    try:
        # Check if the current day has changed
        current_day = datetime.now().day
        if not hasattr(fetch_and_post_news, "last_day") or fetch_and_post_news.last_day != current_day:
            fetch_and_post_news.last_day = current_day
            # Reset the daily tweet count for the new day
            fetch_and_post_news.daily_tweet_count = 0
            # Reset the daily tweet count for fetch_news_and_tweet
            fetch_news_and_tweet.daily_tweet_count = 0

        # Run pending scheduled tasks
        schedule.run_pending()
        time.sleep(1)

    except Exception as e:
        print("Error running scheduled tasks:", e)


# Main function to run all tasks
def main():
    while True:
        if is_matchday():
            get_live_scores()
        run_scheduled_tasks()

if __name__ == "__main__":
    main()

