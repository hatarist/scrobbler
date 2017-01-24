from scrobbler import app, bcrypt, db, lastfm, login_manager
from scrobbler.api.views import blueprint as api_bp
from scrobbler.webui.views import blueprint as webui_bp

# App config
app.config.from_pyfile('config.py')

# FIXME: Template filters (https://github.com/pallets/flask/issues/1907)
import scrobbler.webui.filters  # noqa

# Blueprints
app.register_blueprint(api_bp)
app.register_blueprint(webui_bp)


# Database
db.init_app(app)

# Authentication
bcrypt.init_app(app)
login_manager.init_app(app)

# Last.fm API
lastfm.init_app(app)
