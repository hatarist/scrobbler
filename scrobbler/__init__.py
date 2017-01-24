from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

from ext_lastfm import LastFM


__VERSION__ = '0.3'


app = Flask(__name__)
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
lastfm = LastFM()
