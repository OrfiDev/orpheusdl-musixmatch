<!-- PROJECT INTRO -->

OrpheusDL - Musixmatch
=================

A Musixmatch module for the OrpheusDL modular archival music program

[Report Bug](https://github.com/yarrm80s/orpheusdl-musixmatch/issues)
·
[Request Feature](https://github.com/yarrm80s/orpheusdl-musixmatch/issues)


## Table of content

- [About OrpheusDL - Musixmatch](#about-orpheusdl-musixmatch)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
    - [Global](#global)
    - [Musixmatch](#musixmatch)
- [Contact](#contact)


<!-- ABOUT ORPHEUS -->
## About OrpheusDL - Musixmatch

OrpheusDL - Musixmatch is a module written in Python which allows retrieving lyrics from **Musixmatch** for the modular music archival program.


<!-- GETTING STARTED -->
## Getting Started

Follow these steps to get a local copy of Orpheus up and running:

### Prerequisites

* Already have [OrpheusDL](https://github.com/yarrm80s/orpheusdl) installed

### Installation

1. Go to your `orpheusdl/` directory and run the following command:
   ```sh
   git clone https://github.com/yarrm80s/orpheusdl-musixmatch.git modules/musixmatch
   ```
2. Execute:
   ```sh
   python orpheus.py
   ```
3. Now the `config/settings.json` file should be updated with the Musixmatch settings

<!-- USAGE EXAMPLES -->
## Usage

Either set musixmatch as your default lyrics provider in module_defaults, or call orpheus.py with the following option:

```sh
python orpheus.py -lr musixmatch https://open.qobuz.com/album/c9wsrrjh49ftb
```

<!-- CONFIGURATION -->
## Configuration

You can customize every module from Orpheus individually and also set general/global settings which are active in every
loaded module. You'll find the configuration file here: `config/settings.json`

### Global

```json5
"global": {
    "module_defaults": {
        "lyrics": "musixmatch",
        // ...
    },
    "lyrics": {
        "embed_lyrics": true,
        "save_synced_lyrics": true
    },
}
```

| Option             | Info                                                                                                                                              |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| module_defaults    | Lets you select which module to automatically get lyrics/covers/credits from. If selecting default, it will use the main module for the same task |
| embed_lyrics       | Embeds the (unsynced) as a tag inside the FLAC, M4A, MP3, ... file                                                                                |
| save_synced_lyrics | Saves the synchronized lyrics in a -lrc file alongside the music file                                                                             |


### Musixmatch

```json5
"musixmatch": {
    "token_limit": 10,
    "enable_enhanced_lyrics": false,
    "force_lyrics_x_formatting": false
},
```

| Option                    | Info                                                                                                                                                            |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| token_limit               | Defines how many user tokens should be obtained, a higher number should prevent a rate limit more often.                                                        |
| enable_enhanced_lyrics    | Saves word-by-word (enhanced) lyrics according to the [Enhanced LRC format](https://en.wikipedia.org/wiki/LRC_(file_format)#Enhanced_format)                    |
| force_lyrics_x_formatting | Forces the [LyricsX](https://github.com/ddddxxx/LyricsX) formatting instead of the Enhanced LRC formatting, only works when `enable_enhanced_lyrics` is enabled |

**Note:** `force_lyrics_x_formatting` is still experimental and may not work as expected.

<!-- Contact -->
## Contact

Yarrm80s - [@yarrm80s](https://github.com/yarrm80s)

Dniel97 - [@Dniel97](https://github.com/Dniel97)

Project Link: [OrpheusDL Musixmatch Public GitHub Repository](https://github.com/yarrm80s/orpheusdl-musixmatch)
