# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime #keeps track of things added to the database

# app = Flask(__name__)
# #Add Database 
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
# #Initialize The Database
# db = SQLAlchemy(app)
# #Create Model
# class User(db.Model):
# 	id = db.Column(db.Integer,primary_key=True) #will assign id automatically
# 	username = db.Column(db.String, unique=True, nullable=False)
# 	name = db.Column(db.String(200), nullable=False) #nullable=False means that their name cant be blank
# 	email = db.Column(db.String(120), nullable=False, unique=True) # unique=true, email can only be used once.
# 	date_added = db.Column(db.DateTime, default = datetime.utcnow)

# with app.app_context():
# 	db.create_all()

# 	db.session.add(User(username="example"))
# 	db.session.commit()

# 	users = db.session.execute(db.select(User)).scalars()
