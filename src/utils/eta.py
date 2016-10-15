# Bulletproof Arma Launcher
# Copyright (C) 2016 Sascha Ebert
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

import time


class Eta(object):
    no_eta = ''
    min_rate = 5  # Don't show anything if download slower than that
    values_count_max = 20

    def __init__(self):
        self.values = []

        self.calculated_timestamp = 0
        self.calculated_secs = None

    def get_average_speed(self):
        """Get the average speed of all the samples received."""
        if len(self.values) == 0:
            return 1.0  # Should not happen

        average = float(sum(self.values)) / len(self.values)
        return float(average)

    def update_speed(self, speed, total_size, downloaded_size):
        """Update the class with the latest real speed."""
        # Keep X last values for a rolling average
        self.values.append(speed)
        self.values = self.values[-self.values_count_max:]

        self.missing_size = float(total_size - downloaded_size)

    def get_real_eta_secs(self):
        """Compute the real ETA based on the average speed."""
        if self.get_average_speed() < 1.0:
            return None

        secs = self.missing_size / self.get_average_speed()
        return secs

    def get_pretended_secs(self):
        """Return an extrapolated value to prevent jitter."""
        if self.calculated_secs is None:
            return None

        pretended_secs = self.calculated_secs + self.calculated_timestamp - time.time()
        if pretended_secs < 0:
            pretended_secs = 0

        return pretended_secs

    def update_pretend_secs(self):
        """Update the pretended value if its validity has been terminated."""
        real_eta = self.get_real_eta_secs()
        pretended_eta = self.get_pretended_secs()
        min_eta = min(real_eta, pretended_eta)

        # The less time left, the often update the counter with real values
        if min_eta > 3600:
            validity_timeout = 30  # Update to real value every 30 seconds
        elif min_eta > 60:
            validity_timeout = 10
        elif min_eta > 10:
            validity_timeout = 6
        else:  # or min_eta == None:
            validity_timeout = 3

        now = time.time()
        if now > self.calculated_timestamp + validity_timeout:
            self.calculated_timestamp = now
            self.calculated_secs = real_eta

    def stringify(self, secs):
        """Format the seconds value to a human-readable form."""
        if secs is None:
            return self.no_eta

        secs = int(secs)
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)

        if hours > 0:
            ETA = '{:d}:{:02d}:{:02d}'.format(hours, mins, secs)
        else:
            ETA = '{:d}:{:02d}'.format(mins, secs)
        return ETA

    def calculate_eta(self, speed, total_size, downloaded_size):
        """Return a string showing how much time is left.

        This uses an average speed over <Eta.values_count_max> samples.
        Also, to limit jitter, the real value is computed only once in a while
        and a time offset is used between those computations. This means, the
        time value will go down normally, as you would expet it to and will
        correct itself every once in a while.
        """

        self.update_speed(speed, total_size, downloaded_size)

        # Don't show an ETA if at least one of the last measurements is below
        # the minimal value. This mitigates the problem with astronomical ETA
        # values when the torrent is just starting
        if any(value < self.min_rate * 1024 for value in self.values):
            return self.no_eta

        self.update_pretend_secs()
        secs = self.get_pretended_secs()
        return self.stringify(secs)
