PONG = '''<?xml version="1.0" encoding="UTF-8"?>
<methodResponse>
<params>
<param>
<value><string>pong</string></value>
</param>
</params>
</methodResponse>'''


UPDATE_CHECK = '''<?xml version="1.0" encoding="UTF-8"?>
<Components>
    <!-- Ensure that the Last.fm App is the last App Element in the XML
         this is due to a bug in last.fm app version <= 1.5-->

    <App name="Last.fm" version="1.0" >
        <Path></Path>
        <Url>http://ws.audioscrobbler.com/</Url>
        <Size>0</Size>
    </App>
</Components>'''


RADIO_HANDSHAKE = '''session=0

stream_url=http://ws.audioscrobbler.com/last.mp3?Session=0
subscriber=0
framehack=0..
base_url=ws.audioscrobbler.com
base_path=/radio
info_message=
fingerprint_upload_url=http://ws.audioscrobbler.com/fingerprint/upload.php
permit_bootstrap=0
freetrial=2'''


AUTH_KEY_MAPPING = {
    'a': 'auth',
    'u': 'username',
    't': 'timestamp',
    'time': 'timestamp',
}

SCROBBLE_KEY_MAPPING = {
    's': 'session_id',
    'a': 'artist',
    't': 'track',
    'b': 'album',
    'l': 'length',
    'n': 'tracknumber',
    'm': 'musicbrainz',
    'i': 'timestamp',
    'o': 'source',
    'r': 'rating',
}
