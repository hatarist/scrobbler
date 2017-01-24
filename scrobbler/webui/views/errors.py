from flask import render_template

from scrobbler import login_manager
from scrobbler.webui.views import blueprint


@blueprint.errorhandler(403)
@login_manager.unauthorized_handler
def forbidden(e=None):
    return render_template('errors/403.html'), 403


@blueprint.errorhandler(404)
def page_not_found(e=None):
    return render_template('errors/404.html'), 404
