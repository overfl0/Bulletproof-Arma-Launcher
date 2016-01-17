# Tactical Battlefield Installer/Updater/Launcher
# Copyright (C) 2015 TacBF Installer Team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from __future__ import unicode_literals

import hashlib

def hash_for_file(path, algorithm=hashlib.algorithms[0], block_size=256 * 128, human_readable=True):
    """
    Block size directly depends on the block size of your filesystem
    to avoid performances issues
    Here I have blocks of 4096 octets (Default NTFS)

    Linux Ext4 block size
    sudo tune2fs -l /dev/sda5 | grep -i 'block size'
    > Block size:               4096

    Input:
        path: a path
        algorithm: an algorithm in hashlib.algorithms
                   ATM: ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512')
        block_size: a multiple of 128 corresponding to the block size of your filesystem
        human_readable: switch between digest() or hexdigest() output, default hexdigest()
    Output:
        hash
    """
    if algorithm not in hashlib.algorithms:
        raise NameError('The algorithm "{algorithm}" you specified is '
                        'not a member of "hashlib.algorithms"'.format(algorithm=algorithm))

    hash_algo = hashlib.new(algorithm)  # According to hashlib documentation using new()
                                        # will be slower then calling using named
                                        # constructors, ex.: hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(block_size), b''):
            hash_algo.update(chunk)
    if human_readable:
        file_hash = hash_algo.hexdigest()
    else:
        file_hash = hash_algo.digest()
    return file_hash

def md5(path, human_readable=False):
    return hash_for_file(path, 'md5', human_readable=human_readable)

def sha1(path, human_readable=False):
    return hash_for_file(path, 'sha1', human_readable=human_readable)
