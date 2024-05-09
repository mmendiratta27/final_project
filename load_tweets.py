#!/usr/bin/python3

# imports
import sqlalchemy
from sqlalchemy import MetaData
import os
import datetime
import zipfile
import io
import json
import random
import string
import requests

################################################################################
# helper functions
################################################################################

usern_len = 3
pswd_len = 3
url_len = 3
# twitter char limit is 280 (for future ref)
tweet_len = 20


# Download a list of English words
response = requests.get('https://raw.githubusercontent.com/dolph/dictionary/master/popular.txt')
word_list = response.text.splitlines()
alphanumeric_chars = string.ascii_letters + string.digits

def rand_string(split, length):

    return split.join(random.choice(word_list) for _ in range(length))


def create_users(num_users):
    for i in range(num_users):
        usern = rand_string('_', usern_len)
        pswd = rand_string('_', pswd_len)
    
        sql = sqlalchemy.sql.text("""
        INSERT INTO users (username, password) VALUES (:usern, :pswd);
        """)
        res = connection.execute(sql, {
            'usern': usern,
            'pswd': pswd
        })

        print(f"Inserted user {i}: {usern}")


def create_tweets(num_users, num_tweets):
    for i in range(num_tweets):
        tweet = rand_string(' ', tweet_len)
        user = random.randint(1, num_users)

        sql = sqlalchemy.sql.text("""
        INSERT INTO tweets (id_users, text) VALUES (:id_users, :text);
        """)
        res = connection.execute(sql, {
            'id_users': user,
            'text': tweet
        })

        print(f"Tweet {i} Inserted")


def create_urls(num_urls):
    for i in range(num_urls):
        url = rand_string('.', url_len)

        sql = sqlalchemy.sql.text("""
        INSERT INTO urls (url) VALUES (:url);
        """)
        res = connection.execute(sql, {
            'url': url,
        })

        print(f"Url {i} Inserted")

################################################################################
# main functions
################################################################################

if __name__ == '__main__':
    
    # process command line args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--db',required=True)
    parser.add_argument('--num_users', type=int, required=True)    
    parser.add_argument('--num_tweets', type=int, required=True)
    parser.add_argument('--num_urls', type=int, required=True)
    args = parser.parse_args()

    # create database connection
    engine = sqlalchemy.create_engine(args.db, connect_args={
        'application_name': 'load_tweets.py',
        })
    connection = engine.connect()
    
    create_users(args.num_users)
    create_tweets(args.num_users, args.num_tweets)
    create_urls(args.num_urls)
