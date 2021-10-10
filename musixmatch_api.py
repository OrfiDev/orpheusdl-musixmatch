import hmac, base64
from urllib import parse
from datetime import datetime
from os import urandom
from uuid import uuid4

from utils.utils import create_requests_session


class Musixmatch:
    def __init__(self, exception):
        self.API_URL = 'https://apic-desktop.musixmatch.com/ws/1.1/'
        self.s = create_requests_session()
        self.exception = exception
        self.headers = {
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 10; Pixel 3 Build/QP1A.190711.020))',
            'x-mxm-endpoint': 'default'
        }
        self.user_token = None
    
    def sign_request(self, method, params, timestamp):
        to_hash = self.API_URL + method + '?' + parse.urlencode(params)
        key = ("IEJ5E8XFaH" "QvIQNfs7IC").encode() # Thanks to https://github.com/aaronlpv/live-lyrics/blob/master/musixmatch.c for the desktop app hmac key
        signature = hmac.digest(key, (to_hash + timestamp).encode(), digest='SHA1')
        return base64.urlsafe_b64encode(signature).decode()

    def get_user_token(self):
        currenttime = datetime.now()
        timestamp = currenttime.strftime('%Y-%m-%dT%H:%M:%SZ')
        signature_timestamp = currenttime.strftime('%Y%m%d')
        method = 'token.get'
        params = {
            'format': 'json',
            'guid': str(uuid4()),
            'timestamp': timestamp,
            'build_number': '2017091202',
            'lang': 'en-GB',
            'app_id': 'web-desktop-app-v1.0'
        }
        params['signature'] = self.sign_request(method, params, signature_timestamp)
        params['signature_protocol'] = 'sha1'

        r = self.s.get(self.API_URL + method, params=params, headers=self.headers, cookies={'AWSELBCORS': '0', 'AWSELB': '0'})
        if r.status_code != 200: raise Exception(r.text)
        
        self.user_token = r.json()['message']['body']['user_token']
        if self.user_token == 'UpgradeOnlyUpgradeOnlyUpgradeOnlyUpgradeOnly': raise Exception('Musixmatch: getting token failed')
        return self.user_token

    def _get(self, url: str, query: dict):
        params = {
            'usertoken': self.user_token,
            'app_id': 'web-desktop-app-v1.0',
        }
        params.update(query)

        r = self.s.get(f'{self.API_URL}{url}', params=params, headers=self.headers, cookies={'AWSELBCORS': '0', 'AWSELB': '0'})
        if r.status_code not in [200, 201, 202]:
            raise self.exception(r.text)
        r = r.json()
        if r['message']['header']['status_code'] != 200:
            return None
        return r['message']['body']

    def get_track_by_isrc(self, isrc: str):
        r = self._get('track.get', {'track_isrc': isrc})
        return r['track'] if r else None

    def get_subtitle_by_id(self, common_track_id: str):
        r = self._get('track.subtitle.get', {'commontrack_id': common_track_id})
        return r['subtitle'] if r else None

    def get_lyrics_by_metadata(self, track_name: str, artist_name: str):
        r = self._get('macro.subtitles.get', {'q_artist': artist_name, 'q_track': track_name})
        if r:
            subtitle = r['macro_calls']['track.subtitles.get']['message']
            if subtitle['header']['status_code'] == 200 and subtitle['body']:
                return r['macro_calls']['track.subtitles.get']['message']['body']['subtitle_list'][0]['subtitle']