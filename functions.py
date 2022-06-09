from user import User, db


def get_user_by_session_token(session_token: str) -> User:
    user = None
    if session_token:
        user = db.query(User).filter_by(session_token=session_token).first()

    return user
