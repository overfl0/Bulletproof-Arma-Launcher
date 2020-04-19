from distutils.core import setup

# Dummy setup.py to install libtorrent for python 2.7 using pip

setup(
    name='libtorrent',
    version='1.2.5',
    packages=['libtorrent', ],
    data_files=[('Lib', ['libtorrent/libtorrent.pyd']), ],
)

# Install in "editable mode" for development:
# pip install -e .
