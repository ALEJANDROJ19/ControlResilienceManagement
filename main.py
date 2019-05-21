#!/usr/bin/env python3

"""
    RESOURCE MANAGEMENT - POLICIES MODULE


    Sub-Modules:
        - Agent Start [AS]
        - Leader Protection [LP]
            - Area Resilience [AR]
            - Leader Reelection [LR]

"""

from common.logs import LOG
from common.common import CPARAMS, URLS
from logging import DEBUG, INFO

from leaderprotection.arearesilience import AreaResilience
from agentstart.agentstart import AgentStart
from leaderprotection.leaderreelection import LeaderReelection

from flask import Flask, request
from flask_restplus import Api, Resource, fields
from threading import Thread
from time import sleep
import requests

__status__ = 'Production'
__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__version__ = '2.0.2'
__author__ = 'Universitat Politècnica de Catalunya'

# ### Global Variables ### #
arearesilience = AreaResilience()
agentstart = AgentStart()

# ### main.py code ### #
# Set Logger
if CPARAMS.DEBUG_FLAG:
    LOG.setLevel(DEBUG)
else:
    LOG.setLevel(INFO)

LOG.info('Policies Module. Version {} Status {}'.format(__version__,__status__))

# Print env variables
LOG.debug('Environment Variables: {}'.format(CPARAMS.get_all()))


# Prepare Server
app = Flask(__name__)
app.url_map.strict_slashes = False
api = Api(app, version=__version__, title='Policies Module API', description='Resource Manager - Agent Controller')

pl = api.namespace('api/v2/resource-management/policies', description='Policies Module Operations')
rm = api.namespace('rm', description='Resource Manager Operations')

reelection_model = api.model('Reelection_msg', {
    'deviceID': fields.String(required=True, description='The deviceID of the device that is promoted as new leader.')
})

keepalive_model = api.model('Keepalive Message', {
    'deviceID': fields.String(required=True, description='The deviceID of the device that is sending the message.')
})

keepalive_reply_model = api.model('Keepalive Reply Message', {
    'deviceID': fields.String(required=True, description='The deviceID of the device that is replying the message.'),
    'backupPriority': fields.Integer(required=True, description='Order of the backup in the area.')
})

leader_info_model = api.model('Leader Info Message', {
    'imLeader': fields.Boolean(required=True, description='If the actual role is Leader'),
    'imBackup': fields.Boolean(required=True, description='If the actual role is Backup')
})

components_info_model = api.model('Resource Manager Components Information', {
    "started": fields.Boolean(description='The agent is started'),
    "running": fields.Boolean(description='The agent is currently running'),
    "modules": fields.List(fields.String, description='List of modules that are triggered on starting'),
    "discovery": fields.Boolean(description='Discovery module is started'),
    "identification": fields.Boolean(description='Identification module is started'),
    "cau_client": fields.Boolean(description='CAUClient module is started'),
    "categorization": fields.Boolean(description='Categorization module is started'),
    "policies": fields.Boolean(description='Policies module is started'),
    "discovery_description": fields.String(description='Discovery module description / parameters received'),
    "identification_description": fields.String(description='Identification module description / parameters received'),
    "categorization_description": fields.String(description='Categorization module description / parameters received'),
    "policies_description": fields.String(description='Policies module description / parameters received'),
    "cau_client_description": fields.String(description='CAUClient module description / parameters received')
})


