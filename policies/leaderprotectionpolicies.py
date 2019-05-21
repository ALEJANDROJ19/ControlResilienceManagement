#!/usr/bin/env python3

"""
    LEADER PROTECTION POLICIES
    Common methods and utilities
"""

from json import loads, dumps, JSONDecodeError
from threading import Lock
from common.logs import LOG

__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'


class LeaderProtectionPolicies:
    POLICIES = {
        'BACKUP_MINIMUM': 1,
        'BACKUP_MAXIMUM': None,
        'MAX_TTL': 3 / .1,                      # 30 ticks ~ 3 secs (Time to Live for backups)
        'MAX_RETRY_ATTEMPTS': 5,                # Retry attempts before Leader Down
        'TIME_TO_WAIT_BACKUP_SELECTION': 3,     # Time until check backups
        'TIME_KEEPALIVE': 1,                    # Time until check leader from backup
        'TIME_KEEPER': .1                       # Leader decreasing TTL on backups
    }

    BACKUP_MINIMUM = 'BACKUP_MINIMUM'
    BACKUP_MAXIMUM = 'BACKUP_MAXIMUM'
    MAX_TTL = 'MAX_TTL'
    MAX_RETRY_ATTEMPTS = 'MAX_RETRY_ATTEMPTS'

    TIME_TO_WAIT_BACKUP_SELECTION = 'TIME_TO_WAIT_BACKUP_SELECTION'
    TIME_KEEPALIVE = 'TIME_KEEPALIVE'
    TIME_KEEPER = 'TIME_KEEPER'

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


