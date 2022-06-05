from sqla_wrapper import SQLAlchemy
import os

db_url = os.getenv("DATABASE_URL", "sqlite:///localhost.sqlite").replace("postgres://", "postgresql://", 1)
db = SQLAlchemy(db_url)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, unique=False)
    last_name = db.Column(db.String, unique=False)
    email = db.Column(db.String, unique=True)
    secret_number = db.Column(db.Integer, unique=False)
