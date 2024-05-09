#!/bin/sh

echo '================================================================================'
echo 'loading tweets'
echo '================================================================================'

time python3 load_tweets.py --db=postgresql://postgres:pass@localhost:13231 --num_users=100 --num_tweets=100 --num_urls=100
