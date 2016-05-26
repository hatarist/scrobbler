from flask import render_template

from scrobbler.webui.views import blueprint


@blueprint.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@blueprint.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404
