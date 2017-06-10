#_*_coding:utf-8_*_
__author__ = 'Alex Li'

import os,sys
#from perpetual_machine import
import django
django.setup()
from monitor.backends import data_processing,trigger_handler
from CrazyMonitor import settings



class ManagementUtility(object):
    """
    Encapsulates the logic of the django-admin and manage.py utilities.

    A ManagementUtility has a number of commands, which can be manipulated
    by editing the self.commands dictionary.
    """
    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = os.path.basename(self.argv[0])
        self.settings_exception = None
        self.registered_actions = {
            'start':self.start,
            'stop': self.stop,
            'trigger_watch':self.trigger_watch,
        }

        self.argv_check()

    def argv_check(self):
        '''
        do basic validation argv checks
        :return:
        '''
        if len(self.argv) < 2:
            self.main_help_text()
        if self.argv[1] not in self.registered_actions:
            self.main_help_text()
        else:
            self.registered_actions[sys.argv[1]]()

    def start(self):
        '''start monitor server frontend and backend'''
        reactor = data_processing.DataHandler(settings)
        reactor.looping()

    def stop(self):
        '''stop monitor server'''

    def trigger_watch(self):
        '''start to listen triggers'''
        trigger_watch = trigger_handler.TriggerHandler(settings)
        trigger_watch.start_watching()

    def main_help_text(self, commands_only=False):
        """
        Returns the script's main help text, as a string.
        """
        if not commands_only:
            print("supported commands as flow:")
            for k,v in self.registered_actions.items():
                print("    %s%s" % (k.ljust(20),v.__doc__))
            exit()


    def execute(self):
        '''
        run according to user's input
        :return:
        '''
def execute_from_command_line(argv=None):
    """
    A simple method that runs a ManagementUtility.
    """
    utility = ManagementUtility(argv)
    utility.execute()
