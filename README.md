# scrobbler

This is a third version of my personal AudioScrobbler server implementation.  
Written using Python 3.4+.


## Preview

![Top Artists](https://user-images.githubusercontent.com/2741725/27836970-7f7905a0-60ea-11e7-9c5d-dd4ea1cc02ae.png)

![Dashboard](https://user-images.githubusercontent.com/2741725/27836983-8e5b0a50-60ea-11e7-92f2-c97751b86800.png)


## Installation
    
    pip install -r requirements.txt
    
    cp scrobbler/config.py.example scrobbler/config.py
    
    patch scrobbler/config.py <<EOF
    @@ -5,2 +5,2 @@
    -SECRET_KEY = 'ChangeMe'
    +SECRET_KEY = '$(echo $RANDOM | openssl sha256 | cut -c10-)'
    -SIGNUP_ENABLED = False
    +SIGNUP_ENABLED = True
    EOF
    
    # maybe edit SQLALCHEMY_DATABASE_URI
    ${EDITOR-nano} scrobbler/config.py
    
    sudo -u postgres createuser -P scrobbler
    sudo -u postgres createdb -O scrobbler scrobbler 
    
    python manage.py initdb
    python manage.py runserver


## Client configuration

Make sure that the application server works on the 80 port.  
Add the corresponding entries to the `/etc/hosts` file on the client machines you wish to scrobble from.  
Example:

    {
    cat <<'EOF'
    
    # scrobbler server redirects
    127.0.0.1 ws.audioscrobbler.com
    127.0.0.1 post.audioscrobbler.com
    127.0.0.1 post2.audioscrobbler.com
    
    EOF
    } | sudo tee -a /etc/hosts

