# -*- coding: utf-8 -*-
# Tactical Battlefield Installer/Updater/Launcher
# Copyright (C) 2016 TacBF Installer Team.
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

import functools
import hashlib
import itertools
import struct
import textwrap

''' Notes:
https://community.bistudio.com/wiki/PBO_File_Format
PackingMethod; //=0x56657273 Product Entry (resistance/elite/arma)
0x56657273 == 'Vers' in  big-endian ('sreV' in little-endian)

End header (packing method):
0x43707273 == 'Cprs' in  big-endian ('srpC' in little-endian)
'''

def read_asciiz(f):
    toeof = iter(functools.partial(f.read, 1), '')
    return ''.join(itertools.takewhile('\0'.__ne__, toeof))


def write_asciiz(f, string):
    # TODO: test me with unicode
    f.write(string)
    f.write('\0')


def read_ulong(f):
    data = f.read(4)
    [ulong] = struct.unpack(b'<L', data)
    return ulong


def write_ulong(f, ulong):
    data = struct.pack(b'<L', ulong)
    f.write(data)


class HashingFile(object):
    def __init__(self, orig_file):
        self.orig_file = orig_file
        self.checksum = hashlib.sha1()

    def write(self, data):
        self.orig_file.write(data)
        self.checksum.update(data)

    def get_hash(self):
        return self.checksum.digest()


class PBOFile(object):
    def __init__(self, pbo_header, pbo_files):
        self.pbo_header = pbo_header
        self.pbo_files = pbo_files

    @staticmethod
    def read_file(filename):
        pbo_file_entries = []
        with file(filename, 'rb') as f:
            pbo_header = PBOHeader.parse_from_file(f)

            for header_entry in pbo_header.pbo_entries:
                if header_entry.is_boundary():
                    continue

                pbo_file_entry = PBOFileEntry.parse_from_file(f, header_entry.data_size)

                pbo_file_entries.append(pbo_file_entry)

        pbo_file = PBOFile(pbo_header, pbo_file_entries)

        print pbo_header

        return pbo_file

    def __str__(self):
        out = str(self.pbo_header)

        for f in self.pbo_files:
            out += str(f) + '\n'

        return out


    def save_file(self, filename):
        with file(filename, 'wb') as f:
            hashing_file = HashingFile(f)

            self.pbo_header.save_to_file(hashing_file)

            for pbo_file_entry in self.pbo_files:
                pbo_file_entry.save_to_file(hashing_file)

            f.write('\0')
            f.write(hashing_file.get_hash())


class PBOFileEntry(object):
    def __init__(self, data, physical_size):
        self.data = data
        self.physical_size = physical_size

    @staticmethod
    def parse_from_file(f, length):
        data = f.read(length)

        pbo_file_entry = PBOFileEntry(data, length)

        return pbo_file_entry

    def __str__(self):
        out = 'PBOFileEntry:\n'
        out += '    Physical size: {}\n'.format(self.physical_size)

        return out

    def save_to_file(self, f):
        f.write(self.data)


class PBOHeader(object):
    def __init__(self, pbo_entries, header_extension):
        self.pbo_entries = pbo_entries
        self.header_extension = header_extension

    def __str__(self):
        out = 'PBO Header:\n'

        if self.header_extension:
            out += str(self.header_extension)

        for entry in self.pbo_entries:
            out += str(entry) + '\n'

        return out

    def save_to_file(self, f):
        if not self.pbo_entries:
            return

        self.pbo_entries[0].save_to_file(f)

        if self.pbo_entries[0].is_boundary() and self.header_extension:
            self.header_extension.save_to_file(f)

        for entry in self.pbo_entries[1:]:
            entry.save_to_file(f)

    @staticmethod
    def parse_from_file(f):
        header_entries = []
        header_extension = None
        first_entry = True

        while True:
            pbo_header_entry = PBOHeaderEntry.parse_from_file(f)

            header_entries.append(pbo_header_entry)

            if pbo_header_entry.is_boundary():
                if not first_entry:
                    break

                else:
                    # Read header extension
                    header_extension = PBOHeaderExtension.parse_from_file(f)

            first_entry = False

        header = PBOHeader(header_entries, header_extension)

        return header


class PBOHeaderExtension(object):
    def __init__(self, strings):
        self.strings = strings

    def __str__(self):
        out = 'PBOHeaderExtension:\n'
        for s in self.strings:
            out += '    String: {}\n'.format(s)

        return out

    def save_to_file(self, f):
        for s in self.strings:
            write_asciiz(f, s)

        write_asciiz(f, '')

    @staticmethod
    def parse_from_file(f):
        strings = []

        s = read_asciiz(f)
        while s is not '':
            strings.append(s)
            s = read_asciiz(f)

        header_extension = PBOHeaderExtension(strings)

        return header_extension


class PBOHeaderEntry(object):
    def __init__(self, filename, packing_method, original_size, reserved, timestamp, data_size):
        self.filename = filename
        self.packing_method = packing_method
        self.original_size = original_size
        self.reserved = reserved
        self.timestamp = timestamp
        self.data_size = data_size

    def is_boundary(self):
        return self.filename is ''

    def __str__(self):
        out = textwrap.dedent('''
            PBO Entry:
                filename: {}
                packing_method: {}
                original_size: {}
                reserved: {}
                timestamp: {}
                data_size: {}''').format(self.filename, hex(self.packing_method), self.original_size,
                                         self.reserved, self.timestamp, self.data_size)

        return out

    def save_to_file(self, f):
        write_asciiz(f, self.filename)
        write_ulong(f, self.packing_method)
        write_ulong(f, self.original_size)
        write_ulong(f, self.reserved)
        write_ulong(f, self.timestamp)
        write_ulong(f, self.data_size)


    @staticmethod
    def parse_from_file(f):
        filename = read_asciiz(f)
        packing_method = read_ulong(f)
        original_size = read_ulong(f)
        reserved = read_ulong(f)
        timestamp = read_ulong(f)
        data_size = read_ulong(f)

        entry = PBOHeaderEntry(filename, packing_method, original_size, reserved, timestamp, data_size)

        return entry

if __name__ == '__main__':
    f = PBOFile.read_file('cba_ai.pbo')
    print f
    f.save_file('cba_ai_rework.pbo')

    with file('cba_ai.pbo', 'rb') as pbo_orig:
        orig_hash = hashlib.sha1(pbo_orig.read()).digest()

    with file('cba_ai_rework.pbo', 'rb') as pbo_rework:
        rework_hash = hashlib.sha1(pbo_rework.read()).digest()

    print 'Files are identical: {}'.format(orig_hash == rework_hash)
