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

Just clone the repo inside the folder `orpheusdl/modules/`
   ```sh
   git clone https://github.com/yarrm80s/orpheusdl-musixmatch.git orpheusdl/modules/musixmatch
   ```

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

```json
"global": {
    "module_defaults": {
        "lyrics": "musixmatch",
        "covers": "default",
        "credits": "default"
    },
    "lyrics": {
        "embed_lyrics": true,
        "save_synced_lyrics": true
    },
}
```

`module_defaults`: Lets you select which module to automatically get lyrics/covers/credits from. If selecting default, it will use the main module for the same task.

`lyrics`:
* `embed_lyrics` will add the lyrics as a tag
* `save_synced_lyrics` stores synchronised lyrics in a .lrc

<!-- Contact -->
## Contact

Yarrm80s - [@yarrm80s](https://github.com/yarrm80s)

Dniel97 - [@Dniel97](https://github.com/Dniel97)

Project Link: [OrpheusDL Musixmatch Public GitHub Repository](https://github.com/yarrm80s/orpheusdl-musixmatch)