# API Endpoints
# #### Resource Manager #### #
@rm.route('/components')
class ResourceManagerStatus(Resource):
    """Resource Manager components status"""
    @rm.doc('get_components')
    @rm.marshal_with(components_info_model)
    @rm.response(200, 'Components Information')
    def get(self):
        """Get resource manager module start status"""
        payload = {
            'started': agentstart.isStarted,
            'running': agentstart._connected,  # TODO: Private variable exposed here (soft)
            'modules': ['discovery', 'identification', 'cau_client', 'categorization', 'policies'],
            'discovery': not agentstart.discovery_failed if agentstart.discovery_failed is not None else False,
            'identification': not agentstart.identification_failed if agentstart.identification_failed is not None else False,
            'cau_client': not agentstart.cauclient_failed if agentstart.cauclient_failed is not None else False,
            'categorization': not agentstart.categorization_failed if agentstart.categorization_failed is not None else False,
            'policies': not agentstart.policies_failed if agentstart.policies_failed is not None else False
        }
        # if fcjp.isLeader:        # I'm a leader #TODO; Decide if there is any distinction if leader
        payload.update({'discovery_description': 'detectedLeaderID: \"{}\", MACaddr: \"{}\"'.format(
            agentstart.detectedLeaderID, agentstart.MACaddr) if payload.get(
            'discovery') else 'Discovery not started or error on trigger.'})
        payload.update({'identification_description': 'IDKey: \"{}\", deviceID: \"{}\"'.format(agentstart.IDkey,
                                                                                               agentstart.deviceID) if payload.get(
            'identification') else 'Identification not started or error on trigger.'})
        payload.update(
            {'categorization_description': 'Started: {}'.format(agentstart.categorization_started) if payload.get(
                'categorization') else 'RCategorization not started or error on trigger.'})
        payload.update({'policies_description': 'LPP: {}'.format(agentstart.arearesilience_started) if payload.get(
            'policies') else 'Policies (LPP) not started or error on trigger.'})
        payload.update(
            {'cau_client_description': 'authenticated: {}, secureConnection: {}'.format(agentstart.isAuthenticated,
                                                                                        agentstart.secureConnection) if payload.get(
                'cau_client') else 'CAU_client not started or error on trigger.'})
        # else:
        #     payload.update({'discovery_description': '' if payload.get('discovery') else ''})
        #     payload.update({'identification_description': '' if payload.get('identification') else ''})
        #     payload.update({'categorization_description': '' if payload.get('categorization') else ''})
        #     payload.update({'policies_description': '' if payload.get('policies') else ''})
        return payload, 200


# #### Policies Module #### #
@pl.route(URLS.END_START_FLOW)      # Start Agent
class startAgent(Resource):
    """Start Agent"""
    @pl.doc('get_startAgent')
    @pl.response(200, 'Started')
    @pl.response(403, 'Already Started')
    def get(self):
        """Start Agent"""
        started = agentstart.start(CPARAMS.LEADER_FLAG)
        if started:
            return {'started': started}, 200
        else:
            return {'started': True}, 403


@pl.route(URLS.END_POLICIES)        # Area Resilience
class startAR(Resource):
    """Start Area Resilience"""
    @pl.doc('get_startAR')
    @pl.response(200, 'Started')
    @pl.response(403, 'Already Started')
    def get(self):
        """Start Agent Resilience"""
        started = arearesilience.start(agentstart.deviceID)
        # started = arearesilience.start(CPARAMS.DEVICEID_FLAG)
        if started:
            return {'started': started}, 200
        else:
            return {'started': True}, 403


