#!/bin/sh

echo '================================================================================'
echo 'loading tweets'
echo '================================================================================'

time python3 load_tweets.py --db=postgresql://postgres:pass@localhost:13231 --num_users=1000000 --num_tweets=10000000 --num_urls=1000000
