# This file is auto-generated by the application.

settings_media = {
    "ENABLE_PHOTOS": {
        "value": True,
        "description": "Enable the option to search your photos. The photo's will be displayed in the viewer if the ENABLE_VIEWER option is activated."
    },
    "ENABLE_DOCUMENTS": {
        "value": True,
        "description": 'Enables the option to search your local text files.'
    },
    "ENABLE_ADB": {
        "value": False,
        "description": 'Enables the option to search your local media files and play them on an Android device, like Android-TV.'
    },
    "DEFAULT_PLAYER": {
        "value": '192.168.1.223',
        "description": 'Default Android player IP address.'
    },
    "DEFAULT_PLAYLIST": {
        "value": '/srv/mergerfs/Pool/Playlists/MyPlaylist2.m3u',
        "description": 'Path to the default playlist file.'
    },
    "PLAYED_NEWS_FILE": {
        "value": 'played_news.txt',
        "description": 'File where played news entries are stored.'
    },
    "MAX_PLAYED_NEWS_ENTRIES": {
        "value": 350,
        "description": 'Maximum number of entries to store in the played news file.'
    },
    "INTRO_URL": {
        "value": 'https://X.duckdns.org/intro.mp4',
        "description": 'URL of the intro video to play.'
    },
    "WEBSERVER": {
        "value": 'https://X.duckdns.org',
        "description": 'Base domain of the web server.'
    },
    "PLAYLIST_SAVE_PATH": {
        "value": '/srv/mergerfs/Pool/playlist.m3u',
        "description": 'Path where the playlist is saved.'
    },
    "YOUTUBE_API_KEY": {
        "value": 'YOUR_YOUTUBE_API_KEY',
        "description": 'API Token for accessing YouTube data.'
    },
    "SEARCH_FOLDERS": {
        "value": {'tv': '/srv/mergerfs/Pool/TV', 'music': '/srv/mergerfs/Pool/Music', 'movie': '/srv/mergerfs/Pool/Movies', 'podcast': '/srv/mergerfs/Pool/Podcasts', 'musicvideo': '/srv/mergerfs/Pool/Music_Videos', 'audiobooks': '/srv/mergerfs/Pool/Audiobooks', 'othervideos': '/srv/mergerfs/Pool/Other_Videos', 'jukebox': '/srv/mergerfs/Pool/Music'},
        "description": 'Directories to search for different types of media.'
    },
    "livetv_channels": {
        "value": {'1': 'http://xx', '2': 'http://x', '3': 'http://x', '4': 'http://x', '5': 'http://x', '6': 'http://x', '7': 'http://lx', '8': 'http://x', '9': 'http://x', '10': 'http://x', '11': 'http://x', '12': 'http://x', 'kunskapskanalen': 'x', 'sportkanalen': 'hxx', 'TV4 hockey': 'x', 'sport 1': 'x', 'sport 2': 'http://lx', 'sport 3': 'http://x7', 'sport 4': 'http://x'},
        "description": 'Live TV channels and their streaming URLs.'
    },
    "NEWS_API_LIST": {
        "value": [
            'http://api.sr.se/api/v2/news/episodes?format=json',
            'http://api.sr.se/api/v2/podfiles?programid=178&format=json',
            'http://api.sr.se/api/v2/podfiles?programid=5524&format=json',
            'http://api.sr.se/api/v2/podfiles?programid=5413&format=json',
        ],
        "description": 'List of API endpoints for fetching news data.'
    },
    "CORRECTIONS": {
        "value": {'2,5 men': 'two and a half men', '2,5 m': 'two and a half men', 'två och en halv män': 'two and a half men', 'test': 'House', '2 och en halv män': 'two and a half men', 'oss': 'Oz', 'lag och ordning': 'Law & Order - Special Victims Unit', 'law and order': 'Law & Order - Special Victims Unit', 'Haus': 'House', 'haus': 'House', 'bajskorv': 'House', 'hus': 'House', 'färska prinsen': 'The Fresh Prince of Bel-Air (1990)', 'Pokémon': 'Pokémon (1997)', 'löven 1': 'sport 1', 'löven 2': 'sport 2', 'löven 3': 'sport 3', 'löven 4': 'sport 4', 'löven 5': 'tv4 hockey', 'löven 6': 'sportkanalen', 'ett': '1', 'två': '2', 'tre': '3', 'fyra': '4', 'fem': '5', 'sex': '6', 'sju': '7', 'åtta': '8', 'nio': '9', 'tio': '10', 'elva': '11', 'tolv': '12'},
        "description": 'Corrections for common misinterpretations or misspellings in media requests.'
    },
}
