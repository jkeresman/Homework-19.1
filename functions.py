import hashlib

import constants
from user import User, db


def get_user_by_session_token(session_token: str) -> User:
    user = None
    if session_token:
        user = db.query(User).filter_by(session_token=session_token).first()

    return user


def too_short_password_check(password: str) -> bool:
    return len(password) < constants.PASSWORD_MIN_LENGTH


def re_entered_password_check(password: str, re_entered_password: str) -> bool:
    return password == re_entered_password


def correct_password_check(password: str, user: User) -> bool:
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password == user.password
