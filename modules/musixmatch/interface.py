import re
from typing import Optional

from modules.musixmatch.musixmatch_api import Musixmatch
from utils.models import ModuleInformation, ModuleController, ModuleModes, Tags, LyricsInfo, SearchResult


module_information = ModuleInformation(
    service_name = 'Musixmatch',
    module_supported_modes = ModuleModes.lyrics,
    temporary_settings = ['user_token']
)

class ModuleInterface:
    def __init__(self, module_controller: ModuleController):
        self.musixmatch = Musixmatch(module_controller.module_error)
        self.musixmatch.user_token = module_controller.temporary_settings_controller.read('user_token')
        if not self.musixmatch.user_token:
            self.musixmatch.user_token = self.musixmatch.get_user_token()
            module_controller.temporary_settings_controller.set('user_token', self.musixmatch.user_token)
        
        self.lyrics = {}

    def search(self, querytype, query, tags: Tags = None):
        track = None
        if tags.isrc:
            track = self.musixmatch.get_track_by_isrc(tags.isrc)
            if track:
                track_id = track['commontrack_id']
                self.lyrics[track_id] = self.musixmatch.get_subtitle_by_id(track_id)
        if not track:
            track = self.musixmatch.get_lyrics_by_metadata(tags.title, tags.album_artist)
            if track:
                track_id = track['subtitle_id']
                self.lyrics[track_id] = track
        
        if track:
            return [SearchResult(result_id=track_id)]
        return []

    def get_track_lyrics(self, lyrics_id: str) -> Optional[LyricsInfo]:
        lyrics = self.lyrics[lyrics_id]

        return LyricsInfo(
            embedded = re.sub(re.compile('\[[0-9]+:[0-9]+.[0-9]+] '), string=lyrics['subtitle_body'], repl='') if lyrics else None,
            synced = lyrics['subtitle_body'].replace('] ', ']') if lyrics else None
        )
