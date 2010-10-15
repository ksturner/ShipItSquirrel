#!/usr/bin/env python
import cPickle, time
import tweepy
from creds import credentials


#-------------------------------------------------------------------------------
def login():
    ''' Takes our credentials and logs into Twitter using OAuth. A Tweepy
        api object is returned upon success. '''
    consumer_token = credentials['consumer_key']
    consumer_secret = credentials['consumer_secret']
    access_token = credentials['access_token']
    access_token_secret = credentials['access_token_secret']

    api = None
    try:
        auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth) 
    except tweepy.TweepError, e:
        print e
    return api


#-------------------------------------------------------------------------------
def shipit(api=None, replytostatus=None):
    ''' Tweets a status update. '''
    if api is None:
        api = login()
    m = 'Ship it!'  # our status message
    try:
        if replytostatus is None:
            s = api.update_status(m)
        else:
            # If replying, do some extra formatting of the status message.
            sn = replytostatus.user.screen_name
            m = "@%s %s" % (sn, m,)
            s = api.update_status(m, replytostatus.id)
    except tweepy.TweepError, e:
        print e


#-------------------------------------------------------------------------------
def listen_to_friends(api=None, listened=[]):
    ''' Take in a list of tweets we've already replied to and look to see if
        there are new tweets that we need to consider. '''
    if api is None:
        api = login()
    statuses = api.friends_timeline()
    for s in statuses:
        u = s.user
        if u.screen_name.lower() == credentials['screen_name'].lower():
            # we don't want to consider our own messages
            continue

        # Begin any testing of messages to determine if we are going to reply.
        if 'ship' in s.text.lower():
            found = False
            for l in listened:
                if l[0] == u.screen_name and l[1] == s.text:
                    found = True
                    break
            if not found:
                shipit(api, s)
                listened.append([u.screen_name, s.text])


#-------------------------------------------------------------------------------
def update_following(api=None):
    ''' Check our followers list and friended list and if there are 
        differences (people who are following us, but we are not following),
        follow those. '''
    if api is None:
        api = login()

    screen_name = credentials['screen_name']
    try:
        followers = api.friends_ids(screen_name)
        friends = api.followers_ids(screen_name) 
    except tweepy.TweepError, e:
        # Abort if there was an error, we can try again next time.
        return api

    f1 = set(followers) 
    f2 = set(friends)

    diff = f2.difference(f1)
    for id in diff:
        try:
            # Following the user with ID specified by diff.
            api.create_friendship(id)
        except: 
            pass
    return api

#-------------------------------------------------------------------------------
def main():
    try:
        listened = cPickle.load(open('listened.pkl','r'))
    except:
        listened = []
    
    # We're going to loop indefinitely, pausing between checks.
    while True:
        api = update_following()
        listen_to_friends(api, listened) 
        cPickle.dump(listened,open('listened.pkl', 'w'))
        print time.ctime()
        time.sleep(60)
        
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
