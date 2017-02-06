# Bulletproof Arma Launcher
# Copyright (C) 2016 Lukasz Taczuk
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

import os
import subprocess
import utils.system_processes

from kivy.logger import Logger
from third_party import SoftwareNotInstalled
from utils import unicode_helpers
from utils.registry import Registry


class FaceTrackNoIRNotInstalled(SoftwareNotInstalled):
    pass


def get_faceTrackNoIR_path():
    """Get the path to FaceTrackNoIR installation."""

    try:
        key = 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\FaceTrackNoIR_is1'
        reg_val = Registry.ReadValueUserAndMachine(key, 'InstallLocation', True)

        Logger.info('FaceTrackNoIR: Install location: {}'.format(reg_val))

        path = os.path.join(reg_val, 'FaceTrackNoIR.exe')
        if not os.path.isfile(path):
            Logger.info('FaceTrackNoIR: Found install location but no expected exe file found: {}'.format(path))
            raise FaceTrackNoIRNotInstalled()

        return path

    except Registry.Error:
        raise FaceTrackNoIRNotInstalled()


def is_facetrackNoIR_running():
    """Check if there is a FaceTrackNoIR process already running."""
    return utils.system_processes.program_running('FaceTrackNoIR.exe')


def run_faceTrackNoIR():
    """Run faceTrackNoIR if installed and not already running."""

    try:
        faceTrackNoIR_path = get_faceTrackNoIR_path()

    except FaceTrackNoIRNotInstalled:
        Logger.info('FaceTrackNoIR: No FaceTrackNoIR installation found.')
        return

    if is_facetrackNoIR_running():
        Logger.info('FaceTrackNoIR: FaceTrackNoIR found already running.')
        return

    Logger.info('FaceTrackNoIR: Running file: {}'.format(faceTrackNoIR_path))
    subprocess.Popen(unicode_helpers.u_to_fs_list([faceTrackNoIR_path]))


class TrackIRNotInstalled(SoftwareNotInstalled):
    pass


def get_TrackIR_path():
    """Get the path to FaceTrackNoIR installation."""

    try:
        key = 'Software\\NaturalPoint\\NaturalPoint\\NPClient Location'
        reg_val = Registry.ReadValueUserAndMachine(key, 'Path', True)

        Logger.info('TrackIR: Install location: {}'.format(reg_val))

        path = os.path.join(reg_val, 'TrackIR5.exe')
        if not os.path.isfile(path):
            Logger.info('TrackIR: Found install location but no expected exe file found: {}'.format(path))
            raise TrackIRNotInstalled()

        return path

    except Registry.Error:
        raise TrackIRNotInstalled()


def is_TrackIR_running():
    """Check if there is a FaceTrackNoIR process already running."""
    return utils.system_processes.program_running('TrackIR5.exe')


def run_TrackIR():
    """Run faceTrackNoIR if installed and not already running."""

    try:
        TrackIR_path = get_TrackIR_path()

    except TrackIRNotInstalled:
        Logger.info('TrackIR: No TrackIR installation found.')
        return

    if is_TrackIR_running():
        Logger.info('TrackIR: TrackIR found already running.')
        return

    Logger.info('TrackIR: Running file: {}'.format(TrackIR_path))
    subprocess.Popen(unicode_helpers.u_to_fs_list([TrackIR_path]))
