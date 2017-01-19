# scrobbler

This is a third tier of my personal AudioScrobbler server implementation.  
Written using Python 3.4+.


## Installation
    
    pip install -r requirements.txt
    cp scrobbler/config.py.example scrobbler/config.py
    $EDITOR scrobbler/config.py

    python manage.py initdb
    python manage.py runserver


## Client configuration

Make sure that the application server works on the 80 port.  
Add corresponding entries to the `/etc/hosts` file:

    127.0.0.1 ws.audioscrobbler.com
    127.0.0.1 post.audioscrobbler.com
    127.0.0.1 post2.audioscrobbler.com

