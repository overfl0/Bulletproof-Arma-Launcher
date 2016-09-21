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
"""
Module implementing a simple model
"""

from __future__ import unicode_literals

from kivy.event import EventDispatcher

# str variant of the unicode string on_change
# kivys api only works with non unicode strings
ON_CHANGE = 'on_change'.encode('ascii')

class ModelInterceptorError(object):
    """
    Error class used to cancel from an interceptor
    """
    pass

class Model(EventDispatcher):
    """
    a simple model implementation to have a good separation of data storage
    logic. Do not use this class directly. You should inherit from it

    Every child class has to specify a class variable called "fields". This
    should be an array of field configurations.
    These can have the following keys:
        name - the name of the field used for the get and set methods
        defaultValue - a value which is set on the instanciation of the model
        persist - boolean flag, whether the field should be persisted or not
                  defaults to true

    Changes:
        Everytime trhe models set method is invoked and the value is not equal
        to the old one, the the on_change event is fired with the arguments
        key, old_value and new_value

    Setter/Getter-Interceptors:
        Given a field with the name "attribute_one", you are able to define
        the methods called _set_attribute_one(value) and _get_attribute_one().

        In case model.set('attribute_one', new_value) is called, _set_attribute_one
        is invoked if present and has to return the new value which then gets saved.
        To cancel the set method return a ModelInterceptorError

        The get interceptor is analog, except that you should not use
        ModelInterceptorError as return value

    i.e.:
        fields: [
            {'name': 'use_exception_popup', 'defaultValue': True},
            {'name': 'launcher_basedir'}
        ]
    """

    fields = []

    def __init__(self):
        super(Model, self).__init__()

        self.register_event_type(ON_CHANGE)
        self.data = {}

        # init data fields
        for f in self.fields:
            self.data[f['name']] = f.get('defaultValue', None)

    def get(self, key):
        """
        get a data value from the model instance
        """
        value = self.data[key]
        interceptor = None
        if hasattr(self, '_get_' + key):
            interceptor = getattr(self, '_get_' + key)
        if hasattr(interceptor, '__call__'):
            value = interceptor(value)

        return value

    def set(self, key, value):
        """
        set data

        fires the on_change event with the following args
            self - the object
            old_value
            new_value

        on_change is only getting fired if value really changed
        """
        interceptor = None
        if hasattr(self, '_set_' + key):
            interceptor = getattr(self, '_set_' + key)
        if hasattr(interceptor, '__call__'):
            value = interceptor(value)
            if isinstance(value, ModelInterceptorError):
                return self

        old_value = self.data[key]
        if old_value != value:
            self.data[key] = value
            self.dispatch(ON_CHANGE, key, old_value, value)

        return self

    def on_change(self, *args):
        pass
