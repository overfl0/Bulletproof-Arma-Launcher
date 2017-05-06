# Put this file into your resources/<name>/launcher_configuration.py

from __future__ import unicode_literals

# Name that is written on the GUI window
launcher_name = 'Tactical Battlefield'

# By default, the mods will be downloaded and stored in `Arma 3/<default_mods_dir>`
default_mods_dir = 'Tactical Battlefield'

# Used in resources/*/<icon>
icon = 'icons/tb.ico'

# Link to download your launcher in case of protocol change in metadata.json
# This is a last resort move and has not been used ever in the last 2 years (02.2017)
original_url = 'https://bitbucket.org/tacbf_launcher/tacbf_launcher/downloads/TB_Launcher.exe'

# On windows, it will create the executable "executable_name.exe". Linux is not supported yet.
executable_name = 'TB_Launcher'

# Forum button url (if you set it up in installscreen.kv)
forum_url = 'http://tacticalbattlefield.net/forum'

# Discord button url (if you set it up in installscreen.kv)
discord_url = 'https://discordapp.com/channels/...'

# The domain the launcher will use to fetch metadata.json
domain = 'launcher.tacbf.com'

# Path to the metadata file. The URL will be: `<domain><metadata_path>`
metadata_path = '/metadata.json'

# Torrents will be fetched from this path. The URL will be: `<domain><torrents_path>/*.torrent`
torrents_path = '/torrents'

# Link that is shown in case of a critical error. You should keep this URL.
troubleshooting_url = 'https://github.com/overfl0/Bulletproof-Arma-Launcher/wiki/Troubleshooting'

# Same as with the troubleshooting URL
bugtracker_url = 'https://github.com/overfl0/Bulletproof-Arma-Launcher/issues'

# Url for the donate button (if you set it up in installscreen.kv)
donate_url = 'https://domain/your_donate_link'

# This is where your settings are kept.
# It usually resolves to: C:\Users\<Username>\AppData\Local\<settings_directory>
settings_directory = 'TacBF Launcher'

# News url written in Markdown. This is quite experimental and may be removed
# or changed in the future
news_url = 'https://launcher.tacbf.com/news.md'

# The color of some icons and of the bar in popups
dominant_color = '#eca92d'

# Whether the text on the status bar should ALL BE CAPITALIZED
capitalize_status = True
