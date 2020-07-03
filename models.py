import os

from flask import Flask
from flask import SQLAlchemy
from application import app

db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String, nullable = False)
    password = db.Column(db.String, nullable = False)
