from flask import Flask, render_template, request, make_response, redirect, url_for
from user import User, db
from functions import get_user_by_session_token
import constants
import random
import hashlib
import uuid

app = Flask(__name__)
db.create_all()


@app.route("/", methods=["GET"])
def index():

    session_token = request.cookies.get("session_token")

    user = get_user_by_session_token(session_token=session_token)

    if user is not None:
        return render_template("game.html", user=user)

    return render_template("index.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    response = make_response(render_template("register.html"))

    if request.method == "POST":

        first_name = request.form.get("first-name")
        last_name = request.form.get("last-name")
        username = request.form.get("username")
        password = request.form.get("password")
        re_entered_password = request.form.get("password-check")
        email = request.form.get("email")

        user = db.query(User).filter_by(username=username).first()

        if user is not None:
            user_already_exists = True
            response = make_response(render_template("register.html", user_already_exists=user_already_exists))

        elif re_entered_password != password:
            incorrect_password = True
            response = make_response(render_template("register.html", incorrect_password=incorrect_password))

        else:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            session_token = str(uuid.uuid4())

            secret_number = random.randint(constants.RANDOM_LOW_LIMIT, constants.RANDOM_HIGH_LIMIT)

            user = User(first_name=first_name,
                        last_name=last_name,
                        email=email,
                        secret_number=secret_number,
                        password=hashed_password,
                        username=username,
                        session_token=session_token,
                        )

            user.save()

            response = make_response(render_template("login.html"))

    return response


@app.route("/login", methods=["POST", "GET"])
def login():

    response = make_response(render_template("login.html"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db.query(User).filter_by(username=username).first()

        if user is None:
            incorrect_username = True
            response = make_response(render_template("login.html", incorrect_username=incorrect_username))

        else:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            if user.password == hashed_password:
                response = make_response(render_template("game.html", user=user))
                response.set_cookie("session_token", user.session_token, httponly=True, samesite="Strict")

            elif user.password != hashed_password:
                incorrect_password = True
                response = make_response(render_template("login.html", incorrect_password=incorrect_password))

    return response


@app.route("/logout", methods=["POST", "GET"])
def logout():

    response = make_response(redirect(url_for("index")))

    session_token = request.cookies.get("session_token")
    if session_token:
        response.set_cookie("session_token", expires=0)

    return response


@app.route("/secret-number", methods=["POST"])
def secret_number_handler():

    guess_is_correct = False

    session_token = request.cookies.get("session_token")

    user = get_user_by_session_token(session_token=session_token)

    user_guess = int(request.form.get("user-guess"))

    if user.secret_number == user_guess:
        guess_is_correct = True
        new_secret_number = random.randint(constants.RANDOM_LOW_LIMIT, constants.RANDOM_HIGH_LIMIT)
        user.secret_number = new_secret_number
        user.save()

    response = make_response(render_template("guess.html",
                                             guess_is_correct=guess_is_correct,
                                             secret_number=user.secret_number,
                                             guess=user_guess,
                                             user=user,
                                             ))
    return response


@app.route("/profile")
def profile_handler():

    session_token = request.cookies.get("session_token")
    user = get_user_by_session_token(session_token=session_token)

    return render_template("profile.html", user=user)


if __name__ == "__main__":
    app.run(use_reloader=True)
