import urllib
import json
from scrapy import Request

class HgProfiler(object):

    def __init__(self):
        pass

    def run_profiler(self, usernames):
        # create sites lookup table
        site_db = json.load(open("profiler_sites.json"))

        matched  = []
        for user in usernames:
            flag = False
            print('Looking up data for: %s' % user)
            for site in site_db["sites"]:
                url = site['u'] % urllib.quote(user)
                print('Checking: %s' % site['r'])
                try:
                    yield Request(url, meta={'dont_redirect': True})
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as e:
                    print('%s: %s' % (url, e.__str__()))
                    continue
                if resp.status_code == int(site['gRC']):
                    print('Codes matched %s %s' % (resp.status_code, site['gRC']))
                    if site['gRT'] in resp.text or site['gRT'] in resp.headers:
                        print('Probable match: %s' % url)
                        matched.append(dict(username=user, url=url, resource=site['r'], category=site['c']))
                        flag = True

if __name__ == "__main__":

    usernames = ["mehaase", "acaceres2176"]
    hgp = HgProfiler()
    hgp.run_profiler(usernames)