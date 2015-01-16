# -*- coding: utf-8 -*-

# Scrapy settings for logincrawl project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'hgpscrape'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

CLOSESPIDER_ITEMCOUNT = '1000'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:33.0) Gecko/20100101 Firefox/33.0'
