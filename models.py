from flask_login import UserMixin
from main import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

class Simulation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nmachines = db.Column(db.Integer, nullable=False)
    nworks = db.Column(db.Integer, nullable=False)
    nops = db.Column(db.Integer, nullable=False)