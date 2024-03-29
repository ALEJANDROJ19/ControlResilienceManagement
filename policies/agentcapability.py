#!/usr/bin/env python3

"""
    LEADER ELECTION POLICIES
    Common methods and utilities
"""

from json import loads, dumps, JSONDecodeError
from threading import Lock
from common.logs import LOG

__status__ = 'Production'
__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'


class LeaderMandatoryRequirements:
    RAM_MIN = 'RAM_MIN'

    POLICIES = {
        'RAM_MIN' : 2000.     # MBytes
    }

    __lock = Lock()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.POLICIES.keys():
                self.POLICIES[key] = value

    def get_json(self):
        with self.__lock:
            return dumps(self.POLICIES)

    def set_json(self, json):
        with self.__lock:
            try:
                ljson = loads(json)
                for key in ljson.keys():
                    if key in self.POLICIES.keys():
                        self.POLICIES[key] = ljson[key]
                return True
            except JSONDecodeError:
                LOG.exception('Error on getting new policies.')
                return False

    def get(self, key, default=None):
        with self.__lock:
            if key in self.POLICIES:
                return self.POLICIES.get(key)
            else:
                return default


class LeaderDiscretionaryRequirements:
    POLICIES = {
        'DISK_MIN' : 2000.  # MBytes
    }

    DISK_MIN = 'DISK_MIN'

    __lock = Lock()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.POLICIES.keys():
                self.POLICIES[key] = value

    def get_json(self):
        with self.__lock:
            return dumps(self.POLICIES)

    def set_json(self, json):
        with self.__lock:
            try:
                ljson = loads(json)
                for key in ljson.keys():
                    if key in self.POLICIES.keys():
                        self.POLICIES[key] = ljson[key]
                return True
            except JSONDecodeError:
                LOG.exception('Error on getting new policies.')
                return False

    def get(self, key, default=None):
        with self.__lock:
            if key in self.POLICIES:
                return self.POLICIES.get(key)
            else:
                return default
