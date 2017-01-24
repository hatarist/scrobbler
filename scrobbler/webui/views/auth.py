from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from scrobbler import app, db
from scrobbler.webui.forms import (
    AddTokenForm,
    ChangeAPIPasswordForm,
    ChangeWebUIPasswordForm,
    LoginForm,
    RegisterForm,
)
from scrobbler.webui.helpers import show_form_errors
from scrobbler.webui.views import blueprint
from scrobbler.models import Token, User


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    if not app.config['SIGNUP_ENABLED']:
        flash('The pool is closed. :(', category='error')
        return redirect(url_for('webui.index'))

    form = RegisterForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            api_password=form.password.data,
            webui_password=form.password.data,
            email=form.email.data
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Happy scrobbling!', category='success')
        return redirect(url_for('webui.dashboard'))
    else:
        show_form_errors(form)

    return render_template('auth/register.html', form=form)


@blueprint.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.query(User).filter(
            User.username == form.username.data,
        ).first()

        if user is None or not user.validate_webui_password(form.password.data):
            abort(403)

        login_user(user, remember=form.remember_me.data)
        flash('Logged in successfully.')
        return redirect(url_for('webui.index'))
    else:
        show_form_errors(form)

    return render_template('auth/login.html', form=form)


@blueprint.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('webui.index'))


@blueprint.route("/settings/", methods=["GET", "POST"])
@login_required
def settings():
    form_api_password = ChangeAPIPasswordForm()
    form_webui_password = ChangeWebUIPasswordForm()
    form_add_token = AddTokenForm()

    if form_api_password.validate_on_submit() and form_api_password.api_password_submit.data:
        if not current_user.validate_api_password(form_api_password.current_password.data):
            flash("Wrong current API password.", category='error')
        else:
            current_user.api_password = form_api_password.password.data
            db.session.commit()
            flash("API password has been changed.", category='success')
    else:
        show_form_errors(form_api_password)

    if form_webui_password.validate_on_submit() and form_webui_password.webui_password_submit.data:
        if not current_user.validate_webui_password(form_webui_password.current_password.data):
            flash("Wrong current WebUI password.", category='error')
        else:
            current_user.webui_password = form_webui_password.password.data
            db.session.commit()
            flash("WebUI password has been changed.", category='success')
    else:
        show_form_errors(form_webui_password)

    if form_add_token.validate_on_submit() and form_add_token.token_submit.data:
        token = Token(
            user_id=current_user.id,
            name=form_add_token.data['name'],
            key=form_add_token.data['key']
        )
        db.session.add(token)
        db.session.commit()
        flash("Token has been added.", category='success')
    else:
        show_form_errors(form_add_token)

    tokens = db.session.query(Token).filter_by(user_id=current_user.id).all()

    return render_template(
        'auth/settings.html',
        form_api_password=form_api_password,
        form_webui_password=form_webui_password,
        form_add_token=form_add_token,
        tokens=tokens,
    )
