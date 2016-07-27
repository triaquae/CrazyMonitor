#_*_coding:utf-8_*_
__author__ = 'Alex Li'

import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from core import main

if __name__ == "__main__":
    client = main.command_handler(sys.argv)


