#!/usr/bin/env python3

"""
    RESOURCE MANAGEMENT - POLICIES MODULE
    Logging Methods
"""

import logging
import colorlog     # https://github.com/borntyping/python-colorlog

__status__ = 'Production'
__maintainer__ = 'Alejandro Jurnet'
__email__ = 'ajurnet@ac.upc.edu'
__author__ = 'Universitat Politècnica de Catalunya'


FORMAT = '[POLICIES - %(threadName)-10s] %(log_color)s%(levelname)-10s:%(reset)s %(message_log_color)s%(message)s'
LOG = logging.getLogger('main')

if len(LOG.handlers) < 1: # To avoid duplicated LOGs due multiple handlers (more info: https://stackoverflow.com/a/7672941)
    # LOG.setLevel() <-- Do this in the main
    # Colors!
    COLOR_FORMATTER = colorlog.ColoredFormatter(
        FORMAT,
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red,bg_white',
        },
        secondary_log_colors={
            'message': {
                'ERROR': 'red',
                'CRITICAL': 'bold_red'
            }
        },
        style='%')

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    # ch.setLevel(logging.INFO)

    # create formatter - w/o color
    formatter = logging.Formatter(FORMAT)

    # add formatter to ch
    #ch.setFormatter(formatter)
    ch.setFormatter(COLOR_FORMATTER)

    # add ch to logger
    LOG.addHandler(ch)
