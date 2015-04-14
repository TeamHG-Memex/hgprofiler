from __future__ import division

from lib.trawler.twitter_crawler import  (CrawlTwitterTimelines, FindFriendFollowers, 
                                          RateLimitedTwitterEndpoint, Twython)

from collections import defaultdict

class Trawler:
    def __init__(self, consumer_key, consumer_secret):
        """
        Given the access tokens, provide active connections.
        """

        ACCESS_TOKEN = Twython(consumer_key, consumer_secret, oauth_version=2).obtain_access_token()
        twython = Twython(consumer_key, access_token=ACCESS_TOKEN)

        self.timeline_crawler = CrawlTwitterTimelines(twython)
        self.ff_finder = FindFriendFollowers(twython)


    def names_of_interest(self, names_of_interest):
        """
        Pass in a list of screen names as `names_of_interest`. These
        will be used to generate all scores and filter all matches for the
        rest of the module.
        """
        self.names_of_interest = set([x.lower() for x in names_of_interest])

    def get_ffs(self, screen_name ):
        """
        Query the API for people who are both friends-and-followers of `screen_name`
        NB: this will block if you run out of twitter calls
        """
        ffs = self.ff_finder.get_ff_screen_names_for_screen_name(screen_name)
        return ffs
        
    def get_atmentions(self, screen_name, return_tweets=False):
        """
        Query the API for people who `screen_name` @mentions.
        Will return a dictionary of {screen_name:count}
        NB: this will block if you run out of twitter calls
        NB: you can actually get all of this' person's tweets here, currently dumped on the floor
        If `return_tweets` is True, it will return a compound object: 
        ({screen_name:count},[{tweet},{tweet},...])
        """
        tweets = self.timeline_crawler.get_all_timeline_tweets_for_screen_name(screen_name)
        atmentions = defaultdict(int) #Count up each person mentioned here
        for t in tweets:
            ents = t.get('entities',{})
            mentions = ents.get('user_mentions',[])
            screen_names = [m['screen_name'] for m in mentions]
            for s in screen_names:
                atmentions[s] += 1
        if return_tweets:
            return (atmentions,tweets)
        return atmentions

    def find_neighbors(self, screen_name):
        """ 
        Query the API for people who are connected to `screen_name` either via
        @mentions (in their last 3200 tweets) or their friends and followers.
        NB: this will block if you run out of twitter calls
        """
        atneighbors = self.get_atmentions(screen_name)
        ffs = self.get_ffs(screen_name)
        neighbors = set([x.lower() for x in atneighbors.keys()]).union(set([x.lower() for x in ffs]))
        return neighbors

    def find_neighbors_of_interest(self, screen_name):
        """
        Query the API for neighbors, and see which ones are in the
        users passed as `names_of_interest`.
        NB: this will block if you run out of twitter calls
        """
        neighbors = self.find_neighbors(screen_name)
        return neighbors.intersection(self.names_of_interest)
        

if __name__ == '__main__':
    from lib.trawler.twitter_oauth_tokens import consumer_key, consumer_secret
    #print consumer_key, consumer_secret
    trawler = Trawler(consumer_key, consumer_secret)
    trawler.names_of_interest(['DotSlashPunk','HyperionGray','j2labs'])
    print trawler.find_neighbors_of_interest('glencoppersmith')
