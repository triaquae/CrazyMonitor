#_*_coding:utf-8_*_
__author__ = 'Alex Li'
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CrazyMonitor.settings")

    from monitor.backends.management import execute_from_command_line

    execute_from_command_line(sys.argv)
