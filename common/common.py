#!/usr/bin/env python3

"""
    RESOURCE MANAGEMENT - POLICIES MODULE
    Common methods and utilities
"""

__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'

from os import environ


##############################
#   Environment Variable
##############################
class common_params:
    POLICIES_PORT = 46050

    CIMI_URL = 'http://cimi:8201/api'
    CIMI_HEADER = {'slipstream-authn-info': 'super ADMIN'}
    CAU_CLIENT_ADDR = ('cau-client', 46065)
    WIFI_CONFIG_FILE = '/discovery/mF2C-VSIE.conf'

    TIME_WAIT_INIT = 2.
    TIME_WAIT_ALIVE = 5.

    def __init__(self):
        self.LEADER_FLAG = bool(environ.get('isLeader', default='False') == 'True')
        self.LEADER_IP_FLAG = environ.get('leaderIP', default=None)
        self.TOPOLOGY_FLAG = eval(environ.get('TOPOLOGY', default='[]'))
        self.DEBUG_FLAG = bool(environ.get('DEBUG', default='False') == 'True')
        self.MF2C_FLAG = bool(environ.get('MF2C', default='False') == 'True')
        self.WIFI_DEV_FLAG = str(environ.get('WIFI_DEV', default=''))
        self.DEVICEID_FLAG = str(environ.get('DEVICEID', default='agent/1234'))     # TODO: Remove this

        self.__dicc = {
            'LEADER_FLAG'       : self.LEADER_FLAG,
            'LEADER_IP_FLAG'    : self.LEADER_IP_FLAG,
            'TOPOLOGY_FLAG'     : self.TOPOLOGY_FLAG,
            'DEBUG_FLAG'        : self.DEBUG_FLAG,
            'MF2C_FLAG'         : self.MF2C_FLAG,
            'WIFI_DEV_FLAG'     : self.WIFI_DEV_FLAG,
            'CIMI_URL'          : self.CIMI_URL,
            'CIMI_HEADER'       : self.CIMI_HEADER,
            'CAU_CLIENT_ADDR'   : self.CAU_CLIENT_ADDR,
            'WIFI_CONFIG_FILE'  : self.WIFI_CONFIG_FILE,
            'TIME_WAIT_ALIVE'   : self.TIME_WAIT_ALIVE,
            'POLICIES_PORT'     : self.POLICIES_PORT,
            'DEVICEID_FLAG'     : self.DEVICEID_FLAG
        }

    def get_all(self):
        return self.__dicc


CPARAMS = common_params()


##############################
#   Modules URLs
##############################
class ModuleURLs:
    __POLICIES_BASE_URL = '/api/v2/resource-management/policies'
    URL_DISCOVERY = '/api/v1/resource-management/discovery/scan/'
    URL_DISCOVERY_MAC = '/api/v1/resource-management/discovery/mac/'  # Deprecated
    URL_DISCOVERY_SWITCH_LEADER = '/api/v1/resource-management/discovery/broadcast/'
    URL_DISCOVERY_WATCH = '/api/v1/resource-management/discovery/watch_agent_side/'
    URL_IDENTIFICATION = '/api/v1/resource-management/identification/requestID/'
    URL_IDENTIFICATION_START = '/api/v1/resource-management/identification/registerDevice/'
    URL_CATEGORIZATION_SWITCH_LEADER = '/api/v1/resource-management/categorization/leader-switch/'
    URL_CATEGORIZATION = '/api/v1/resource-management/categorization/start/'
    URL_CAU_CLIENT = '/api/v1/cau-client/triggerCAUclinet/'

    END_POLICIES = '/startAreaResilience'
    URL_POLICIES = '{}{}/'.format(__POLICIES_BASE_URL, END_POLICIES)
    END_POLICIES_ROLECHANGE = '/roleChange'
    URL_POLICIES_ROLECHANGE = '{}{}/'.format(__POLICIES_BASE_URL, END_POLICIES_ROLECHANGE)
    END_POLICIES_LEADERINFO = '/leaderinfo'
    URL_POLICIES_LEADERINFO = '{}{}/'.format(__POLICIES_BASE_URL, END_POLICIES_LEADERINFO)
    END_START_FLOW = 'startAgent'
    URL_START_FLOW = '{}{}/'.format(__POLICIES_BASE_URL, END_START_FLOW)
    END_POLICIES_KEEPALIVE = '/keepalive'
    URL_POLICIES_KEEPALIVE = '{}{}/'.format(__POLICIES_BASE_URL, END_POLICIES_KEEPALIVE)

    END_POLICIESDISTR_RECV = '/receiveNewPolicies'
    URL_POLICIESDISTR_RECV = '{}{}/'.format(__POLICIES_BASE_URL, END_POLICIESDISTR_RECV)
    END_POLICIESDISTR_TRIGGER = '/PoliciesDistributionTrigger'
    URL_POLICIESDISTR_TRIGGER = '{}{}/'.format(__POLICIES_BASE_URL, END_POLICIESDISTR_TRIGGER)

    URL_POLICIES_RMSTATUS = '/rm/components/'

    DEFAULT_ADDR = '127.0.0.1'
    DEFAULT_PORT = '60451'

    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT):
        """
        Default value for addr and port can be found at DEFAULT_ADDR and DEFAULT_PORT atributes.
        :param addr: address of the endpoint.
        :param port: port of the endpoint
        """
        self.addr = str(addr)
        self.port = port

    def build_url_address(self, api_url, addr=None, port=None, portaddr=None):
        if addr is not None:
            use_addr = str(addr)
        else:
            use_addr = self.addr
        if port is not None:
            use_port = str(port)
        else:
            use_port = self.port
        if portaddr is not None and (type(portaddr) == tuple or type(portaddr) == list) and len(portaddr) > 1:
            use_addr = str(portaddr[0])
            use_port = str(portaddr[1])

        return str('http://' + use_addr + ':' + use_port + str(api_url))


URLS = ModuleURLs()
