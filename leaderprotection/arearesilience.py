#!/usr/bin/env python3

"""
    RESOURCE MANAGEMENT - POLICIES MODULE
    Area Resilience - Keep always a Leader in the area!

"""

import threading
import requests
import socket
from time import sleep
from random import randrange

from common.logs import LOG
from common.common import CPARAMS, URLS

from requests.exceptions import ConnectTimeout as timeout

__status__ = 'Production'
__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'


class BackupEntry:
    MAX_TTL = 3 / .1 # 30 ticks ~ 3 secs

    def __init__(self, deviceID, deviceIP, priority):
        self.deviceID = deviceID
        self.deviceIP = deviceIP
        self.priority = priority
        self.TTL = self.MAX_TTL


class AreaResilience:
    # SELECTION_PORT = 46051  # 29512 # Deprecated - Keepalive is now REST!
    # LEADER_PORT = 46052  # 29513

    MAX_RETRY_ATTEMPTS = 5

    TIME_TO_WAIT_BACKUP_SELECTION = 3
    TIME_KEEPALIVE = 1
    TIME_KEEPER = .1
    MINIMUM_BACKUPS = 1

    PRIORITY_ON_DEMOTION = -2
    PRIORITY_ON_REELECTION = 0
    PRIORITY_ON_FAILURE = -3

    TAG = '\033[34m' + '[AR]: ' + '\033[0m'

    def __init__(self, CIMIRequesterFunction=None):
        self._connected = False
        self._imBackup = False
        self._imLeader = False
        self._imCapable = False
        self._leaderFailed = False
        self._backupSelected = False
        self._startupCorrect = False
        self._deviceID = ''
        self._leaderIP = ''
        self._backupPriority = -1

        self.backupDatabase = []
        self.backupDatabaseLock = threading.Lock()

        self._CIMIRequesterFunction = CIMIRequesterFunction
        self.th_proc = None
        self.th_keep = None
        self.isStarted = False

    def __imLeader(self):
        """

        :return:
        """
        self._imLeader = self.__getCIMIData('leader', False)
        return self._imLeader

    def __imCapable(self):
        """

        :return:
        """
        # TODO: Capable by evaluation, not hardcoded
        return True  # By default, all agents will be capable to be leader.

    def __getCIMIData(self, key, default=None):
        """

        :return:
        """
        if self._CIMIRequesterFunction is None:
            value = default
        else:
            value = self._CIMIRequesterFunction(key, default)
        return value

    def imBackup(self):
        return self._imBackup

    def imLeader(self):
        return self._imLeader

    def getBackupDatabase(self):
        with self.backupDatabaseLock:
            ret = self.backupDatabase.copy()
        return ret

    def addBackup(self, deviceID, deviceIP, priority):
        found = False
        with self.backupDatabaseLock:
            for backup in self.backupDatabase:
                if backup.deviceID == deviceID:
                    LOG.debug(self.TAG + 'Backup {} found!'.format(deviceID))
                    found = True
                    break
        if not found:
            correct = self.__send_election_message(deviceIP)
            if correct:
                new_backup = BackupEntry(deviceID, deviceIP, priority)
                with self.backupDatabaseLock:
                    self.backupDatabase.append(new_backup)
                LOG.info('Backup {}[{}] added with priority {}'.format(deviceID, deviceIP, priority))
            return correct

    def deleteBackup(self, deviceID):
        """

        :param deviceID:
        :return:
        """
        # 1- Get and delete backup from database
        found = False
        correct = False
        with self.backupDatabaseLock:
            for backup in self.backupDatabase:
                if backup.deviceID == deviceID:
                    LOG.debug(self.TAG + 'Backup {} found!'.format(deviceID))
                    found = True
                    break
        if found:
            # Backup is in the database, delete him!
            with self.backupDatabaseLock:
                self.backupDatabase.remove(backup)
            # And now... Let him know...
            correct = self.__send_demotion_message(backup.deviceIP)
        return correct

    def start(self, deviceID): # TODO: Give deviceID at startup?
        """

        :return:
        """
        self._deviceID = deviceID
        if self.isStarted:
            LOG.warning(self.TAG + 'Procedure is already started...')
            return False
        else:
            self.th_proc = threading.Thread(name='area_res', target=self.__common_flow, daemon=True)
            self.th_proc.start()
            self.isStarted = True
            LOG.info(self.TAG + 'Module Started')
            return True

    def stop(self):
        """
        Stop all the module activity
        :return:
        """
        if self.isStarted:
            self._connected = False
            if self.th_proc is not None:
                while self.th_proc.is_alive():
                    LOG.debug(self.TAG + 'Waiting {} to resume activity...'.format(self.th_proc.name))
                    sleep(0.1)

            if self.th_keep is not None:
                while self.th_keep.is_alive():
                    LOG.debug(self.TAG + 'Waiting {} to resume activity...'.format(self.th_keep.name))
                    sleep(0.1)
            LOG.info(self.TAG + 'All threads stoped. AreaResilience module is stopped.')
        else:
            LOG.info(self.TAG + 'Module is not started')
        return

    def promotedToBackup(self, leaderIP):
        """
        The agent is promoted to be a backup
        :return:
        """
        # First check if Agent was electable
        self._leaderIP = leaderIP
        if self._imCapable:
            LOG.info(self.TAG + 'Becoming backup due leader selection.')
            # Then, check if AreaResilience thread is running
            if self.th_proc is None:
                pass
            elif not self.th_proc.is_alive():
                pass
            elif self._imLeader or self._imBackup:
                LOG.error('Agent is already a Backup/Leader. Cannot become a Backup.')
                return False
            else:
                LOG.warning('Area Resilience still starting. Cannot promote on this state. Waiting...')
                while self.th_proc.is_alive():
                    sleep(0.1)
                LOG.debug('Successful waiting.')
            LOG.debug('Module is ready for promotion.')
            self.th_proc = threading.Thread(name='area_res', target=self.__backupLeader_flow, daemon=True)
            self.th_proc.start()
            self.isStarted = True
            return True
        else:
            if not self._startupCorrect:
                LOG.warning('Area Resilience still starting. Cannot promote on this state.')
            else:
                LOG.error('Agent not capable to be Backup/Leader')
            return False

    def __common_flow(self):
        self._connected = True
        if not self.__imLeader():
            LOG.info(self.TAG + 'I\'m not a Leader.')
            # I'm not a leader
            if self.__imCapable():
                LOG.info(self.TAG + 'I\'m capable to be Leader.')
                self._imCapable = True
                # Can be a backup
                self.__preSelectionSetup()
                LOG.info(self.TAG + 'Waiting to be selected.')
            else:
                # Can not be a backup
                LOG.info(self.TAG + 'I\'m NOT capable to be Leader.')
        self._startupCorrect = True
        if self._imLeader:
            # Starting as Leader
            self.__backupLeader_flow()
        return

    def __backupLeader_flow(self):
        if not self._connected:
            LOG.error('Module stoped due _connected = False')
            return

        if not self._imLeader:
            # I've been promoted as backup
            LOG.info(self.TAG + 'I\'m selected to be a backup. Seting up')
            self.__preBackupSetup()
            self.__becomeBackup()

        if not self._connected:
            return

        if self._imLeader or self._leaderFailed:
            # I'm a leader
            LOG.info(self.TAG + 'Leader seting up')
            self.__becomeLeader()
            self.__backupSelection()
        return

    def __becomeLeader(self):  # TODO
        """

        :return:
        """
        # 1- Shutdown/Notify all the modules involving Agent to Leader transiction.
        if self._leaderFailed:
            # Only if leader fails, triggers are needed, otherwise no action is required
            try:
                r = requests.get(URLS.build_url_address('{}leader'.format(URLS.URL_POLICIES_ROLECHANGE), portaddr=('127.0.0.1', '46050'))) #TODO Addr+Prt by CPARAMS; Parametrize
                LOG.info(self.TAG + 'Trigger to AgentStart Switch done. {}'.format(r.json()))
                self._imLeader = True
                self._imBackup = False
            except Exception as ex:
                LOG.exception(self.TAG + '_becomeLeader trigger to AgentStart failed')
        self.th_keep = threading.Thread(name='ar_keeper', target=self.__keeper, daemon=True)
        self.th_keep.start()

    def __getTopology(self):  # TODO: Get actual CIMI data or Topology from environment
        """

        :return:
        """
        return self.__getCIMIData('topology', default=[]).copy()

    def __backupSelection(self):
        """

        :return:
        """
        # TODO:
        # 1- Check Backups
        # 2- Enough backups?
        # YES: End sleep(X)
        # NO:
        # 3- Get topology and select one agent
        # If not capable: Go to 3
        # 4- promote to Backup
        # Success: Correct_backups++
        # Go to 2

        while self._connected:
            correct_backups = 0
            with self.backupDatabaseLock:
                # Check backups
                for backup in self.backupDatabase:
                    if backup.TTL >= 0:
                        correct_backups += 1
            # Enough?
            if correct_backups >= self.MINIMUM_BACKUPS:
                # Enough backups
                LOG.debug('{} correct backup dettected in Leader. Everything is OK.'.format(correct_backups))
            else:
                # Not enough
                if not self._connected:
                    break
                LOG.warning('{} backup dettected are not enough. Electing new ones...'.format(correct_backups))
                topology = self.__getTopology()
                new_backups = []
                while self._connected and correct_backups < self.MINIMUM_BACKUPS and len(topology) > 0:
                    device = topology[0]
                    topology.remove(device)
                    # Todo: Evaluate if selected device is capable
                    correct = self.__send_election_message(device.get('deviceIP'))
                    if correct:
                        new_backup = BackupEntry(device.get('deviceID'), device.get('deviceIP'), 1)
                        with self.backupDatabaseLock:
                            self.backupDatabase.append(new_backup)
                        LOG.info('Backup {}[{}] added with priority {}'.format(device.get('deviceID'), device.get('deviceIP'), 1))
                        correct_backups += 1
                        new_backups.append(new_backups)

                if correct_backups >= self.MINIMUM_BACKUPS:
                    # Now we have enough
                    LOG.info('{} correct backups dettected in Leader. {} new backups added.'.format(correct_backups, len(new_backups)))
                else:
                    LOG.warning('{} backups dettected are not enough. Waiting for new election.'.format(correct_backups))
            # Sleep
            if self._connected:
                sleep(self.TIME_TO_WAIT_BACKUP_SELECTION)
        LOG.info('Leader stopped...')

    def __preSelectionSetup(self):
        """

        :return:
        """
        return

    def __preBackupSetup(self):
        """

        :return:
        """
        if self._imBackup:
            pass  # Do something here if necessary

    def __becomeBackup(self):
        """

        :return:
        """
        # 1- Send the KeepAlive message to the leader.
        # 2- Receive the reply (with preference number).
        # If leader down, Backup becomes leader.
        # Else repeat.

        attempt = 0
        counter = 0
        payload = {
            'deviceID': self._deviceID
        }
        self._imBackup = True
        while self._connected and attempt < self.MAX_RETRY_ATTEMPTS:
            stopLoop = False
            while self._connected and not stopLoop:
                try:
                    # 1. Requests to Leader Keepalive endpoint
                    r = requests.post(URLS.build_url_address(URLS.URL_POLICIES_KEEPALIVE, portaddr=(self._leaderIP, CPARAMS.POLICIES_PORT)), json=payload, timeout=0.5)
                    LOG.debug(self.TAG + 'Keepalive sent [#{}]'.format(counter))
                    # 2. Process Reply
                    jreply = r.json()
                    if r.status_code == 200:
                        leaderID = jreply['deviceID']   # Todo: Use this
                        priority = jreply['backupPriority']
                        # 3. Update Preference
                        self._backupPriority = priority
                        LOG.debug(self.TAG + 'Reply received, Leader still alive: LeaderID: {}'.format(leaderID))
                        attempt = 0
                    else:
                        # Error?
                        LOG.error('KeepAlive status_code = {}'.format(r.status_code))
                        if r.status_code == 403 and self.PRIORITY_ON_DEMOTION == jreply['backupPriority']:
                            LOG.warning('Backup has been removed from database or not authorized to send keepalive messages')
                        elif r.status_code == 405 and self.PRIORITY_ON_FAILURE == jreply['backupPriority']:
                            LOG.warning('Sending message to a Device that is not a Leader!')
                            stopLoop = True
                        else:
                            stopLoop = True

                    if not stopLoop:
                        # 4. Sleep
                        sleep(self.TIME_KEEPALIVE)
                    counter += 1
                except:
                    # Connection broke, backup assumes that Leader is down.
                    LOG.debug('Keepalive connection refused')
                    stopLoop = True
            LOG.warning('Keepalive connection is broken... Retry Attempts: {}'.format(self.MAX_RETRY_ATTEMPTS-(attempt+1)))
            attempt += 1

        if not self._connected:
            LOG.info('Backup stopped.')
        else:
            LOG.warning(self.TAG + '## LEADER IS DOWN! ##')
        self._leaderFailed = True
        return

    def __keeper(self):
        """
        Thread that reduces the TTL of a backup and demotes if TTL <= 0
        :return:
        """
        LOG.debug('Keeper is running')
        with self.backupDatabaseLock:
            self.backupDatabase = []    # Restart database
        while self._connected:
            with self.backupDatabaseLock:
                for backup in self.backupDatabase:
                    # Reduce TTL
                    backup.TTL -= 1
                    if backup.TTL < 0:
                        # Backup is down
                        LOG.warning('Backup {}[{}] is DOWN with TTL: {}'.format(backup.deviceID, backup.deviceIP, backup.TTL))
                        self.__send_demotion_message(backup.deviceIP)
                        # Remove from list
                        self.backupDatabase.remove(backup)  # TODO: Inform CIMI?
                        LOG.debug('Backup removed from database.')
                    else:
                        # Backup is ok
                        LOG.debug('Backup {}[{}] is OK with TTL: {}'.format(backup.deviceID, backup.deviceIP, backup.TTL))
            if self._connected:
                sleep(self.TIME_KEEPER)
        LOG.warning('Keeper thread stopped')

    def __send_election_message(self, address):
        """

        :param address: IP address for election
        :return: True if correct election, False otherwise
        """
        try:
            r = requests.get('{}backup'.format(URLS.build_url_address(URLS.URL_POLICIES_ROLECHANGE, addr=address, port=CPARAMS.POLICIES_PORT)), timeout=1.5)
            if r.status_code == 200:
                # Correct
                return True
            else:
                LOG.warning('Selected device [{}] received {} status code received on electing a new backup'.format(address,r.status_code))
                return False
        except timeout:
            LOG.warning('Selected device [{}] cannot become Backup due timeout'.format(address))
            return False
        except:
            LOG.exception('Selected device [{}] cannot become Backup due error in election message'.format(address))
            return False

    def __send_demotion_message(self, address):
        """
        Demote a backup to normal agent
        :param address: IP address for demotion
        :return: True if correct demotion, False otherwise
        """
        try:
            r = requests.get('{}agent'.format(
                URLS.build_url_address(URLS.URL_POLICIES_ROLECHANGE, addr=address, port=CPARAMS.POLICIES_PORT)),
                timeout=1.5)
            if r.status_code == 200:
                # Correct
                return True
            else:
                LOG.warning('Selected device [{}] received {} status code received on removing a backup'.format(address, r.status_code))
                return False
        except timeout:
            LOG.warning('Selected device [{}] cannot be demoted to Agent due timeout'.format(address))
            return False
        except:
            LOG.exception('Selected device cannot become Agent due error in demotion message')
            return False

    def receive_keepalive(self, deviceID):
        with self.backupDatabaseLock:
            for backup in self.backupDatabase:
                if backup.deviceID == deviceID:
                    # It's a match
                    backup.TTL = BackupEntry.MAX_TTL
                    LOG.debug(
                        'backupID: {}; backupIP: {}; priority: {}; Keepalive received correctly'.format(backup.deviceID,
                                                                                                        backup.deviceIP,
                                                                                                        backup.priority))
                    return True, backup.priority
        return False, self.PRIORITY_ON_DEMOTION
