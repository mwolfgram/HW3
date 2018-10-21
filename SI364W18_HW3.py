## matthew wolfgram
## SI 364 - Winter 2018
## HW 3

####################
## Import statements
####################

#my main source for help was http://wtforms.simplecodes.com/docs/1.0.1/validators.html

from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError, IntegerField
from wtforms.validators import Required, Length
from flask_sqlalchemy import SQLAlchemy

############################
# Application configurations
############################

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/mrwwolfHW3" #make a database name and then get the url, formatted as above
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

##################
### App setup ####
##################
db = SQLAlchemy(app) # For database use

#########################
##### Set up Models #####
#########################

## TODO 364: Set up the following Model classes, as described, with the respective fields (data types).

class Tweet(db.Model):                                          # -- Tweet

    __tablename__ = 'tweets'
    id = db.Column(db.Integer, primary_key = True)              ## -- id (Integer, Primary Key)
    text = db.Column(db.String(280))                            ## -- text (String, up to 280 chars)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))   ## -- user_id (Integer, ID of user posted -- ForeignKey)

    def __repr__(self):
        return "{} // ID: {}".format(self.text, self.id) #lmao


class User(db.Model):                                           # -- User

    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True)              ## -- id (Integer, Primary Key)
    username = db.Column(db.String(64), unique = True)          ## -- username (String, up to 64 chars, Unique=True)
    display_name = db.Column(db.String(124))                    ## -- display_name (String, up to 124 chars)
    tweets = db.relationship('Tweet' , backref = 'User')        ## -- Line to indicate relationship between Tweet and User tables (the 1 user: many tweets relationship)

    def __repr__(self): #this takes apart the object that is returned and formats it so it's legible
        return "{} // ID: {}".format(self.username, self.id)

########################
##### Set up Forms #####
########################

# TODO 364: Fill in the rest of the below Form class so that someone running this web app will be able to fill in information about tweets they wish existed to save in the database:
# TODO 364: Set up custom validation for this form such that:

class TweetsForm(FlaskForm):
    text = StringField("what's on your mind? (keep it under 280 characters): ", validators = [Required(), Length(max = 280)])   ## -- text: tweet text (Required, should not be more than 280 characters)
    username = StringField("enter a username under 64 characters: ", validators = [Required(), Length(max = 64)])               ## -- username: the twitter username who should post it (Required, should not be more than 64 characters)
    display_name = StringField("enter a display name: ", validators = [Required()])                                             ## -- display_name: the display name of the twitter user with that username (Required, + set up custom validation for this -- see below)
    submit = SubmitField('#send #tweet')

    def validate_username(self, field): #custom validation - the twitter username may NOT start with an "@" symbol
        username = field.data
        if username[0] == "@":
            raise ValidationError("a twitter handle can't start with @!")

    def validate_display_name(self, field): #custom validation - the display name MUST be at least 2 words
        display_name = field.data
        split_display = display_name.split(' ')
        if len(split_display) < 2:
            raise ValidationError("display name can't be less than 2 words!")

###################################
##### Routes & view functions #####
###################################

## Error handling routes - PROVIDED
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#############
## Main route
#############

@app.route('/', methods=['GET', 'POST'])
def index():

    form = TweetsForm()                 #Initialize the form
    initialize = Tweet.query.all()
    tweet_amount = len(initialize)      #Get the number of Tweets

    if form.validate_on_submit():       #If the form was posted to this route, Get the data from the form
        username = form.username.data
        tweet = form.text.data
        display_name = form.display_name.data
        user = User.query.filter_by(username = username).first() #***

        if user:    # verifies user entered doesn't already exist
            user = User.query.filter_by(username = username).first()
            flash("this user already exists - ")
        else:
            user = User(username = username, display_name = display_name) #creates new user if user is new
            db.session.add(user)
            db.session.commit()

        if Tweet.query.filter_by(text = tweet, user_id = user.id).first(): #verifies tweet entered doesn't already exist
            flash('oops, this tweet already exists')
            return redirect(url_for('see_all_tweets'))
        else:
            fresh_tweet_data = Tweet(text = tweet, user_id = user.id) #creates new tweet if entry is new
            db.session.add(fresh_tweet_data)
            db.session.commit()
            flash("the tweet has been added successfully!") #verifies tweet has been saved to db
            return redirect(url_for('index'))

    # PROVIDED: If the form did NOT validate / was not submitted
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('index.html', form = form, num_tweets = tweet_amount) #redirect to index.html

#############
## all tweets
#############

@app.route('/all_tweets')
def see_all_tweets():
    tweets_master = []
    list_of_tweets = Tweet.query.all()

    for x in list_of_tweets:
        user_piece = User.query.filter_by(id = x.user_id).first() #a tweet!
        grouped = (x.text, user_piece.username)
        tweets_master.append(grouped)
    return render_template('all_tweets.html', all_tweets = tweets_master)

@app.route('/all_users')
def see_all_users():
    everybody = User.query.all()
    #print(everybody)
    return render_template('all_users.html', users = everybody) #fill in the view function so that it can successfully render the template all_tweets.html, which is provided.

#############
## longest tweet
#############

@app.route('/longest_tweet') #movies n director
def longest_tweet_get():
    tweets = Tweet.query.all()
    tweet_dict = {}
    for tweet in tweets:
        indexed_tweet = Tweet.query.filter_by(user_id = tweet.user_id).first()
        indexed_user = User.query.filter_by(id = indexed_tweet.user_id).first() #a SQL query!!
        split_tweet =  tweet.text.split(" ")
        accum = len(split_tweet)

        tweet_dict[tweet.text] = (accum, indexed_user, indexed_user.display_name)
        sorted_tweets = sorted(tweet_dict, key = lambda x : tweet_dict[x][0], reverse = True)
        big_tweet = str(sorted_tweets[0])
        big_user = str(tweet_dict[big_tweet][1]).split(' ')[0]
        big_displayname = str(tweet_dict[big_tweet][2])
    return render_template('longest_tweet.html', text = big_tweet, user = big_user, displayname = big_displayname)
    #return str(tweet_dict)

if __name__ == '__main__':
    db.create_all() # Will create any defined models when you run the application
    app.run(use_reloader=True,debug=True) # The usual
