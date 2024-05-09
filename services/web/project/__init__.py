import os

from flask import Flask, render_template, jsonify, send_from_directory, request, make_response, redirect, Markup
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import sqlalchemy
import re

from contextlib import contextmanager

app = Flask(__name__)
app.config.from_object("project.config.Config")
db = SQLAlchemy(app)
db_url = "postgresql://postgres:pass@postgres:5432"

#engine = sqlalchemy.create_engine(db_url, connect_args={
#        'application_name': '__init__.py root()',
#        })

#connection = engine.connect()

#class User(db.Model):
#    __tablename__ = "users"
#
#    id = db.Column(db.Integer, primary_key=True)
#    email = db.Column(db.String(128), unique=True, nullable=False)
#    active = db.Column(db.Boolean(), default=True, nullable=False)
#
#    def __init__(self, email):
#        self.email = email

@contextmanager
def get_connection():
    """
    This function helps build the connection with the databases so SQL commands can run, then finally, it closes the connection.
    """
    engine = sqlalchemy.create_engine(db_url)
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()

def are_cred_good(username, password):
    print(username, password)    
    sql = sqlalchemy.sql.text('''
        SELECT username
        FROM users
        WHERE username = :username
          AND password = :password
        LIMIT 1;
    ''')
    with get_connection() as connection:
        cred = connection.execute(sql, {
            'username': username,
            'password': password
        })
    
    if cred.fetchone() is not None:
        return True
    else:
        return False

def fetch_tweets(page_num):
    tweets = []
    sql = sqlalchemy.sql.text('''
        SELECT users.username, tweets.created_at, tweets.text
        FROM users
        JOIN tweets USING (id_users)
        ORDER BY tweets.created_at DESC
        LIMIT 20
        OFFSET :offset
    ''')

    offset = (page_num - 1) * 20 # 0 offset for page 1


    print(f"called fetch with page # : {page_num} and offset: {offset}")
    
    with get_connection() as connection:
        page = connection.execute(sql, {
            'offset': offset
        })

    for post in page.fetchall():
        tweets.append({
            'username': post[0],
            'created_at': post[1].strftime("%d-%m-%Y  %H:%M"),
            'text': post[2]
        })
    return tweets


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.cookies.get('username')
    password = request.cookies.get('password')

    good_cred = are_cred_good(username, password)

    print(f"username: {username}, password: {password}, goodcred {good_cred}")

    if good_cred:
        return redirect('/')
    
    
    username = request.form.get('username')
    password = request.form.get('password')

    good_cred = are_cred_good(username, password)
    print(f"username: {username}, password: {password}, goodcred {good_cred}")

    # the first time we've visited, no form submission 
    if username is None:
        return render_template('login.html', bad_cred=False)

    #submitted a form (on the post method)
    else:
        if not good_cred:
           return render_template('login.html', bad_cred=True)
        else:
           response = make_response(redirect('/'))
           response.set_cookie('username', username)
           response.set_cookie('password', password)
            
           return response


@app.route('/logout')
def logout():
    # Clear the login cookies by setting an empty value and an expiry time in the past
    response = make_response(render_template('logout.html'))
    response.set_cookie('username', '', expires=0)
    response.set_cookie('password', '', expires=0)

    return response

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():

    username = request.form.get('username')
    pswd1 = request.form.get('pswd1')
    pswd2 = request.form.get('pswd2')

    # before form
    if username is None:
        return render_template('create_account.html')
    # all sections not filled
    elif not (username and pswd1):
        return render_template('create_account.html', not_valid = True)
    else:
        if pswd1 != pswd2:
            return render_template('create_account.html', diff_pswd = True)
        else:
            try:
                with get_connection() as connection:
                    transaction = connection.begin()
                    sql = sqlalchemy.sql.text('''
                        INSERT INTO users (username, password)
                        VALUES (:username, :password);
                        ''')

                    res = connection.execute(sql, {
                        'username': username,
                        'password': pswd1
                    })
                    transaction.commit()
                print(f"INSERTED {username} and {pswd1}")
                response = make_response(redirect('/'))
                response.set_cookie('username', username)
                response.set_cookie('password', pswd1)

                return response

            except sqlalchemy.exc.IntegrityError:
                return render_template('create_account.html', acct_exists= True)

