from user import User, db


def check_if_user_exists(user_email: str) -> User:
    user = None
    if user_email:
        user = db.query(User).filter_by(email=user_email).first()

    return user