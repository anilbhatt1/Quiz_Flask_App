from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_ckeditor import  CKEditor

#Create a flask instance
app = Flask(__name__)
#Add CKEditor
ckeditor = CKEditor(app)
#Add sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
#Secret Key
app.config['SECRET_KEY'] = 'secret'
#Initialize the DB
db = SQLAlchemy(app)
#Migrate our quiz with db
migrate = Migrate(app, db)

# Dont move 'user_route' this above. Will cause circular reference
from quiz.routes import *

