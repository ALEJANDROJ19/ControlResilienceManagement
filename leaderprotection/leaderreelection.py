#!/usr/bin/env python3

"""
    RESOURCE MANAGEMENT - POLICIES MODULE
    Leader Reelection - Choose with head

"""

import requests

from common.logs import LOG
from common.common import CPARAMS, URLS

__status__ = 'Production'
__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'


class LeaderReelection:
    @staticmethod
    def reelection(arearesilience, deviceID, deviceIP):
        # 0. Check if is not a backup
        backups = arearesilience.getBackupDatabase()
        LOG.debug('Backup database query: {}'.format(backups))
        found = False
        for backup in backups:
            if backup.deviceID == deviceID:
                found = True
                break

        # If backup: Go to step # 2
        if not found:
            LOG.debug('Device {} is not an active backup.'.format(deviceID))
            # 1. Promote device to Backup
            # Ok? Go to 3, return False otherwise
            ok = arearesilience.addBackup(deviceID, deviceIP, arearesilience.PRIORITY_ON_REELECTION)
            if not ok:
                LOG.error('Proposed device cannot be promoted to backup for reelection')
                return False
        else:
            LOG.info('Device {} is an active backup.'.format(deviceID))
            # 2. Change preference to 0
            backup.priority = arearesilience.PRIORITY_ON_REELECTION

        # 3. Demote other backups (if any)
        backups = arearesilience.getBackupDatabase()
        for backup in backups:
            if backup.deviceID != deviceID:
                # Delete
                ok = arearesilience.deleteBackup(backup.deviceID)
                if ok:
                    LOG.info('Backup {}[{}] demoted successfully due Leader Reelection.'.format(backup.deviceID, backup.deviceIP))
                else:
                    LOG.error('Error on Backup deletion {}[{}] in Leader Reelection.'.format(backup.deviceID, backup.deviceIP))

        # 4. Demote leader (rest call self)
        r = requests.get('{}agent'.format(URLS.build_url_address(URLS.URL_POLICIES_ROLECHANGE, portaddr=('127.0.0.1', CPARAMS.POLICIES_PORT))))
        if r.status_code == 200:
            # Correct
            LOG.info('Leader (self) demoted successfully')
            return True
        LOG.warning('Leader not demoted or confirmation not received')
        return False
