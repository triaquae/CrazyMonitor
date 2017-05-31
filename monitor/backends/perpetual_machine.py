#_*_coding:utf-8_*_
__author__ = 'Alex Li'

import sys,os
import django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CrazyMonitor.settings")
from CrazyMonitor import settings

django.setup()
from  monitor import models
from monitor.backends import data_processing



if __name__ == '__main__':
    reactor = data_processing.DataHandler(settings)
    reactor.looping()






