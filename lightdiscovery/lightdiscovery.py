#!/usr/bin/env python3

"""
    Light Discovery and Categorization

"""

import threading
import requests
import socket
from time import sleep
from json import dumps, loads, JSONDecodeError
import psutil as psutil


from common.logs import LOG
from common.common import CPARAMS, URLS

__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'


class LightDiscovery:
    def __init__(self, bcast_addr, deviceID):
        self._connected = False
        self._isStarted = False
        self._isBroadcasting = False
        self._isScanning = False
        self._deviceID = deviceID

        self._bcast_addr = bcast_addr
        self._th_proc = threading.Thread()
        self._db_lock = threading.Lock()
        self._db = {}
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def startBeaconning(self):
        if self._isStarted or self._isBroadcasting:
            LOG.warning('LDiscovery is already started: isStarted={} isBroadcasting={}'.format(self._isStarted, self._isBroadcasting))
            return False
        self._th_proc = threading.Thread(name='LDiscB', target=self.__beaconning_flow, daemon=True)
        self._connected = True
        self._isStarted = True
        self._isBroadcasting = True
        self._db = {}
        self._th_proc.start()
        LOG.info('LDiscovery successfully started in Beacon Mode.')
        return True

    def stopBeaconning(self):
        if self._isStarted and self._isBroadcasting:
            self._connected = False
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
                self._socket.close()
                LOG.debug('Socket closed on beaconing')
            except:
                pass
            self._th_proc.join()
            LOG.info('LDisc Beaconning Stopped')
            self._isBroadcasting = False
            self._isStarted = False
        else:
            LOG.warning('LDisc is not Beaconning.')
        return True

    def startScanning(self):
        if self._isStarted or self._isScanning:
            LOG.warning('LDiscovery is already started: isStarted={} isScanning={}'.format(self._isStarted,
                                                                                               self._isScanning))
            return False
        self._th_proc = threading.Thread(name='LDiscS', target=self.__scanning_flow, daemon=True)
        self._connected = True
        self._isStarted = True
        self._isScanning = True
        self._th_proc.start()
        LOG.info('LDiscovery successfully started in Scan Mode.')
        return True

    def stopScanning(self):
        if self._isStarted and self._isScanning:
            self._connected = False
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
                self._socket.close()
                LOG.debug('Socket closed on scanning')
            except:
                pass
            self._th_proc.join()
            LOG.info('LDisc Scanning Stopped')
            self._isScanning = False
            self._isStarted = False
        else:
            LOG.warning('LDisc is not Scanning.')
        return True

    def recv_reply(self, payload, deviceIP):
        try:
            dev_obj = DeviceInformation(dict=payload)
            dev_obj.deviceIP = deviceIP
            with self._db_lock:
                self._db.update({dev_obj.deviceID: dev_obj})
            LOG.debug('Topology added/modified device: {}'.format(dev_obj))
            return True
        except:
            LOG.exception('Error on receiving reply from device to a beacon.')
            return False

    def get_topology(self):
        with self._db_lock:
            return [(self._db[item].deviceID, self._db[item].deviceIP) for item in self._db]

    def __beaconning_flow(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        beacon = dumps({
            'leaderID': self._deviceID
        })
        while self._connected:
            try:
                LOG.debug('Sending beacon at [{}:{}]'.format(CPARAMS.BROADCAST_ADDR_FLAG,CPARAMS.LDISCOVERY_PORT))
                self._socket.sendto(beacon.encode(),(CPARAMS.BROADCAST_ADDR_FLAG, CPARAMS.LDISCOVERY_PORT))
                sleep_ticks = 0
                while sleep_ticks < 5 / .1:     # TODO: Policies
                    if not self._connected:
                        break
                    else:
                        sleep_ticks += 1
                        sleep(0.1)
            except:
                LOG.exception('Error sending beacons')
                self._connected = False


    def __scanning_flow(self):
        # 1. Get Beacon
        # 2. Categorize
        # 3. Send Categorization info
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._socket.bind(('0.0.0.0', CPARAMS.LDISCOVERY_PORT))
            LOG.info('Scan server created correctly')
        except:
            LOG.exception('Error on creating the scan receiver')
            return

        while self._connected:
            try:
                data, addr = self._socket.recvfrom(4096)
                if not self._connected:
                    break
                LOG.debug('Received beacon from [{}]: \"{}\"'.format(addr[0], data.decode()))
                cpu, mem, stg = self.__categorize_device()
                LOG.debug('CPU: {}, MEM: {}, STG: {}'.format(cpu,mem,stg))
                payload = DeviceInformation(deviceID=self._deviceID, cpuCores=cpu, memAvail=mem, stgAvail=stg).getDict()
                LOG.info('Sending beacon reply to Leader...')
                r = requests.post(URLS.build_url_address(URLS.URL_BEACONREPLY, portaddr=(addr[0],CPARAMS.POLICIES_PORT)),json=payload, timeout=2)
                if r.status_code == 200:
                    LOG.info('Discovery Message successfully sent to Leader')
                else:
                    LOG.warning('Discovery Message received error status code {}'.format(r.status_code))
            except:
                LOG.exception('Error on beacon received')
        try:
            self._socket.close()
            LOG.info('Scan Server Stopped')
        except:
            LOG.exception('Server Stop not successful')

    def __categorize_device(self):
        try:
            cpu_cores = int(psutil.cpu_count()) if psutil.cpu_count() is not None else -1
            mem_avail = float(psutil.virtual_memory().available / (2 ** 30))
            storage_avail = float(sum([psutil.disk_usage(disk.mountpoint).free for disk in psutil.disk_partitions()]) / 2 ** 30)
        except:
            LOG.exception('Categorization not successful')
            cpu_cores = 0
            mem_avail = .0
            storage_avail = .0
        finally:
            return cpu_cores, mem_avail, storage_avail

class DeviceInformation:
    def __init__(self, json=None, dict=None, **kwargs):
        self.deviceID = str(kwargs.get('deviceID') if kwargs.get('deviceID') is not None else '')
        self.deviceIP = str(kwargs.get('deviceIP') if kwargs.get('deviceID') is not None else '')
        self.cpu_cores = int(kwargs.get('cpuCores') if kwargs.get('deviceID') is not None else 0)
        self.mem_avail = float(kwargs.get('memAvail') if kwargs.get('deviceID') is not None else .0)
        self.stg_avail = float(kwargs.get('stgAvail') if kwargs.get('deviceID') is not None else .0)
        if json is not None:
            correct = self.setJson(json)
        if dict is not None:
            correct = self.setDict(dict)

    def getJson(self):
        return dumps({
            'deviceID' : str(self.deviceID),
            'deviceIP' : str(self.deviceIP),
            'cpu_cores': int(self.cpu_cores),
            'mem_avail': float(self.mem_avail),
            'stg_avail': float(self.stg_avail)
        })

    def setJson(self, json):
        try:
            ljson = loads(json)
            return self.setDict(ljson)
        except JSONDecodeError:
            LOG.exception('Error on getting new device via JSON.')
            return False

    def setDict(self, dict):
        try:
            self.deviceID = str(dict.get('deviceID'))
            self.deviceIP = str(dict.get('deviceIP'))
            self.cpu_cores = int(dict.get('cpu_cores'))
            self.mem_avail = float(dict.get('mem_avail'))
            self.stg_avail = float(dict.get('stg_avail'))
            return True
        except:
            LOG.exception('Error on getting new device via Dict.')
            return False

    def getDict(self):
        return {
            'deviceID': str(self.deviceID),
            'deviceIP': str(self.deviceIP),
            'cpu_cores': int(self.cpu_cores),
            'mem_avail': float(self.mem_avail),
            'stg_avail': float(self.stg_avail)
        }

    def __str__(self):
        return str(self.getDict())
