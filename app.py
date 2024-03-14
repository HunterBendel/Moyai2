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
db_path = os.path.join(os.path.dirname(__file__), 'database.db')
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


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

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
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    return render_template('home_page.html', name=current_user.username)

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

@app.route('/about')
@login_required
def about():
    return render_template('about.html', name=current_user.username)


@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

if __name__ == '__main__':
	app.run(debug=True)  # Run our application
