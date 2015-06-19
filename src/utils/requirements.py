import sys
import os.path

from pkg_resources import require, \
                          DistributionNotFound, \
                          VersionConflict, \
                          parse_version

libtorrent_least_required_version = '0.16.18'
kivy_least_required_version = '1.8.0'

def check_libraries_requirements(basedir):
    """Check if the required dependencies are met.
    Calling this function at the program start will allow the program to terminate
    gracefully in case of an unmet dependency instead of crashing while performing
    important tasks."""
    file_path = os.path.join(basedir, 'requirements.txt')

    try:
        # TODO: pkg_resources does not seem to work in a PyInstaller bundle.
        # Skip the check if we are running in a |PyInstaller| bundle. Assume everything is all right.
        if not getattr(sys, 'frozen', False):
            with file(file_path) as req_file:
                requirements = req_file.readlines()
                require(requirements)

        # Libtorrent requirements
        try:
            # Workaround for libtorrent version (not available on pip so it cannot
            # be written inside requirements.txt).
            import libtorrent

            if parse_version(libtorrent.version) < parse_version(libtorrent_least_required_version):
                raise VersionConflict('libtorrent {}'.format(libtorrent.version),
                                      'libtorrent >= {}'.format(libtorrent_least_required_version))

        except ImportError:
            raise DistributionNotFound('libtorrent')


        # Kivy requirements
        try:
            import multiprocessing
            multiprocessing.freeze_support()

            import kivy

            kivy.require(kivy_least_required_version)

        except ImportError:
            raise DistributionNotFound('kivy')

        except Exception as ex:
            # Kivy raises an Exception with a not-so-nicely formatted message
            # Just print it and exit
            print ex.message
            sys.exit(1)


    except VersionConflict as ex:
        print 'Wrong library version. Installed: {}. Required: {}'.format(ex.args[0], ex.args[1])
        sys.exit(1)

    except DistributionNotFound as ex:
        print 'Missing python library. Required: {}'.format(ex.args[0])
        sys.exit(1)
