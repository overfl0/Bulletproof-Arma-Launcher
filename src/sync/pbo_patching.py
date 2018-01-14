import os
import shutil
from collections import OrderedDict

import libtorrent

import yapbol


def get_pbo_offsets(path):
    offsets = OrderedDict()
    pbo = yapbol.PBOFile.read_file(path)

    for f in pbo:
        offsets[f.filename.encode('utf8')] = f.offset

    # print(offsets)
    return offsets


def fetch_pbo_metadata_from_disk(torrent_metadata):
    """Gets metadata about all the files inside each PBO file."""
    # TODO: exception handling!
    # TODO: Check if the path is a full path!

    metadata = OrderedDict()
    root = torrent_metadata['info']['name']
    files = torrent_metadata['info']['files']

    for pbo in files:
        file_path = os.path.join(root, *pbo['path'])

        # Filter out the non-pbo files
        if file_path[-4:].lower() != '.pbo':
            continue

        print(file_path)
        if os.path.isfile(file_path):
            try:
                offsets = get_pbo_offsets(file_path)
            except Exception as ex:
                # TODO: Log the exception
                print(ex)
                continue

            metadata[unicode(pbo['path'])] = offsets

    return metadata


def getSize(fileobject):
    fileobject.seek(0,2) # move the cursor to the end of the file
    size = fileobject.tell()
    return size


def seek_and_extend(fileobject, absolute_offset):
    size = getSize(fileobject)

    if absolute_offset > size:
        fileobject.seek(0, 2)  # move the cursor to the end of the file
        fileobject.write('\0' * (absolute_offset - size))

    fileobject.seek(absolute_offset)


def fix_pbo_offsets(full_pbo_path, torrent_pbo_offsets):
    # # Sanity check
    # if not os.path.isfile(full_pbo_path):
    #     return

    tmp_pbo_path = full_pbo_path + '_tmp'
    pbo = yapbol.PBOFile.read_file(full_pbo_path)

    shutil.copy2(full_pbo_path, tmp_pbo_path)

    with open(tmp_pbo_path, 'ab+') as f:
        for subfile in torrent_pbo_offsets:
            dest_offset = torrent_pbo_offsets[subfile]

            try:
                subfile_entry = pbo[subfile]
            except KeyError:
                continue

            if subfile_entry.offset != dest_offset:
                # Do copy the data
                seek_and_extend(f, dest_offset)
                f.write(subfile_entry.data)

    os.unlink(full_pbo_path)
    os.rename(tmp_pbo_path, full_pbo_path)


def prepare_mod_pbos(mod_full_path, torrent_metadata):
    """
    Go through all the PBO files that are both on disk and in the metadata.
    Then check if all the offsets in the metadata are at the same place on disk.
    If not, attempt to fix the situation by moving subfiles inside the PBO.
    """

    disk_metadata = fetch_pbo_metadata_from_disk(torrent_metadata)
    torrent_files = torrent_metadata['info']['files']

    for torrent_pbo in torrent_files:
        full_pbo_path = os.path.join(mod_full_path, *torrent_pbo['path'])
        torrent_pbo_offsets = torrent_pbo.get(b'pbo_offsets')
        disk_pbo_offsets = disk_metadata.get(unicode(torrent_pbo['path']))

        if torrent_pbo_offsets is None or disk_pbo_offsets is None:
            continue

        for torrent_pbo_subfile in torrent_pbo_offsets:
            if(torrent_pbo_subfile in disk_pbo_offsets and
               disk_pbo_offsets[torrent_pbo_subfile] != torrent_pbo_offsets[torrent_pbo_subfile]):
                # Fix the file on disk
                print('Fixing file: {}. Subfile offset doesn\'t match: {}'.format(full_pbo_path, torrent_pbo_subfile))
                fix_pbo_offsets(full_pbo_path, torrent_pbo_offsets)
                break


def extend_torrent_metadata_with_pbo(torrent_metadata):
    """Add information about each PBO file inside the torrent."""
    metadata = fetch_pbo_metadata_from_disk(torrent_metadata)
    files = torrent_metadata['info']['files']

    for pbo in files:
        if pbo['path'] in metadata:
            pbo[b'pbo_offsets'] = metadata[unicode(pbo['path'])]


if __name__ == '__main__':
    with open('@Frontline.torrent', 'rb') as f:
        torrent_metadata = libtorrent.bdecode(f.read())
    prepare_mod_pbos('@Frontline', torrent_metadata)
