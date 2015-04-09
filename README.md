Purpose
===

The hgprofiler takes as its input a list of usernames (line-separated) and returns other websites where that username is also used. It is meant to be used as a web reconnaissance tool and is based off of the Profiler module in recon-ng.

Usage
===

1. Create a file usernames.txt of line-separated usernames

Ex: 
```
  username1
  username2
```
2. ./run.bash
3. Your output will be in the out/ directory

Output Format
===

Output is returned as single files in out/ for each user entered into usernames.txt

Ex:
```
memex-punk@memexpunk-VirtualBox:~/memex-dev/workspace/hgprofiler/out$ ls
username1.json  username2.json
```

Each file returns the sites that a user was found in:

```
memex-punk@memexpunk-VirtualBox:~/memex-dev/workspace/hgprofiler/out$ cat username1.json 
[{"username": "username1", "url": "http://favstar.fm/users/username1", "category": "social", "resource": "Favstar"},
{"username": "username1", "url": "https://klout.com/username1", "category": "social", "resource": "Klout"},
{"username": "username1", "url": "https://twitter.com/username1", "category": "social", "resource": "Twitter"},
{"username": "username1", "url": "http://twtrland.com/profile/username1/", "category": "social", "resource": "twtrland"}]
```


Greetz & Props
===

This tool is a faster, scrapy-integrated version of the Profiler module in [recon-ng](https://bitbucket.org/LaNMaSteR53/recon-ng). Many thanks go to Tim Tomes the author of recon-ng and [WebBreacher](http://webbreacher.blogspot.com/), the author of the Profiler module.

Requirements
===

pip install -r requirements.txt
