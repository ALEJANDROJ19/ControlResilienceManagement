#!/usr/bin/env python3

"""
    RESOURCE MANAGEMENT - POLICIES MODULE
    CIMI API calls
"""

__status__ = 'Production'
__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'

from common.common import CPARAMS
from common.logs import LOG

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)     # https://stackoverflow.com/a/28002687


class CIMIcalls:

    CIMI_URL = CPARAMS.CIMI_URL
    CIMI_HEADERS = CPARAMS.CIMI_HEADER

    CIMI_API_ENTRY = '/cloud-entry-point'
    CIMI_AGENT_RESOURCE = '/agent'

    @staticmethod
    def checkCIMIstarted():
        """
        Check if CIMI is up.
        :return: True if CIMI is started, False otherwise.
        """
        URL = CIMIcalls.CIMI_URL + CIMIcalls.CIMI_API_ENTRY
        try:
            r = requests.get(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False)
            LOG.debug('CIMI [{}] status_code {}, content {}'.format(URL, r.status_code,r.text))
            return True
        except Exception as ex:
            LOG.debug('CIMI [{}] failed. Exception: {}'.format(URL, ex))
            return False


    @staticmethod
    def getAgentResource():
        """
        Get Agent resource in CIMI
        :return: Dicc of the Agent Resource if found or empty dicc otherwise
        """
        URL = CIMIcalls.CIMI_URL + CIMIcalls.CIMI_AGENT_RESOURCE
        try:
            r = requests.get(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False)
            rjson = r.json()
            LOG.debug('CIMI agent [{}] status_code {} count {}'.format(URL, r.status_code, rjson.get('count')))
            if len(rjson.get('agents')) > 0:
                LOG.debug('Agent resource found!')
                return rjson.get('agents')[0], rjson.get('agents')[0].get('id')
            else:
                LOG.debug('Agent resource not found!')
                return {}, ''
        except:
            LOG.exception('CIMI agent [{}] failed'.format(URL))
            return {}, ''

    @staticmethod
    def createAgentResource(agentResource):
        """
        Create a new Agent Resource in CIMI
        :param agentResource: Agent resource dicc formated
        :return: Agent resource ID
        """
        URL = CIMIcalls.CIMI_URL + CIMIcalls.CIMI_AGENT_RESOURCE
        payload = agentResource
        try:
            r = requests.post(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False, json=payload)
            rjson = r.json()
            LOG.debug('CIMI create agent [{}] status_code {} resource-id {}'.format(URL, r.status_code, rjson.get('resource-id')))
            if r.status_code == 409:
                LOG.error('CIMI create agent already exists! resource-id {}'.format(rjson.get('resource-id')))
            return str(rjson.get('resource-id'))
        except:
            LOG.exception('CIMI agent [{}] failed'.format(URL))
            return ''


    # ### Common Methods ### #
    @staticmethod
    def get_resource(resource_id):
        """
        Get resource by ID if exists
        :param resource_id: CIMI resource id
        :return: status_code and resource if successful, None otherwise
        """
        URL = CIMIcalls.CIMI_URL + '/' + resource_id
        try:
            r = requests.get(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False)
            rjson = r.json()
            LOG.debug('CIMI GET resource [{}] status_code {}'.format(URL, r.status_code))
            return r.status_code, rjson
        except:
            LOG.exception('CIMI GET resource [{}] failed.'.format(URL))
            return None, None

    @staticmethod
    def modify_resource(resource_id, payload):
        """
        Modify resource by ID in CIMI
        :param resource_id: CIMI resource id
        :param payload: new content of the resource
        :return: status_code if successful, None otherwise
        """
        URL = CIMIcalls.CIMI_URL + '/' + resource_id
        try:
            r = requests.put(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False, json=payload)
            # rjson = r.json()
            LOG.debug('CIMI EDIT resource [{}] status_code {} content {}'.format(URL, r.status_code, r.content))
            return r.status_code
        except:
            LOG.exception('CIMI EDIT resource [{}] failed.'.format(URL))
            return None

    @staticmethod
    def delete_resource(resource_id):
        """
        Delete resource by ID in CIMI
        :param resource_id: CIMI resource ID
        :return: status_code if successful, None otherwise
        """
        URL = CIMIcalls.CIMI_URL + '/' + resource_id
        try:
            r = requests.delete(URL, headers=CIMIcalls.CIMI_HEADERS, verify=False)
            # rjson = r.json()
            LOG.debug('CIMI DELETE resource [{}] status_code {}'.format(URL, r.status_code))
            return r.status_code
        except:
            LOG.exception('CIMI DELETE resource [{}] failed.'.format(URL))
            return None


class AgentResource:

    def __init__(self, deviceID, deviceIP, auth, conn, isLeader, leaderID=None, leaderIP=None, backupIP=None):
        self.deviceID = deviceID
        self.deviceIP = deviceIP
        self.authenticated = auth
        self.connected = conn
        self.isLeader = isLeader

        self.leaderID = leaderID
        self.leaderIP = leaderIP
        self.backupIP = backupIP
        self.childrenIPs = []

    def getCIMIdicc(self):
        p = {
            'device_id' : self.deviceID,
            'device_ip' : self.deviceIP,
            'authenticated' : self.authenticated,
            'connected' : self.connected,
            'isLeader' : self.isLeader
        }

        if self.leaderID is not None:
            p.update({'leader_id' : self.leaderID})
        if self.leaderIP is not None:
            p.update({'leader_ip' : self.leaderIP})
        if self.backupIP is not None:
            p.update({'backup_ip' : self.backupIP})

        return p