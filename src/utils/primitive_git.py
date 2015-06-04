import os
import sys

build_sha1_file = 'build.sha1'

def get_sha1_from_file(base_dir, relative_path):
    """Try to read base_dir/relative_path. For git head, relative_path should be 'HEAD'.
    If it contains a sha1, return it.
    If it contains a ref, open base_dir/<ref> and return its contents.
    On error, return None"""
    try:
        head_file_path = os.path.join(base_dir, relative_path)
        head_file = open(head_file_path, "r")
        head_contents = head_file.readlines()

        line = head_contents[0].rstrip('\n')
        if line.startswith('ref: '):
            ref = line[5:]  # Skip the 'ref: '

            ref_file_path = os.path.join(base_dir, ref)
            ref_file = open(ref_file_path, "r")

            ref_file_contents = ref_file.readlines()
            sha1 = ref_file_contents[0].rstrip('\n')
        else:
            sha1 = line
    except (IOError, IndexError) as e:
        sha1 = None

    return sha1

def get_sha1_from_git_controlled(base_repo_dir):
    """Get the sha1 of the last commit of a repository.
    The base_repo_dir should contain a direct '.git' subdirectory"""
    return get_sha1_from_file(os.path.join(base_repo_dir, '.git'), 'HEAD')

def get_git_sha1_auto():
    """Get the sha1 of the last commit.
    This works both in normal mode and in pyinstaller-wrapped mode.
    Returns a string with the sha1 or None if the sha1 was impossible to be found.
    """
    if hasattr(sys, "_MEIPASS"):  # PyInstaller
        return get_sha1_from_file(sys._MEIPASS, build_sha1_file)

    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
    return get_sha1_from_git_controlled(base_dir)

def save_git_sha1_to_file(git_controlled_directory, dump_file):
    """Dump the sha1 to a file that can then be used when wrapped by pyinstaller"""
    sha1 = get_sha1_from_git_controlled(git_controlled_directory)
    os.unlink(dump_file)  # Make sure the file does not contain old data! Failure in unlinking should be visible!

    try:
        f = None
        f = open(dump_file, "w")
        f.write(sha1)
        f.close()
    except:
        if f:
            f.close()
