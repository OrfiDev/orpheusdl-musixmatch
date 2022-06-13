import json
import logging
import re
from typing import Optional

from modules.musixmatch.musixmatch_api import Musixmatch, CaptchaError, UserTokenError
from utils.models import ManualEnum, ModuleInformation, ModuleController, ModuleModes, TrackInfo, LyricsInfo, \
    SearchResult, DownloadTypeEnum

module_information = ModuleInformation(
    service_name='Musixmatch',
    module_supported_modes=ModuleModes.lyrics,
    global_settings={
        'token_limit': 10,
        'enable_enhanced_lyrics': False,
        'force_lyrics_x_formatting': False
    },
    global_storage_variables=['user_tokens'],
    login_behaviour=ManualEnum.manual
)


def format_timestamp(seconds: float, decimal_places: int = 2) -> str:
    # return mm:ss.xxx (m: minutes, s: seconds, x: milliseconds) from a seconds float value
    milliseconds = int(10**decimal_places)
    return f'{int(seconds // 60):02d}:{int(seconds % 60):02d}.' \
           f'{int(seconds * milliseconds % milliseconds):0{decimal_places}d}'


def parse_rich_sync_lyrics(rich_sync_lyrics: dict, use_lyrics_x: bool = False) -> str:
    """
    Parse the rich sync data and return the lyrics as a formatted string ready to be saved
    :param rich_sync_lyrics: the rich sync lyrics dict in JSON format from the musixmatch API
    :param use_lyrics_x: whether to format the lyrics according to LyricsX format (beta) or use enhanced LRC format
    :return: the lyrics as a formatted string ready to be saved
    """
    rich_sync_lrc = []

    if use_lyrics_x:
        # iterate over every line
        for line in rich_sync_lyrics:
            # "ts" is the absolute line time start, "te" is the abs line time end and add it as the first element
            time_start = line['ts']
            rich_sync_line = f'[{format_timestamp(time_start, 3)}]'

            # add the complete line lyrics "x"
            rich_sync_line += f'{line["x"]}\n[{format_timestamp(time_start, 3)}][tt]<0,0>'

            # looks like LyricsX needs the start time of a word corresponding to the number of (word) characters
            char_count = len(line['l'][0]['c'])
            for i in range(1, len(line['l'])):
                word = line['l'][i]
                if word['c'] == ' ':  # if the word is a space
                    continue  # skip it

                # append the last word start timestamp and the number of characters
                # needs to be converted to milliseconds according to
                # https://github.com/ddddxxx/LyricsKit/blob/master/Sources/LyricsCore/LyricsLineAttachment.swift
                word_ts = round(word["o"], 3)
                # count the characters + 1 for whitespace of the current word and add it to char_count
                rich_sync_line += f'<{int(word_ts * 1000.0)},{char_count}>'
                # count the characters
                char_count += len(word["c"]) + 1

            # finally, add the last word end timestamp
            time_end = line['te']
            # use the line time end as an offset and subtract a margin of 0.005 seconds
            rich_sync_line += f'<{int(float((time_end - time_start) - 0.005) * 1000.0)},{char_count}>'
            # add the line time end offset as the last element
            rich_sync_line += f'<{int(float(time_end - time_start) * 1000.0)}>'
            # add the line to the rich sync lrc
            rich_sync_lrc.append(rich_sync_line)

    else:  # enhanced LRC format
        # add the first 00:00.00 timestamp
        rich_sync_line = f'[{format_timestamp(0.0)}]'
        # iterate over every line
        for line in rich_sync_lyrics:
            # "ts" is the absolute line time start and add it as the first element
            time_start = line['ts']

            # for every word in the given line "l"
            for word in line['l']:
                if word['c'] == ' ':  # if the word is a space
                    continue  # skip it

                # "o" is the word offset in seconds from "ts"
                word_ts = round(float(time_start) + float(word["o"]), 2)
                # "c" is the word text, and format according to
                # https://en.wikipedia.org/wiki/LRC_(file_format)#Enhanced_format
                rich_sync_line += f' <{format_timestamp(word_ts)}> {word["c"]}'

            rich_sync_lrc.append(rich_sync_line)
            rich_sync_line = f'[{format_timestamp(line["te"])}]'

    # return the formatted lyrics as a string
    return '\n'.join(rich_sync_lrc)


