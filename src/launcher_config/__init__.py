from __future__ import unicode_literals

################################################################################

# Note: this module imports all the variables declared in the right config file
# contained in resources/<name>/launcher_configuration.py
# The value of <name> is declared inside src/launcher_config/config_select.py

################################################################################

__all__ = [
    'launcher_name',
    'default_mods_dir',
    'icon',
    'original_url',
    'executable_name',
    'forum_url',
    'domain',
    'metadata_path',
    'torrents_path',
    'troubleshooting_url',
    'bugtracker_url',
    'settings_directory',
    'news_url',
    'dominant_color',
    'donate_url',
    'capitalize_status',
]

import textwrap

try:
    # Try importing the config dir and fail gracefully
    from config_select import config_dir

except ImportError:
    message = textwrap.dedent('''
        Could not load config_dir variable from config_select.py.
        Make sure you created that file in "src/launcher_config" directory
        and filled it with the correct value.
        You can use config_select_sample.py as an example.''')

    print message

    from kivy.logger import Logger
    Logger.error('Config: {}'.format(message))

    from utils.critical_messagebox import MessageBox
    MessageBox(message, 'Error')

    import sys
    sys.exit(1)

try:
    import site
    import os

    file_directory = os.path.dirname(os.path.realpath(__file__))
    site.addsitedir(os.path.abspath(os.path.join(file_directory, '..', '..', 'resources', config_dir)))
except AttributeError:
    pass  # there is no site.addsitedir in applications frozen with PyInstaller
    # Which we don't care because we don't need to fix the path in those

from launcher_configuration import *
