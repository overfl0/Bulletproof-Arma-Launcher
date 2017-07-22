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
import utils.system_processes

from utils.devmode import devmode
from kivy.logger import Logger
from third_party import SoftwareNotInstalled
from utils import process_launcher
from utils.registry import Registry


class FaceTrackNoIRNotInstalled(SoftwareNotInstalled):
    pass


def get_faceTrackNoIR_path():
    """Get the path to FaceTrackNoIR installation."""

    fake_path = devmode.get_facetracknoir_path()
    if fake_path:
        return fake_path

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
    process_launcher.run([faceTrackNoIR_path])


class OpentrackNotInstalled(SoftwareNotInstalled):
    pass


def get_opentrack_path():
    """Get the path to Opentrack installation."""

    fake_path = devmode.get_opentrack_path()
    if fake_path:
        return fake_path

    try:
        key = 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{63F53541-A29E-4B53-825A-9B6F876A2BD6}_is1'
        reg_val = Registry.ReadValueUserAndMachine(key, 'InstallLocation', True)

        Logger.info('Opentrack: Install location: {}'.format(reg_val))

        path = os.path.join(reg_val, 'opentrack.exe')
        if not os.path.isfile(path):
            Logger.info('Opentrack: Found install location but no expected exe file found: {}'.format(path))
            raise OpentrackNotInstalled()

        return path

    except Registry.Error:
        raise OpentrackNotInstalled()


def is_opentrack_running():
    """Check if there is a Opentrack process already running."""
    return utils.system_processes.program_running('opentrack.exe')


def run_opentrack():
    """Run Opentrack if installed and not already running."""

    try:
        opentrack_path = get_opentrack_path()

    except OpentrackNotInstalled:
        Logger.info('Opentrack: No FaceTrackNoIR installation found.')
        return

    if is_opentrack_running():
        Logger.info('Opentrack: FaceTrackNoIR found already running.')
        return

    Logger.info('Opentrack: Running file: {}'.format(opentrack_path))
    process_launcher.run([opentrack_path])


class TrackIRNotInstalled(SoftwareNotInstalled):
    pass


def get_TrackIR_path():
    """Get the path to FaceTrackNoIR installation."""

    fake_path = devmode.get_trackir_path()
    if fake_path:
        return fake_path

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
    process_launcher.run([TrackIR_path])