class ModuleInterface:
    def __init__(self, module_controller: ModuleController):
        self.musixmatch = Musixmatch(module_controller.module_error)
        self.exception = module_controller.module_error
        self.use_enhanced_lyrics = module_controller.module_settings['enable_enhanced_lyrics']
        self.force_lyrics_x_formatting = module_controller.module_settings['force_lyrics_x_formatting']
        token_limit = module_controller.module_settings['token_limit']

        user_tokens = module_controller.temporary_settings_controller.read('user_tokens', 'global')
        if not user_tokens:
            user_tokens = []

        if len(user_tokens) < token_limit:
            # try to get as many tokens as possible till an error occurs
            while True:
                try:
                    logging.debug(f'{module_information.service_name}: Trying to get a new user_token...')
                    user_tokens.append(self.musixmatch.get_user_token())
                    logging.debug(f'{module_information.service_name}: user_token successfully added')
                except CaptchaError:
                    logging.debug(f'{module_information.service_name}: user_token got a captcha error')
                    break
            module_controller.temporary_settings_controller.set('user_tokens', user_tokens, 'global')

        # save the user tokens and the current index in the list
        self.user_tokens = user_tokens
        self.user_token_index = 0
        self.musixmatch.user_token = user_tokens[self.user_token_index]

    def set_next_user_token(self):
        # set the next user token from the list
        if self.user_token_index < len(self.user_tokens) - 1:
            self.user_token_index += 1
            self.musixmatch.user_token = self.user_tokens[self.user_token_index]
        else:
            self.user_token_index = 0

        logging.debug(f'{module_information.service_name}: Switched to user_token {self.user_token_index}: '
                      f'{self.musixmatch.user_token}')

    def search(self, query_type: DownloadTypeEnum, query: str, track_info: TrackInfo = None):
        track_id, lyrics, success = None, None, False

        # retry the search if the user token is invalid
        for _ in range(len(self.user_tokens)):
            try:
                # check if track_info is given and has an ISRC tag
                if track_info and track_info.tags.isrc:
                    track = self.musixmatch.get_track_by_isrc(track_info.tags.isrc)
                    success = True
                    if track:
                        track_id = track.get('track_id')
                        if self.use_enhanced_lyrics is True and track.get('has_richsync') == 1:
                            lyrics = self.musixmatch.get_rich_sync_by_id(track.get('track_id'))
                        if not lyrics and track.get('has_subtitles') == 1:
                            lyrics = self.musixmatch.get_subtitle_by_id(track.get('commontrack_id'))
                        if not lyrics and track.get('has_lyrics') == 1:
                            lyrics = self.musixmatch.get_lyrics_by_id(track.get('track_id'))

                        # if lyrics are found, break the loop
                        if lyrics:
                            break

                # fallback to manual search
                if not track_id:
                    # search for track with artist, album and title
                    track = self.musixmatch.get_lyrics_by_metadata(
                        track_info.name, track_info.artists[0], track_info.album)
                    success = True

                    if track['matcher.track.get']['message']['header']['status_code'] == 200:
                        track_id = track['matcher.track.get']['message']['body']['track']['track_id']

                    if ((self.use_enhanced_lyrics is True and track.get('track.richsync.get')) and
                            track['track.richsync.get']['message']['header']['status_code'] == 200):
                        lyrics = track['track.richsync.get']['message']['body']['richsync']
                    elif (track['track.subtitles.get']['message']['header']['status_code'] == 200 and
                          track['track.subtitles.get']['message']['body']):
                        # track.subtitles.get can return an empty body even with a status_code of 200?!
                        lyrics = track['track.subtitles.get']['message']['body']['subtitle_list'][0]['subtitle']
                    elif track['track.lyrics.get']['message']['header']['status_code'] == 200:
                        lyrics = track['track.lyrics.get']['message']['body']['lyrics']

                    break

            except CaptchaError:
                # try the next user token in the list
                self.set_next_user_token()

        if not success:
            raise self.exception('Captcha error could not be solved, open '
                                 '"https://apic.musixmatch.com/captcha.html?callback_url=mxm://captcha" to solve the '
                                 'captcha')

        if track_id:
            return [SearchResult(result_id=track_id, extra_kwargs={'lyrics': lyrics})]
        return []

    def get_track_lyrics(self, lyrics_id: str, lyrics=None) -> Optional[LyricsInfo]:
        synced, embedded = None, None
        if lyrics:
            # rich sync lyrics are present so use them
            if lyrics.get('richsync_body'):
                rich_sync_lyrics = json.loads(lyrics.get('richsync_body'))
                synced = parse_rich_sync_lyrics(rich_sync_lyrics, self.force_lyrics_x_formatting)
                embedded = '\n'.join([line['x'] for line in rich_sync_lyrics])
            elif lyrics.get('subtitle_body'):  # use normal LRC format
                synced = lyrics['subtitle_body'].replace('] ', ']')
                embedded = re.sub(r'\[[0-9]+:[0-9]+.[0-9]+]', '', synced)
            elif lyrics.get('lyrics_body'):  # use unsynced lyrics
                embedded = lyrics['lyrics_body']

        return LyricsInfo(
            embedded=embedded,
            synced=synced
        )
