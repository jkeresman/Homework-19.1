from user import User, db


def check_if_user_exists(session_token: str) -> User:
    user = None
    if session_token:
        user = db.query(User).filter_by(session_token=session_token).first()

    return user
