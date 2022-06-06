from flask import Flask, render_template, request, make_response, redirect, url_for
from user import User, db
from functions import check_if_user_exists
import constants
import random
import hashlib
import uuid

app = Flask(__name__)
db.create_all()


@app.route("/", methods=["GET"])
def index():

    session_token = request.cookies.get("session_token")

    user = check_if_user_exists(session_token=session_token)
    if user is not None:
        return render_template("game.html")

    response = make_response(render_template("index.html", user=user))
    return response


@app.route("/register", methods=["POST", "GET"])
def register():

    if request.method == "POST":

        first_name = request.form.get("first-name")
        last_name = request.form.get("last-name")
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        email = request.form.get("email")
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

    else:
        response = make_response(render_template("register.html"))

    return response


@app.route("/login", methods=["POST", "GET"])
def login():

    response = make_response(render_template("login.html"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db.query(User).filter_by(username=username).first()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        if user.password == hashed_password:
            response = make_response(render_template("game.html"))
            response.set_cookie("session_token", user.session_token, httponly=True, samesite="Strict")

    return response


@app.route("/log-out", methods=["POST"])
def log_out():

    response = make_response(redirect(url_for("index")))

    session_token = request.cookies.get("session_token")
    if session_token:
        response.set_cookie("session_token", expires=0)

    return response


@app.route("/secret-number", methods=["POST"])
def secret_number_handler():

    guess_is_correct = False

    session_token = request.cookies.get("session_token")
    user = check_if_user_exists(session_token=session_token)

    user_guess = int(request.form.get("user-guess"))

    if user.secret_number == user_guess:
        guess_is_correct = True
        new_secret_number = random.randint(constants.RANDOM_LOW_LIMIT, constants.RANDOM_HIGH_LIMIT)
        user.secret_number = new_secret_number
        user.save()

    response = make_response(render_template("guess.html",
                                             guess_is_correct=guess_is_correct,
                                             secret_number=user.secret_number,
                                             guess=user_guess
                                             ))
    return response


if __name__ == "__main__":
    app.run(use_reloader=True)
