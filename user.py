from sqla_wrapper import SQLAlchemy
import os

db_url = os.getenv("DATABASE_URL", "sqlite:///localhost.sqlite").replace("postgres://", "postgresql://", 1)
db = SQLAlchemy(db_url)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, unique=False)
    last_name = db.Column(db.String, unique=False)
    password = db.Column(db.String, unique=True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=False)
    session_token = db.Column(db.String, unique=True)
    secret_number = db.Column(db.Integer, unique=False)
