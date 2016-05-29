from flask import abort, flash, redirect, render_template, url_for
from flask.ext.login import current_user, login_required, login_user, logout_user

from scrobbler import db
from scrobbler.webui.forms import (
    LoginForm,
    RegisterForm,
    ChangeAPIPasswordForm,
    ChangeWebUIPasswordForm,
)
from scrobbler.webui.helpers import show_form_errors
from scrobbler.webui.views import blueprint
from scrobbler.models import User


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    flash('The pool is closed. :(', 'error')
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
        flash('Happy scrobbling!', 'success')
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
    form_api_pass = ChangeAPIPasswordForm()
    form_webui_pass = ChangeWebUIPasswordForm()

    if form_api_pass.validate_on_submit() and form_api_pass.api_pass.data:
        if not current_user.validate_api_password(form_api_pass.current_password.data):
            flash("Wrong current API password.", 'error')
        else:
            current_user.api_password = form_api_pass.password.data
            db.session.commit()
            flash("API password has been changed.", 'success')
    else:
        show_form_errors(form_api_pass)

    if form_webui_pass.validate_on_submit() and form_webui_pass.webui_pass.data:
        if not current_user.validate_webui_password(form_webui_pass.current_password.data):
            flash("Wrong current WebUI password.", 'error')
        else:
            current_user.webui_password = form_webui_pass.password.data
            db.session.commit()
            flash("WebUI password has been changed.", 'success')
    else:
        show_form_errors(form_webui_pass)

    return render_template(
        'auth/settings.html',
        form_api_pass=form_api_pass,
        form_webui_pass=form_webui_pass,
    )
