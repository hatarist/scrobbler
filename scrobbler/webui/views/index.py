from flask import redirect, render_template, url_for
from flask.ext.login import current_user

from scrobbler.webui.views import blueprint


@blueprint.route("/hello/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('webui.dashboard'))
    else:
        return render_template('index.html')
