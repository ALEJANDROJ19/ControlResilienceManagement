#!/usr/bin/env python3

"""
    POLICIES DISTRIBUTION
    Common methods and utilities
"""

import threading
import requests
from json import loads, dumps, JSONDecodeError
from threading import Lock

from common.logs import LOG
from common.common import CPARAMS, URLS

from policies.agentcapability import LeaderDiscretionaryRequirements, LeaderMandatoryRequirements
from policies.leaderprotectionpolicies import LeaderProtectionPolicies
from policies.leaderselectionpolicies import AutomaticLeaderSelectionPolicies, PassiveLeaderSelectionPolicies
from policies.leaderreelectionpolicies import LeaderReelectionPolicies


__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'


class DistributionPolicies:
    SYNC_ENABLED = 'SYNC_ENABLED'
    SYNC_PERIOD = 'SYNC_PERIOD'
    POLICIES = {
        'SYNC_ENABLED' : False,
        'SYNC_PERIOD' : 60.
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


class PoliciesDistribution:
    def __init__(self):
        self.__POLICIES = {
            'LMR': LeaderMandatoryRequirements(),
            'LDR': LeaderDiscretionaryRequirements(),
            'PLSP': PassiveLeaderSelectionPolicies(),
            'ALSP': AutomaticLeaderSelectionPolicies(),
            'LPP': LeaderProtectionPolicies(),
            'LRP': LeaderReelectionPolicies(),
            'DP': DistributionPolicies(),
        }
        self.LMR = self.__POLICIES['LMR']
        self.LDR = self.__POLICIES['LDR']
        self.PLSP = self.__POLICIES['PLSP']
        self.ALSP = self.__POLICIES['ALSP']
        self.LPP = self.__POLICIES['LPP']
        self.LRP = self.__POLICIES['LRP']
        self.DP = self.__POLICIES['DP']

    def distributePolicies(self, listIPs):
        # 1. Get all the policies
        payload = {}
        for policy in self.__POLICIES.keys():
            payload.update({policy: self.__POLICIES.get(policy).get_json()})
        LOG.debug('Policy Payload : [{}]'.format(payload))

        # 2. Send to all the IPs
        for ip in listIPs:
            try:
                r = requests.post(
                    URLS.build_url_address(URLS.URL_POLICIESDISTR_RECV, portaddr=(ip, CPARAMS.POLICIES_PORT)),
                    json=payload, timeout=2)
                if r.status_code == 200:
                    # Correct
                    LOG.debug('Policies sent correctly to [{}]'.format(ip))
                else:
                    LOG.debug('Policies NOT sent correctly to [{}]'.format(ip))
            except:
                LOG.exception('Error occurred sending to [{}] the payload [{}]'.format(ip, payload))
        return

    def receivePolicies(self, payload):
        for key in payload:
            if key in self.__POLICIES.keys():
                self.__POLICIES[key].set_json(payload[key])
        LOG.info('Policies Received from Leader.')
        for policy in self.__POLICIES.keys():
            LOG.debug('[{}] - {}'.format(policy, self.__POLICIES[policy].get_json()))
        return True
