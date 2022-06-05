from flask import Flask, render_template, url_for, request, redirect, make_response
from user import User, db
from functions import check_if_user_exists
import constants
import random

app = Flask(__name__)
db.create_all()


@app.route("/", methods=["GET"])
def index():

    user_email = request.cookies.get("email")

    user = check_if_user_exists(user_email)

    response = make_response(render_template("index.html", user=user))
    return response


@app.route("/login", methods=["POST"])
def login():

    first_name = request.form.get("first-name")
    last_name = request.form.get("last-name")
    email = request.form.get("email")
    secret_number = random.randint(constants.RANDOM_LOW_LIMIT, constants.RANDOM_HIGH_LIMIT)

    user = User(first_name=first_name, last_name=last_name, email=email, secret_number=secret_number)
    print(user.first_name, user.last_name, user.email, user.secret_number)
    user.save()

    response = make_response(redirect(url_for("index")))
    response.set_cookie("email", user.email)

    return response


@app.route("/secret-number", methods=["POST"])
def secret_number_handler():

    guess_is_correct = False

    user_email = request.cookies.get("email")
    user = check_if_user_exists(user_email)

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
    app.run(port=5004, use_reloader=True)
