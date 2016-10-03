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

class ProxyBehavior(object):
    '''Proxy class attributes to some other objects.
    Adds a Proxy(...) method that forwards the attribute it is assigned to.

    Usage:
    class PBOFileEntryView(ProxyBehavior):
        def __init__(self, header_entry):
            super(PBOFileEntryView, self).__init__()
            self.header_entry = header_entry
            self.filename = self.Proxy('header_entry', 'filename')

            self.filename = 'somefile' # self.header_entry.filename = 'somefile'
    '''


    def __init__(self, *args, **kwargs):
        super(ProxyBehavior, self).__init__(*args, **kwargs)
        object.__setattr__(self, '_proxy_objects', {})

    def _register_proxy(self, attribute, *proxies):
        self._proxy_objects[attribute] = proxies

    def __getattr__(self, name):
        try:
            pointer = self
            attributes = self._proxy_objects[name]

            for attribute in attributes:
                pointer = getattr(pointer, attribute)

            return pointer

        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, name))

    def __setattr__(self, name, value):
        # Check for self.attribute = self.Proxy('obj', 'attr')
        if isinstance(value, self.Proxy):
            return self._register_proxy(name, *value.attributes_list)

        try:
            pointer = self
            attributes = self._proxy_objects[name]

            for attribute in attributes[:-1]:
                pointer = getattr(pointer, attribute)

            return setattr(pointer, attributes[-1], value)

        except KeyError:
            return object.__setattr__(self, name, value)

    class Proxy(object):
        def __init__(self, *args):
            self.attributes_list = args
