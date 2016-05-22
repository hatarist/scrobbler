from flask_wtf import Form
from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import Required, Optional, Length, EqualTo, Email


class LoginForm(Form):
    username = StringField('Username', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Remember me')


class RegisterForm(Form):
    username = StringField('Username', [Required(), Length(min=3, max=32)])
    email = StringField('Email', [Optional(), Email()])
    password = PasswordField('Password', [
        Required(),
        EqualTo('repeat_password', message='Passwords must match')
    ])
    repeat_password = PasswordField('Repeat password')
