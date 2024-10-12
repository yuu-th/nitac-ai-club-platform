# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import secrets
from sys import exit

from authlib.integrations.flask_client import OAuth
from decouple import config
from flask import Flask, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from flask_migrate import Migrate

from apps import create_app, db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import CreateAccountForm, LoginForm
from apps.authentication.models import Users
from apps.authentication.util import verify_pass
from apps.config import config_dict

# WARNING: Don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

# The configuration
get_config_mode = "Debug" if DEBUG else "Production"

try:
    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit("Error: Invalid <config_mode>. Expected values [Debug, Production] ")

app = create_app(app_config)
Migrate(app, db)

# Initialize OAuth
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=config("GOOGLE_CLIENT_ID"),
    client_secret=config("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@app.route("/")
def route_default():
    return redirect(url_for("login"))


# Login & Registration


@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm(request.form)
    if "login" in request.form:
        # read form data
        email = request.form["email"]
        password = request.form["password"]

        # Locate user
        user = Users.query.filter_by(email=email).first()

        # Check the password
        if user and verify_pass(password, user.password):
            login_user(user)
            return redirect(url_for("home_blueprint.index"))

        # Something (user or pass) is not ok
        return render_template(
            "accounts/login.html", msg="Wrong user or password", form=login_form
        )

    if not current_user.is_authenticated:
        return render_template("accounts/login.html", form=login_form)
    return redirect(url_for("home_blueprint.index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    create_account_form = CreateAccountForm(request.form)
    if "register" in request.form:
        username = request.form["username"]
        email = request.form["email"]

        # Check username exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template(
                "accounts/register.html",
                msg="Username already registered",
                success=False,
                form=create_account_form,
            )

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template(
                "accounts/register.html",
                msg="Email already registered",
                success=False,
                form=create_account_form,
            )

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        return render_template(
            "accounts/register.html",
            msg='User created please <a href="/login">login</a>',
            success=True,
            form=create_account_form,
        )

    else:
        return render_template("accounts/register.html", form=create_account_form)


@app.route("/logout")
def logout():
    token = oauth.google.token
    if token:
        del oauth.google.token

    logout_user()
    return redirect(url_for("login"))
    # return redirect(
    #     "https://accounts.google.com/Logout?continue=https://appengine.google.com/_ah/logout?continue="
    #     + url_for("login", _external=True)
    # )


@app.route("/google/")
def login_google():
    nonce = secrets.token_urlsafe(16)
    session["nonce"] = nonce
    redirect_uri = url_for("google_auth", _external=True)
    return oauth.google.authorize_redirect(
        redirect_uri, nonce=nonce, prompt="select_account"
    )


@app.route("/google/auth/")
def google_auth():
    token = oauth.google.authorize_access_token()
    nonce = session.pop("nonce", None)
    user_info = oauth.google.parse_id_token(token, nonce=nonce)
    user = Users.query.filter_by(email=user_info["email"]).first()

    if user is None:
        user = Users(username=user_info["name"], email=user_info["email"])
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for("home_blueprint.index"))


# Errors


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("home/page-403.html"), 403


@app.errorhandler(403)
def access_forbidden(error):
    return render_template("home/page-403.html"), 403


@app.errorhandler(404)
def not_found_error(error):
    return render_template("home/page-404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("home/page-500.html"), 500


if DEBUG:
    app.logger.info("DEBUG       = " + str(DEBUG))
    app.logger.info("Environment = " + get_config_mode)
    app.logger.info("DBMS        = " + app_config.SQLALCHEMY_DATABASE_URI)

if __name__ == "__main__":
    app.run()
