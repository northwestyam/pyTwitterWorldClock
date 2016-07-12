# pyTwitterWorldClock
# This script will get the last 200 tweets (API max) and look for mentions
# of a city.  If the city is found, it will check pytz and tweet back to
# the user its time in 24-hour format!

import requests, requests_oauthlib, sys, json, pytz, datetime, time

consumer_key = 'INSERT CONSUMER KEY HERE'
consumer_secret = 'INSERT CONSUMER SECRET KEY HERE'
access_token = 'INSERT ACCESS TOKEN HERE'
access_secret = 'INSERT ACCESS SECRET TOKEN HERE'

def init_auth():
    # Create OAuth1 authentication instance
    auth_obj = requests_oauthlib.OAuth1(consumer_key,
                                        consumer_secret,
                                        access_token,
                                        access_secret)
    if verify_credentials(auth_obj):
        print('Credentials validated!')
        return auth_obj
    else:
        print('Validation failed!')
        sys.exit(1)

def verify_credentials(auth_obj):
    url = 'https://api.twitter.com/1.1/account/verify_credentials.json'
    response = requests.get(url, auth=auth_obj)
    # If the response is status code 200, we're good to go!
    return response.status_code == 200

def get_mentions(since_id, auth_obj):
    params =    {   'count': 200, # max number of tweets for single request
                    'since_id': since_id,
                    'include_rts': 0, # don't include retweets
                    'include_entities': 'false' }
    url = 'https://api.twitter.com/1.1/statuses/mentions_timeline.json'
    response = requests.get(url, params=params, auth=auth_obj)
    response.raise_for_status()
    return json.loads(response.text)

def process_tweet(tweet):
    username = tweet['user']['screen_name']
    text = tweet['text']
    # filter out tags using @ and #
    words = [x for x in text.split() if x[0] not in ['@', '#']]
    place = ' '.join(words)
    check = place.replace(' ', '_').lower()
    timeZoneFound = False
    for timeZone in pytz.common_timezones:
        timeZone_low = timeZone.lower()
        if check in timeZone_low.split('/'):
            timeZoneFound = True
            break
    if timeZoneFound:
        timezone = pytz.timezone(timeZone)
        time = datetime.datetime.now(timezone).strftime('%H:%M')
        reply = '@{} The time in {} is currently {}'.format(username, place, time)
    else:
        reply = "@{} Sorry, I didn't recognize '{}' as a city".format(username, place)
    print(reply)
    #post_reply(tweet['id'], reply, auth_obj)

def post_reply(reply_to_id, text, auth_obj):
    params = {  'status': text,
                'in_reply_to_status_id': reply_to_id }
    url = 'https://api.twitter.com/1.1/statuses/update.json'
    response = requests.post(url, params=params, auth=auth_obj)
    response.raise_for_status()

if __name__ == '__main__':
    auth_obj = init_auth()
    since_id = 1
    error_count = 0
    while error_count < 15:
        try:
            for tweet in get_mentions(since_id, auth_obj):
                process_tweet(tweet)
                since_id = max(since_id, tweet['id'])
            error_count = 0
        except requests.exceptions.HTTPError as e:
            print('Error: {}'.format(str(e)))
            error_count += 1
        time.sleep(60)
