from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import Required, Optional, Length, EqualTo, Email


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Remember me', default=True)


class RegisterForm(FlaskForm):
    username = StringField('Username', [Required(), Length(min=3, max=32)])
    email = StringField('Email', [Optional(), Email()])
    password = PasswordField('Password', [
        Required(),
        EqualTo('repeat_password', message='Passwords must match')
    ])
    repeat_password = PasswordField('Repeat password')


class BaseChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current password', [Required()])
    password = PasswordField('New password', [
        Required(),
        EqualTo('repeat_password', message='Passwords must match')
    ])
    repeat_password = PasswordField('Repeat password')


class ChangeAPIPasswordForm(BaseChangePasswordForm):
    api_password_submit = SubmitField('Change password')


class ChangeWebUIPasswordForm(BaseChangePasswordForm):
    webui_password_submit = SubmitField('Change password')


class AddTokenForm(FlaskForm):
    name = StringField('Token', validators=[Required()])
    key = PasswordField('Key', validators=[Required()])
    token_submit = SubmitField('Add token')


class CorrectionForm(FlaskForm):
    CHOICES = (
        ('artist', 'Artist'),
        ('track', 'Track'),
        ('tag', 'Tag'),
    )

    type = SelectField(u'Type', choices=CHOICES, validators=[Required()])

    old = StringField('Old', validators=[Required()])
    new = StringField('New', validators=[Required()])
