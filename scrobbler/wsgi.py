from scrobbler import app, db
from scrobbler.api import blueprint as api_bp
from scrobbler.webui import blueprint as webui_bp


# Blueprints
app.config.from_pyfile('config.py')
app.register_blueprint(api_bp)
app.register_blueprint(webui_bp, url_prefix='/webui')

# Database
db.init_app(app)
