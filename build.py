from __future__ import unicode_literals

import os
import shutil
import site
import subprocess
import sys

file_directory = os.path.dirname(os.path.realpath(__file__))
site.addsitedir(os.path.abspath(os.path.join(file_directory, 'src')))

from config import config

full_executable = config.executable_name + '.exe'

def cleanup(clean_dirs):
    print_text('Performing cleanup...')

    if clean_dirs:
        quiet_unlink('build')
        quiet_unlink('dist')

    quiet_unlink(full_executable)
    quiet_unlink(os.path.join('c:\\vagrant', full_executable))

def tests():
    print_text('Running Unit tests...')
    subprocess.check_call(['nosetests', 'tests', '-a', '!integration', '--nocapture'])
    print_text('Running Integration tests...')
    subprocess.check_call(['nosetests', 'tests', '-a', 'integration', '--nocapture'])

def build():
    print_text('Building...')
    subprocess.check_call(['python', 'c:\Python27\Scripts\pyinstaller-script.py', 'launcher.spec'])

def post_build():
    print_text('Copying files...')
    shutil.copy2(os.path.join('dist', full_executable), 'c:\\vagrant')
    shutil.copy2(os.path.join('dist', full_executable), '.')

def main():
    clean_dirs = True if len(sys.argv) > 1 and sys.argv[1] == 'new' else False

    try:
        cleanup(clean_dirs)
        tests()
        build()
        post_build()

    except Exception:
        print 'Build FAILED!'
        raise
    else:
        print 'Build succeeded!'

# Helpers ######################################################################

def print_text(text):
    print '{}\n{}\n{}'.format(80 * '#', text, 80 * '#')

def quiet_unlink(file_name):
    from utils import context

    with context.ignore_nosuchfile_exception():
        if os.path.isdir(file_name):
            shutil.rmtree(file_name)
        else:
            os.unlink(file_name)

if __name__ == '__main__':
    main()