@app.route('/create_tweet', methods = ['GET', 'POST'])
def create_tweet():
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    with get_connection() as connection:
        sql = sqlalchemy.sql.text('''
            SELECT id_users FROM users
            WHERE username = :username
            AND password = :password
            LIMIT 1; 
            ''')
        res = connection.execute(sql, {
            'username': username,
            'password': password
        })
    id_user = res.fetchone()[0]

    print(id_user)

    tweet = request.form.get('tweet')
    print("tweet:", tweet)
    if not tweet:
        return render_template('create_tweet.html', no_words=False, logged_in = True)
    elif len(tweet.replace(" ", "")) == 0:
        return render_template('create_tweet.html', no_words = True, logged_in = True)

    try:
        with get_connection() as connection:
            transaction = connection.begin()
            try:
                sql = sqlalchemy.sql.text("""
                    INSERT INTO tweets (
                        id_users,
                        created_at,
                        text
                    ) VALUES (
                        :id_users,
                        NOW(),
                        :tweet);
                """)
                print("Executing SQL...")
                connection.execute(sql, {'id_users': id_user, 'tweet': tweet})
                transaction.commit()
                print("SQL done successfully")
            except Exception as e:
                print("INTERNAL TRY", e)
    except Exception as e:
        print("EXTERNAL TRY", e)
    return render_template('create_tweet.html', posted=True, logged_in = True)

def get_search(search_word, page_num):
    tweets = []

    offset = (page_num - 1) * 20
    sql = sqlalchemy.sql.text("""
        SELECT tweets.text, users.username, tweets.created_at
        FROM tweets
        JOIN users USING (id_users)
        WHERE to_tsvector('english', tweets.text) @@ phraseto_tsquery(:search_word)
        ORDER BY to_tsvector('english', tweets.text) <=> phraseto_tsquery(:search_word), created_at DESC, id_tweets DESC
        LIMIT 20 OFFSET :offset;
    """)
    with get_connection() as connection:
        search_word = ' '.join(search_word.strip().split())
        print("search word is ", search_word)

        res = connection.execute(sql, {
            'offset': offset,
            'search_word': f'{search_word}'})
        
        regex = re.compile(re.escape(search_word), re.IGNORECASE)
        for row in res:
            highlighted_text = Markup(regex.sub(lambda match: f'<mark>{match.group(0)}</mark>', row.text))
            tweets.append({'text': highlighted_text, 'created_at': row.created_at.strftime("%d-%m-%Y  %H:%M"), 'username': row.username})
 
        return tweets

@app.route('/search')
def search():
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    good_cred = are_cred_good(username, password) 

    page_num = request.args.get('page_num', 1, type=int)
    
    search_word = request.args.get('search_word', '')
    tweets = None
    if search_word:
        tweets = get_search(search_word, page_num)
#    else:
#        tweets = fetch_tweets(page_num)
  
    if not tweets:
        print("No search results")
        render_template('search.html', logged_in = good_cred, tweets = False, page_num = page_num, search_word = search_word)
    return render_template('search.html', logged_in = good_cred, tweets = tweets, page_num = page_num, search_word = search_word)

@app.route('/')
def root():
    messages = [{}]

    # check if logged in
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    good_cred = are_cred_good(username, password)
    
    print(f"username {username} password {password} good {good_cred}")
    page_num = request.args.get('page_num', 1, type=int)

    tweets = fetch_tweets(page_num)
    page_full = True if len(tweets) == 20 else False 
    return render_template('root.html', logged_in = good_cred, page_full = page_full, tweets = tweets, page_num = page_num)

if __name__ == "__main__":
    app.run(debug=True)

