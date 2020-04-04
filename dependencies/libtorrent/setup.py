from distutils.core import setup

# Dummy setup.py to install libtorrent for python 2.7 using pip

setup(
    name='libtorrent',
    version='1.0.9',
    packages=['libtorrent',],
	data_files=[('Lib', ['libtorrent/libtorrent.pyd']),],
)

# Install in "editable mode" for development:
# pip install -e .
