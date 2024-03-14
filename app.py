import json
import os
import sqlite3
import base64
from io import BytesIO
from flask import Flask, render_template, redirect, url_for, jsonify, request, send_file
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from datetime import datetime
from wtforms import StringField, PasswordField, BooleanField, FileField
from wtforms.validators import InputRequired, Email, Length #if you didnt type something in the field it will alert, (there's validators for email addresses)
from flask_sqlalchemy import SQLAlchemy #database
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_change_password import ChangePassword, ChangePasswordForm, SetPasswordForm
from werkzeug.utils import secure_filename

app = Flask(__name__)  # Create application object
app.config['SECRET_KEY'] = 'This is my super secret key'
db_path = os.path.join(os.path.dirname(__file__), 'user_data.db')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
flask_change_password = ChangePassword(min_password_length=8, rules=dict(long_password_override=2))
flask_change_password.init_app(app)

with app.app_context():
    db.create_all()

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    first = db.Column(db.String(80))
    last = db.Column(db.String(80))

#Do not use this table. it is not the implementation of the post table
#The post Table was added via command line and is probably different
class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, db.ForeignKey('user.username'))
    file = db.Column(db.String)
    caption = db.Column(db.String(256))
    itemCategory = db.Column(db.String(50))
    date = db.Column(db.String)


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class PostForm(FlaskForm):
    file = FileField('image')
    caption = StringField('caption', validators=[InputRequired(), Length(min=4, max=256)])
    itemCategory = StringField('item category', validators=[InputRequired(), Length(min=4, max=15)])

class LoginForm(FlaskForm):
	username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
	password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
	remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    first = StringField('first name', validators=[InputRequired(), Length(min=2, max=80)])
    last = StringField('last name', validators=[InputRequired(), Length(min=2, max=80)])
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])

@app.route('/')
def index():
    return render_template('index_page.html')

@app.route('/home')
@login_required
def home():
    data = getPostData()
    return render_template('home_page.html', name=current_user.username, all_data = data)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile_page.html', name=current_user.username)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings_page.html', name=current_user.username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('home'))

        return '<h1>Invalid username or password</h1>'

    return render_template('login_page.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            return '<h1>Username already exists. Please choose a different username.</h1>'

        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256') # Update the method argument to 'pbkdf2:sha256'
        new_user = User(first=form.first.data, last=form.last.data, username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return '<h1>New user has been created!</h1><p>You may now <a class="btn btn-lg btn-primary btn-block" href="login" role="button">Log in</a></p>'

    return render_template('signup_page.html', form=form)

@app.route('/changed/<title>/<new_password>')
@login_required
def page_changed(title, new_password=''):
    return render_template('changed.html', title=title, new_password=new_password)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def page_change_password():
    title = 'Change Password'
    form = ChangePasswordForm(username=current_user.username, changing=True, title=title)
    if form.validate_on_submit():
        valid = flask_change_password.verify_password_change_form(form)
        if valid:
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            current_user.password = hashed_password
            db.session.commit()
            return redirect(url_for('page_changed', title='changed', new_password=form.password.data))

        return redirect(url_for('page_change_password'))
    password_template = flask_change_password.change_password_template(form, submit_text='Change')
    return render_template('change_password.html', password_template=password_template, title=title, form=form,
                           user=dict(username=current_user.username),
                           )

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    title = 'New Post'
    form = PostForm()
    if form.validate_on_submit():
        new_post = Post(username=current_user.username, file=base64.b64encode(form.file.data.read()).decode("UTF-8"), caption=form.caption.data, itemCategory=form.itemCategory.data, date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('new_post.html', form=form, name=current_user.username)

#Matthew
@app.route('/about')
@login_required
def about():
    return render_template('about.html', name=current_user.username)


@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

def getPostData():
    database = sqlite3.connect("user_data.db")
    cursor = database.cursor()

    #If you want to quickly enter stuff into the database uncomment a line below and follow same format
    #It goes Username, caption of image, date entered, alt text for image
    #if you want the items to stay in database uncomment the commit line
    #Important please comment/remove lines when you no longer want to add stuff
    #Removing duplicate posts in the table would be a hassle

    #cursor.execute("INSERT INTO Post VALUES ('Methuselah Honeysuckle','If anyone needs a bunch of notebooks I accidently got too many', '10/31/22','notebooks')")
    #cursor.execute("INSERT INTO Post VALUES ('11lb. Black Forest Ham','Got a bunch of free clothes for anyone wanting some. DM me if interested', '11/4/22','clothes')")
    #database.commit()

    cursor.execute("SELECT * FROM Post")
    post_data = cursor.fetchall()
    print("HOWDY HOWDY HOWDY")
    
    #for row in post_data:
        #print(row)

    reverse = post_data[::-1]

    return reverse

if __name__ == '__main__':
	app.run(debug=True)  # Run our application
