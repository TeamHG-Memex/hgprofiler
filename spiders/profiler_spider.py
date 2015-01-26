# -*- coding: utf-8 -*-
import scrapy
from scrapy import log
from scrapy import Request
import urllib
import json

class ProfilerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    url = scrapy.Field()
    username = scrapy.Field()
    resource = scrapy.Field()
    category = scrapy.Field()

class ProfilerSpider(scrapy.Spider):
    name = "profiler_spider"

    def __init__(self, usernames):
        self.site_db = json.load(open("profiler_sites.json"))
        self.usernames = usernames.split(",")        
        
    def start_requests(self):
        # create sites lookup table
        matched  = []
        for user in self.usernames:
            print('Looking up data for: %s' % user)
            for site in self.site_db["sites"]:
                url = site['u'] % urllib.quote(user)
                print('Checking: %s' % site['r'])
                try:
                    yield Request(url, 
                                  self.parse_profiler_response,
                                  meta={'dont_redirect': True,
                                        'site' : site,
                                        'user' : user})
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as e:
                    print('%s: %s' % (url, e.__str__()))
                    continue

    def parse_profiler_response(self, response):
        log.msg("Parsing profiler URL %s" % response.url, level = log.INFO)
        # <script src.. xpath should trigger splash request
        site = response.request.meta['site']
        needed_resp_code = response.request.meta['site']['gRC']

        if response.status == int(needed_resp_code):
            print('Codes matched %s %s' % (response.status, needed_resp_code))
            if site['gRT'] in response.body_as_unicode() or site['gRT'] in response.headers:
                print('Probable match: %s' % response.request.url)
                item = ProfilerItem()
                item["username"] = response.request.meta['user']
                item["url"] = response.request.url
                item["resource"] = site['r']
                item["category"]=site['c']
                return item


