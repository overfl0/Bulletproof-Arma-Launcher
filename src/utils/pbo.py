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
import sys
import textwrap

from attribute_proxy import ProxyBehavior

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

        return pbo_file

    def __str__(self):
        out = str(self.pbo_header) + '\n'

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

    def add_entry(self, filename, data, packing_method=0, original_size=-1, reserved=0, timestamp=0, data_size=-1):
        if data_size == -1:
            data_size = len(data)

        if original_size == -1:
            original_size = data_size

        header_entry = PBOHeaderEntry(filename, packing_method, original_size, reserved, timestamp, data_size)
        file_entry = PBOFileEntry(data, data_size)

        self.pbo_header.pbo_entries.append(header_entry)
        self.pbo_files.append(file_entry)


    def __iter__(self):
        for header_entry, file_entry in zip(self.pbo_header.pbo_entries, self.pbo_files):
            yield PBOFileEntryView(header_entry, file_entry)

    def __getitem__(self, key):
        if isinstance(key, int):
            return PBOFileEntryView(self.pbo_header.pbo_entries[key], self.pbo_files[key])

        elif isinstance(key, slice):
            return (PBOFileEntryView(h, f) for h, f in zip(self.pbo_header.pbo_entries[key], self.pbo_files[key]))

        else:
            raise TypeError('Invalid __getitem__ type')


class PBOFileEntryView(ProxyBehavior):
    def __init__(self, header_entry, file_entry):
        super(PBOFileEntryView, self).__init__()

        self.header_entry = header_entry
        self.file_entry = file_entry

        self.filename = self.Proxy('header_entry', 'filename')
        self.original_size = self.Proxy('header_entry', 'original_size')
        self.data = self.Proxy('file_entry', 'data')

    def __str__(self):
        out = ''
        out += 'Filename: {}\n'.format(self.filename)
        out += 'Size: {}\n'.format(self.original_size)
        out += 'First 100 bytes: {}\n'.format(repr(self.data[:100]))

        return out


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
    def __init__(self, header_extension, pbo_entries, eoh_boundary):
        self.header_extension = header_extension
        self.pbo_entries = pbo_entries
        self.eoh_boundary = eoh_boundary

    def __str__(self):
        out = ''

        if self.header_extension:
            out += str(self.header_extension)

        for entry in self.pbo_entries:
            out += str(entry) + '\n'

        out += str(self.eoh_boundary) + '\n'

        return 'PBO Header:\n' + _indent(out) + '\n'

    def save_to_file(self, f):
        if not self.pbo_entries:
            return

        if self.header_extension:
            self.header_extension.save_to_file(f)

        for entry in self.pbo_entries:
            entry.save_to_file(f)

        self.eoh_boundary.save_to_file(f)

    @staticmethod
    def parse_from_file(f):
        header_entries = []
        header_extension = None
        eoh_boundary = None
        first_entry = True

        while True:
            pbo_header_entry = PBOHeaderEntry.parse_from_file(f)

            if not pbo_header_entry.is_boundary():
                header_entries.append(pbo_header_entry)

            else:  # If boundary
                if first_entry:
                    # Read header extension
                    header_extension = PBOHeaderExtension.parse_from_file(f, pbo_header_entry)

                else:
                    eoh_boundary = pbo_header_entry
                    break

            first_entry = False

        header = PBOHeader(header_extension, header_entries, eoh_boundary)

        return header


class PBOHeaderExtension(object):
    def __init__(self, strings, pbo_header_entry):
        self.pbo_header_entry = pbo_header_entry
        self.strings = strings

    def __str__(self):
        out = 'PBOHeaderExtension:'
        out += _indent(str(self.pbo_header_entry)) + '\n'
        for s in self.strings:
            out += '    String: {}\n'.format(s)

        return out

    def save_to_file(self, f):
        self.pbo_header_entry.save_to_file(f)

        for s in self.strings:
            write_asciiz(f, s)

        write_asciiz(f, '')

    @staticmethod
    def parse_from_file(f, pbo_header_entry):
        strings = []

        s = read_asciiz(f)
        while s is not '':
            strings.append(s)
            s = read_asciiz(f)

        header_extension = PBOHeaderExtension(strings, pbo_header_entry)

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


def _indent(text, indent=4 * ' '):
    return '\n'.join(indent + line for line in text.splitlines())


def _same_hash(file_a, file_b):
    with file(file_a, 'rb') as pbo_orig:
        orig_hash = hashlib.sha1(pbo_orig.read()).digest()

    with file(file_b, 'rb') as pbo_rework:
        rework_hash = hashlib.sha1(pbo_rework.read()).digest()

    return orig_hash == rework_hash


if __name__ == '__main__':
    file_tested = 'testpbo.pbo'
    f = PBOFile.read_file(file_tested)

    # print f
    for entry in f:
        # print entry.filename
        print entry

    f.save_file(file_tested + '.repack.pbo')

    print 'Files are identical: {}'.format(_same_hash(file_tested, file_tested + '.repack.pbo'))
