#!/usr/bin/env python3

"""
    LEADER REELECTION POLICIES
    Common methods and utilities
"""

from json import loads, dumps, JSONDecodeError
from threading import Lock
from common.logs import LOG

__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'


class LeaderReelectionPolicies:

    POLICIES = {
        'REELECTION_ALLOWED': True
    }

    REELECTION_ALLOWED = 'REELECTION_ALLOWED'

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