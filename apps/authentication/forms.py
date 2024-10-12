# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField
from wtforms.fields import StringField
from wtforms.validators import DataRequired, Email

# login and registration


class LoginForm(FlaskForm):
    # username = TextField("Username", id="username_login", validators=[DataRequired()])
    # username = StringField("Username", id="username_login", validators=[DataRequired()])
    email = EmailField("Email", id="email_login", validators=[DataRequired()])
    password = PasswordField("Password", id="pwd_login", validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    # username = TextField("Username", id="username_create", validators=[DataRequired()])
    # email = TextField("Email", id="email_create", validators=[DataRequired(), Email()])
    username = StringField(
        "Username", id="username_create", validators=[DataRequired()]
    )
    email = EmailField("Email", id="email_create", validators=[DataRequired(), Email()])
    password = PasswordField("Password", id="pwd_create", validators=[DataRequired()])
