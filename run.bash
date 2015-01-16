#!/bin/bash
#usage: create usernames.txt then do ./run.bash
#you should have usernames.txt line separated

cat usernames.txt | while read line
do
	echo "Running against username: $line"
	scrapy crawl profiler_spider -a usernames=$line -o out/${line}.json -t json
done

