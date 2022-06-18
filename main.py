from flask import Flask, render_template, request, make_response, redirect, url_for
from functions import *
from user import User, db
from sqlalchemy_pagination import paginate
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

    if user:
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

        if user is not None or user_already_have_an_account(email=email):
            response = make_response(render_template("register.html", user_have_account=True))

        else:
            if too_short_password_check(password=password):
                response = make_response(render_template("register.html", too_short_password=True))

            elif not re_entered_password_check(password=password, re_entered_password=re_entered_password):
                response = make_response(render_template("register.html", incorrect_password=True))

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
                            best_score=None,
                            attempts=constants.STARTING_SCORE,
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

            if correct_password_check(password=password, user=user):
                response = make_response(render_template("game.html", user=user))
                response.set_cookie("session_token", user.session_token, httponly=True, samesite="Strict")

            else:
                response = make_response(render_template("login.html", incorrect_password=True))

    return response


@app.route("/profile/logout", methods=["POST", "GET"])
def logout():

    response = make_response(redirect(url_for("index")))

    session_token = request.cookies.get("session_token")
    if session_token:
        response.set_cookie("session_token", expires=0)

    return response


@app.route("/secret-number", methods=["GET", "POST"])
def secret_number_handler():

    too_long_guess = False

    user_guess = request.form.get("user-guess")

    session_token = request.cookies.get("session_token")
    user = get_user_by_session_token(session_token=session_token)

    if guess_is_too_long(user_guess=user_guess):
        too_long_guess = True
        user_guess = user_guess[:constants.MAX_LENGTH_OF_GUESS]

    try:
        int_user_guess = int(float(user_guess))
    except ValueError:
        return render_template("game.html",
                               incorrect_input=True,
                               user_guess=user_guess,
                               too_long_guess=too_long_guess,
                               user=user)

    if user.secret_number == int_user_guess:
        new_secret_number = random.randint(constants.RANDOM_LOW_LIMIT, constants.RANDOM_HIGH_LIMIT)
        user.secret_number = new_secret_number

        if user.best_score is None:
            user.best_score = user.attempts

        elif user.best_score > user.attempts:
            user.best_score = user.attempts

        user.attempts = constants.STARTING_SCORE
        user.save()
        response = make_response(render_template("guess.html",
                                                 guess_is_correct=True,
                                                 guess=int_user_guess,
                                                 user=user,
                                                 ))
    else:
        user.attempts += 1
        user.save()
        response = make_response(render_template("guess.html",
                                                 guess=int_user_guess,
                                                 user=user,
                                                 too_long_guess=too_long_guess
                                                 ))

    return response


@app.route("/profile", methods=["GET"])
def profile_handler():

    session_token = request.cookies.get("session_token")
    user = get_user_by_session_token(session_token=session_token)

    return render_template("profile.html", user=user)


@app.route("/profile/change-password", methods=["GET", "POST"])
def change_password():

    session_token = request.cookies.get("session_token")
    user = get_user_by_session_token(session_token=session_token)

    response = make_response(render_template("change_password.html", user=user))

    if request.method == "POST":
        if user:
            current_password = request.form.get("current-password")
            new_password = request.form.get("new-password")
            re_entered_password = request.form.get("password-check")

            if not correct_password_check(password=current_password, user=user):
                return render_template("change_password.html", incorrect_password=True)

            elif too_short_password_check(password=new_password):
                return render_template("change_password.html", too_short_password=True)

            elif not re_entered_password_check(password=new_password, re_entered_password=re_entered_password):
                return render_template("change_password.html", incorrect_re_entered_password=True)

            else:
                hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
                user.password = hashed_password
                user.save()

                response = make_response(render_template("index.html", password_change=True))
                response.set_cookie("session_token", expires=0)

    return response


@app.route("/leaderboard", methods=["GET"])
def leaderboard():

    session_token = request.cookies.get("session_token")
    user = get_user_by_session_token(session_token=session_token)

    all_players = db.query(User).all()

    players_that_played_game = list(filter(lambda player: player.best_score is not None, all_players))
    players_sorted_by_score = sorted(players_that_played_game, key=lambda player: player.best_score)

    return render_template("leaderboard.html", user=user, players=players_sorted_by_score[:constants.NUMBER_OF_PLAYERS])


@app.route("/profile/delete-profile", methods=["GET", "POST"])
def delete_profile():

    session_token = request.cookies.get("session_token")
    user = get_user_by_session_token(session_token=session_token)

    response = make_response(render_template("delete_profile.html", user=user))

    if request.method == "POST":
        user.delete()
        response = make_response(redirect(url_for("index")))

    return response


@app.route("/users", methods=["GET"])
def all_users():

    page = request.args.get("page")

    if not page:
        page = constants.STARTING_PAGE

    session_token = request.cookies.get("session_token")
    user = get_user_by_session_token(session_token=session_token)

    users_query = db.query(User)

    users = paginate(query=users_query, page=int(page), page_size=constants.USERS_PER_PAGE)
    return render_template("users.html", users=users, user=user)


@app.route("/users/<user_id>", methods=["GET"])
def user_details(user_id):

    session_token = request.cookies.get("session_token")
    logged_in_user = get_user_by_session_token(session_token=session_token)

    observed_user = db.query(User).get(int(user_id))

    return render_template("user_details.html", user=logged_in_user, observed_user=observed_user)


@app.route("/profile/edit-profile", methods=["GET", "POST"])
def edit_profile():

    session_token = request.cookies.get("session_token")
    user = get_user_by_session_token(session_token=session_token)

    response = make_response(render_template("profile.html", user=user, edit_profile=True))

    if request.method == "POST":
        first_name = request.form.get("profile-first-name")
        last_name = request.form.get("profile-last-name")
        email = request.form.get("profile-email")
        username = request.form.get("profile-username")

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = username

        # TODO check if username or email already exist before updating profile info
        user.save()

        response = make_response(redirect(url_for('profile_handler', user=user)))

    return response


if __name__ == "__main__":
    app.run(use_reloader=True)