# noinspection PyUnresolvedReferences
@pl.route('/roleChange/<string:role>')      # TODO: Parametrized Endpoint
@pl.param('role', 'The requested role to change.')
class role_change(Resource):
    """Promotion/Demotion of the agent role."""
    @pl.doc('get_change')
    @pl.response(200, 'Successful')
    @pl.response(403, 'Not Successful')
    @pl.response(404, 'Role not found')
    def get(self, role):
        global arearesilience
        """Promotion/Demotion of the agent role."""
        imLeader = arearesilience.imLeader()
        imBackup = arearesilience.imBackup()
        if role.lower() == 'leader':
            # Do you want to be a leader?
            if imLeader:
                # If a leader is promoted to leader, it becomes a super-leader?
                LOG.debug('Role change: Leader -> Leader')
                return {'imLeader': imLeader, 'imBackup': imBackup}, 403
            elif imBackup:
                # Hi, I'm backup-kun - It's my time to shine!!
                LOG.debug('Role change: Backup -> Leader')
                ret = agentstart.switch(imLeader=True)
                if ret:
                    LOG.info('Successful promotion to Leader')
                else:
                    LOG.warning('Unsuccessful promotion from Backup to Leader')
                return {'imLeader': True, 'imBackup': False}, 200
            else:
                # Nor leader, nor Backup, just a normal agent
                # For reelection, first you must be a backup!
                LOG.debug('Role change: Agent -> Leader')
                return {'imLeader': imLeader, 'imBackup': imBackup}, 403

        elif role.lower() == 'backup':
            # Always have a B plan
            if imLeader:
                # Why in the hell a Leader'll become a backup?
                LOG.debug('Role change: Leader -> Backup')
                return {'imLeader': imLeader, 'imBackup': imBackup}, 403
            elif imBackup:
                # Emm... no pls.
                LOG.debug('Role change: Backup -> Backup')
                return {'imLeader': imLeader, 'imBackup': imBackup}, 403
            else:
                # Can you watch my shoulder?
                LOG.debug('Role change: Agent -> Backup')
                leaderIP = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                LOG.debug('Leader at {} is selecting me as Backup'.format(leaderIP))
                ret = arearesilience.promotedToBackup(leaderIP=leaderIP)    # TODO: get leaderIP from CIMI
                if ret:
                    LOG.info('Successful promotion to Backup')
                    return {'imLeader': imLeader, 'imBackup': True}, 200
                else:
                    LOG.warning('Unsuccessful promotion from Agent to Backup')
                    return {'imLeader': arearesilience.imLeader(), 'imBackup': arearesilience.imBackup()}, 403

        elif role.lower() == 'agent':
            # Bigger will be the fall....
            if imLeader:
                # You are shuch an incompetent, you're FIRED!
                # Leader demotion
                LOG.debug('Role change: Leader -> Agent')
                arearesilience.stop()
                agentstart.switch(imLeader=False)
                CPARAMS.LEADER_FLAG = False
                arearesilience = AreaResilience(cimi)
                arearesilience.start(agentstart.deviceID)
                return {'imLeader': False, 'imBackup': False}, 200
            elif imBackup:
                # Maybe we are gona call you latter.... or not
                # Backup demotion
                LOG.debug('Role change: Backup -> Agent')
                arearesilience.stop()
                arearesilience = AreaResilience(cimi)
                arearesilience.start(agentstart.deviceID)
                return {'imLeader': False, 'imBackup': False}, 200
            else:
                # You're so tiny that I don't even care.
                LOG.debug('Role change: Agent -> Agent')
                return {'imLeader': False, 'imBackup': False}, 403

        else:
            # keikaku doori... Weird syntax maybe?
            return {'imLeader': imLeader, 'imBackup': imBackup}, 404


@pl.route('/reelection')
class reelection(Resource):
    """Reelection of the Leader"""
    @pl.doc('post_reelection')
    @pl.expect(reelection_model)
    # @pl.marshal_with(reelection_model, code=200)  # Only for return if we want to follow the same schema
    @pl.response(200, 'Reelection Successful')
    @pl.response(401, 'The Agent is not authorized to trigger the reelection')
    @pl.response(403, 'Reelection failed')
    @pl.response(404, 'Device not found or IP not available')
    def post(self):
        """Reelection of the Leader"""
        found = False
        deviceIP = ''
        deviceID = api.payload['deviceID']
        for device in cimi('topology', default=[]):     # TODO: use real topology
            if device.get('deviceID') == deviceID:
                found = True
                deviceIP = device.get('deviceIP')
                break

        if not found:
            LOG.error('Device {} not found in the topology'.format(deviceID))
            return {'deviceID': deviceID, 'deviceIP': deviceIP}, 404
        if not arearesilience.imLeader():
            LOG.error('Device is not a Leader, cannot perform a reelection in a non-leader device.')
            return {'deviceID': deviceID, 'deviceIP': deviceIP}, 401

        correct = LeaderReelection.reelection(arearesilience, deviceID, deviceIP)
        if correct:
            return {'deviceID': deviceID, 'deviceIP': deviceIP}, 200
        else:
            return {'deviceID': deviceID, 'deviceIP': deviceIP}, 403


@pl.route('/keepalive')
class keepalive(Resource):
    """Keepalive entrypoint"""
    @pl.doc('post_keepalive')
    @pl.expect(keepalive_model)
    @pl.marshal_with(keepalive_reply_model, code=200)
    @pl.response(200, 'Leader alive')
    @pl.response(403, 'Agent not authorized (Not recognized as backup)')
    @pl.response(405, 'Device is not a Leader')
    def post(self):
        """Keepalive entrypoint for Leader"""
        if not arearesilience.imLeader():
            # It's not like I don't want you to send me messages or anything, b-baka!
            return {'deviceID': agentstart.deviceID, 'backupPriority': arearesilience.PRIORITY_ON_FAILURE}, 405

        correct, priority = arearesilience.receive_keepalive(api.payload['deviceID'])
        LOG.debug('Device {} has sent a keepalive. Result correct: {}, Priority: {}'.format(api.payload['deviceID'],correct,priority))
        if correct:
            # Authorized
            return {'deviceID': agentstart.deviceID, 'backupPriority': priority}, 200
        else:
            # Not Authorized
            return {'deviceID': agentstart.deviceID, 'backupPriority': priority}, 403


