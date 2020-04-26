from __future__ import unicode_literals

launcher_name = 'Tactical Battlefield'
default_mods_dir = 'Tactical Battlefield'
icon = 'icons/tb.ico'
original_url = 'https://github.com/overfl0/Bulletproof-Arma-Launcher/releases/latest'
executable_name = 'TB_Launcher'
forum_url = 'http://tacticalbattlefield.net/forum'
discord_url = None
domain = 'launcher.tacbf.com'
metadata_path = '/metadata.json'
torrents_path = '/torrents'
troubleshooting_url = 'https://github.com/overfl0/Bulletproof-Arma-Launcher/wiki/Troubleshooting'
bugtracker_url = 'https://github.com/overfl0/Bulletproof-Arma-Launcher/issues'
settings_directory = 'TacBF Launcher'
news_url = 'http://launcher.tacbf.com/news.md'
dominant_color = '#2FA7D4CC'
donate_url = 'https://www.patreon.com/user?u=2944710'
capitalize_status = False
sentry_reporting_url = None

try:
    # In this file you can put values that you don't want to save in the git
    # repository, like sentry.io keys
    from custom_configuration import *
except ImportError:
    pass
