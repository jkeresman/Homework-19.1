import os
import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from user import User
from main import app, db


@pytest.fixture
def client():
    client = app.test_client()

    cleanup()

    db.create_all()

    yield client


def cleanup():
    db.drop_all()


def test_too_short_password_when_registering(client):
    response = client.post("/register",
                           data={
                               "first-name": "John",
                               "last-name": "Doe",
                               "email": "email@email.com",
                               "username": "username",
                               "password": "1",
                               "password-check": "1",
                                },
                           )

    assert b'Your password is too short.' in response.data
    assert b'Please try again!' in response.data


def test_incorrect_re_entered_password_when_registering(client):
    response = client.post("/register",
                           data={
                               "first-name": "John",
                               "last-name": "Doe",
                               "email": "email@email.com",
                               "username": "username",
                               "password": "password",
                               "password-check": "wrong_password",
                           },
                           )

    assert b'Wrong password!' in response.data
    assert b'Please try again!' in response.data


def test_user_already_have_an_account(client):
    client.post("/register",
                data={
                    "first-name": "John",
                    "last-name": "Doe",
                    "email": "email@email.com",
                    "username": "username",
                    "password": "password",
                    "password-check": "password",
                }
                )

    response = client.post("/register",
                           data={
                               "first-name": "John",
                               "last-name": "Doe",
                               "email": "email@email.com",
                               "username": "username",
                               "password": "password",
                               "password-check": "password",
                           }
                           )

    assert b'You already have an account!' in response.data


def test_user_not_logged_in(client):
    response = client.get("/")
    assert b'Guess the secret number' in response.data


def test_user_is_logged_in(client):

    client.post("/register",
                data={
                    "first-name": "John",
                    "last-name": "Doe",
                    "email": "email@email.com",
                    "username": "username",
                    "password": "password",
                    "password-check": "password",
                },
                follow_redirects=True,
                )

    client.post("/login",
                data={
                    "username": "username",
                    "password": "password",
                    },
                follow_redirects=True
                )

    response = client.get("/")
    assert b'Number is between 1 and 30!' in response.data
    assert b'Enter your guess' in response.data


def test_wrong_username(client):

    client.post("/register",
                data={
                    "first-name": "John",
                    "last-name": "Doe",
                    "email": "email@email.com",
                    "username": "username",
                    "password": "password",
                    "password-check": "password",
                },
                follow_redirects=True,
                )

    response = client.post("/login",
                           data={
                               "username": "incorrect_username",
                               "password": "password",
                           }
                           )

    assert b'You have entered incorrect username, please try again!' in response.data


def test_wrong_password(client):
    client.post("/register",
                data={
                    "first-name": "John",
                    "last-name": "Doe",
                    "email": "email@email.com",
                    "username": "john",
                    "password": "1234567",
                    "password-check": "1234567",
                },
                follow_redirects=True,
                )

    response = client.post("/login",
                           data={
                               "username": "john",
                               "password": "wrong_password",
                           }
                           )

    assert b'Your password is incorrect, please try again!' in response.data


def test_profile_handler(client):

    test_user_is_logged_in(client=client)

    response = client.get("/profile")
    assert b'Profile' in response.data
    assert b'John Doe' in response.data


def test_delete_your_profile(client):

    test_user_is_logged_in(client)

    # GET
    response = client.get('profile/delete-profile')
    assert b'Do you really want to delete your profile' in response.data

    # POST
    response = client.post('profile/delete-profile', follow_redirects=True)
    assert b'Guess the secret number' in response.data


def test_change_password(client):

    test_user_is_logged_in(client)

    # GET
    response = client.get('profile/change-password')
    assert b'Change password' in response.data

    # POST
    response = client.post('profile/change-password',
                           data={
                               "current-password": "password",
                               "new-password": "new_password",
                               "password-check": "new_password",
                                },
                           follow_redirects=True,
                           )

    assert b'Your password was successfully changed!' in response.data
    assert b'Now you can log in with your new password.' in response.data


def test_change_password_incorrect_password(client):

    test_user_is_logged_in(client)

    response = client.post('profile/change-password',
                           data={
                               "current-password": "incorrect_password",
                               "new-password": "new_password",
                               "password-check": "new_password",
                                },
                           follow_redirects=True,
                           )

    assert b'You have entered wrong password.' in response.data
    assert b'Please try again!' in response.data


def test_change_password_incorrect_re_entered_password(client):

    test_user_is_logged_in(client)

    response = client.post('profile/change-password',
                           data={
                               "current-password": "password",
                               "new-password": "new_password",
                               "password-check": "incorrect_new_password",
                                },
                           follow_redirects=True,
                           )

    assert b'Please try again!' in response.data
    assert b'When re-entering your new password, you have made a mistake.' in response.data


def test_change_password_too_short_new_password(client):

    test_user_is_logged_in(client)

    response = client.post('profile/change-password',
                           data={
                               "current-password": "password",
                               "new-password": "1",
                               "password-check": "1",
                                },
                           follow_redirects=True,
                           )

    assert b'Your new password is too short.' in response.data
    assert b'Please try again!' in response.data


def test_logout(client):

    test_user_is_logged_in(client)

    response = client.post("/profile/logout", follow_redirects=True)

    assert b'Guess the secret number' in response.data


def test_guessing_logic(client):

    test_user_is_logged_in(client)

    user = db.query(User).first()

    user.secret_number = 15
    user.save()

    # correct guess
    response = client.post("/secret-number",
                           data={
                               "user-guess": "15"
                           })

    assert b'Congratulation!' in response.data
    assert b'You have guessed it!' in response.data
    assert b'Play again' in response.data

    # too small guess
    response = client.post("/secret-number",
                           data={
                               "user-guess": "1"
                           })

    assert b'Wrong guess!' in response.data
    assert b'Try something bigger!' in response.data
    assert b'Try again' in response.data

    # too big guess
    response = client.post("/secret-number",
                           data={
                               "user-guess": "30"
                           })

    assert b'Wrong guess!' in response.data
    assert b'Try something smaller!' in response.data
    assert b'Try again' in response.data