@pl.route('/leaderinfo')
class leaderInfo(Resource):     # TODO: Provisional, remove when possible
    """Leader and Backup information"""
    @pl.doc('get_leaderinfo')
    @pl.marshal_with(leader_info_model, code=200)
    @pl.response(200, 'Leader and Backup Information')
    def get(self):
        """Leader and Backup information"""
        return {
            'imLeader': arearesilience.imLeader(),
            'imBackup': arearesilience.imBackup()
        }, 200


# And da Main Program
def cimi(key, default=None):    # TODO: Remove this (only for code redessign)
    value = default
    if key == 'leader':
        value = CPARAMS.LEADER_FLAG
    elif key == 'topology':
        value = []
        try:
            for item in CPARAMS.TOPOLOGY_FLAG:
                i = {
                    'deviceID': item[0],
                    'deviceIP': item[1]
                }
                value.append(i)
        except:
            LOG.exception('Topology Environment variable format is not correct.')
            value = []

    return value


def initialization():
    global arearesilience, agentstart
    # 0. Waitting time
    LOG.info('INIT: Wait {:.2f}s to start'.format(CPARAMS.TIME_WAIT_INIT))
    sleep(CPARAMS.TIME_WAIT_INIT)
    LOG.debug('INIT: Wake Me up Before You Go-Go ♫')

    # 1. Area Resilience Module Creation
    LOG.debug('Area Resilience submodule creation')
    arearesilience = AreaResilience(cimi)
    LOG.debug('Area Resilience created')

    # 2. Leader Reelection Module Creation (None)

    # 3. Agent Start Module Creation
    LOG.debug('Agent Start submodule creation')
    if CPARAMS.MF2C_FLAG:
        agentstart = AgentStart(addr_pol=('127.0.0.1', '46050'),
                                addr_dis=('discovery', '46040'),
                                addr_cat=('resource-categorization', '46070'),
                                addr_id=('identification', '46060'))
    else:
        agentstart = AgentStart(addr_pol=('127.0.0.1', '46050'))
    agentstart.deviceID = CPARAMS.DEVICEID_FLAG     # TODO: remove this
    if CPARAMS.LEADER_IP_FLAG is not None and len(CPARAMS.LEADER_IP_FLAG) != 0:
        agentstart.leaderIP = CPARAMS.LEADER_IP_FLAG
    LOG.debug('Agent Start created')

    return


def main():
    LOG.info('API documentation page at: http://{}:{}/'.format('localhost', 46050))
    app.run(debug=False, host='0.0.0.0', port=CPARAMS.POLICIES_PORT)


def debug():
    sleep(10)
    LOG.info('Early start of Identification procedure...')
    attempt = 0
    successful = False
    while attempt < 10 and not successful:      # TODO: Param
        try:
            r = requests.get(URLS.build_url_address(URLS.URL_IDENTIFICATION_START, portaddr=('identification', '46060')))   # TODO: Dynamic address
            LOG.debug('Identification request result: {}'.format(r.json()))
            successful = True
        except ValueError:
            LOG.debug('ValueError raised on Identification: {}'.format(r.text))
        except:
            LOG.warning('Early start of Identification not successful.')
        finally:
            if not successful:
                sleep(10)
            attempt += 1

    sleep(5)

    LOG.info('Starting Agent Flow...')
    r = requests.get(URLS.build_url_address(URLS.URL_START_FLOW, portaddr=('127.0.0.1', CPARAMS.POLICIES_PORT))) # TODO
    # r = requests.get(URLS.build_url_address(URLS.URL_POLICIES, portaddr=('127.0.0.1', CPARAMS.POLICIES_PORT))) # TODO
    LOG.debug('Agent Flow request result: {}'.format(r.json()))
    LOG.debug('Stoping thread activity.')
    return


if __name__ == '__main__':
    initialization()
    if CPARAMS.DEBUG_FLAG or CPARAMS.MF2C_FLAG:
        t = Thread(target=debug, name='debug_init', daemon=True)
        t.start()
    main()
    exit(0)
