import base64
import hmac
from datetime import datetime
from os import urandom
from urllib import parse
from uuid import uuid4

from utils.utils import create_requests_session


class CaptchaError(Exception):
    def __init__(self, message):
        super(CaptchaError, self).__init__(message)


class UserTokenError(Exception):
    def __init__(self, message):
        super(UserTokenError, self).__init__(message)


class Musixmatch:
    def __init__(self, exception):
        self.API_URL = 'https://apic-desktop.musixmatch.com/ws/1.1/'
        self.s = create_requests_session()
        self.exception = exception
        self.headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Musixmatch/0.19.4 Chrome/58.0.3029.110 Electron/1.7.6 Safari/537.36 '
        }
        self.user_token = None

    def sign_request(self, method, params, timestamp):
        to_hash = self.API_URL + method + '?' + parse.urlencode(params)
        # Thanks to https://github.com/aaronlpv/live-lyrics/blob/master/musixmatch.c for the desktop app hmac key
        key = ("IEJ5E8XFaH" "QvIQNfs7IC").encode()
        signature = hmac.digest(key, (to_hash + timestamp).encode(), digest='SHA1')
        return base64.urlsafe_b64encode(signature).decode()

    def get_user_token_old(self):
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

        r = self.s.get(self.API_URL + method, params=params, headers=self.headers, cookies={'AWSELB': 'unknown'})
        if r.status_code != 200:
            raise Exception(r.text)

        self.user_token = r.json()['message']['body']['user_token']
        if self.user_token == 'UpgradeOnlyUpgradeOnlyUpgradeOnlyUpgradeOnly':
            raise Exception('Musixmatch: getting token failed')
        return self.user_token

    def get_user_token(self):
        r = self.s.get(f'{self.API_URL}token.get', headers=self.headers, params={
            'user_language': 'en', 'app_id': 'web-desktop-app-v1.0'
        }, cookies={
            'AWSELB': '0', 'AWSELBCORS': '0'
        })

        r = r.json()
        if r['message']['header']['status_code'] == 401 and r['message']['header']['hint'] == 'captcha':
            raise CaptchaError('Captcha required')
        elif r['message']['header']['status_code'] != 200:
            raise self.exception(f"Error: {r['message']['header']['hint']}")

        self.user_token = r['message']['body']['user_token']
        if self.user_token == 'UpgradeOnlyUpgradeOnlyUpgradeOnlyUpgradeOnly':
            raise UserTokenError('Getting user token failed')
        return self.user_token

    def _get(self, url: str, query: dict):
        params = {
            'usertoken': self.user_token,
            'app_id': 'web-desktop-app-v1.0',
        }
        params.update(query)

        r = self.s.get(f'{self.API_URL}{url}', params=params, headers=self.headers, cookies={
            'AWSELB': '0', 'AWSELBCORS': '0'
        })
        if r.status_code not in [200, 201, 202]:
            raise self.exception(r.text)

        r = r.json()
        if r['message']['header']['status_code'] == 401 and r['message']['header']['hint'] == 'captcha':
            # throw a captcha error
            raise CaptchaError('Captcha required')
        elif r['message']['header']['status_code'] != 200:
            return None

        return r['message']['body']

    def get_search_by_track(self, track_name: str, artist_name: str, album_name: str):
        # needed for richsync?
        r = self._get('matcher.track.get', {
            'q_track': track_name,
            'q_artist': artist_name,
            'q_album': album_name,
        })
        return r['track'] if r else None

    def get_track_by_isrc(self, isrc: str):
        r = self._get('track.get', {'track_isrc': isrc})
        return r['track'] if r else None

    def get_lyrics_by_id(self, track_id: str):
        r = self._get('track.lyrics.get', {'track_id': track_id})
        return r['lyrics'] if r else None

    def get_subtitle_by_id(self, common_track_id: str):
        r = self._get('track.subtitle.get', {'commontrack_id': common_track_id})
        return r['subtitle'] if r else None

    def get_rich_sync_by_id(self, track_id: str):
        # requires track_id and not common_track_id
        r = self._get('track.richsync.get', {'track_id': track_id})
        return r['richsync'] if r else None

    def get_lyrics_by_metadata(self, track_name: str, artist_name: str, album_name: str):
        return self._get('macro.subtitles.get', {
            'q_artist': artist_name,
            'q_track': track_name,
            'q_album': album_name,
            'format': 'json',
            'namespace': 'lyrics_richsynched',
            'optional_calls': 'track.richsync'
        })['macro_calls']
