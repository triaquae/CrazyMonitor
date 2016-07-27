#!/usr/bin/env python
#coding:utf-8

#apt-get install sysstat

import commands
import subprocess

def monitor(frist_invoke=1):
    shell_command = 'sar 1 3| grep "^Average:"'
    status,result = commands.getstatusoutput(shell_command)
    #result = subprocess.Popen(shell_command,shell=True,stdout=subprocess.PIPE).stdout.read()
    if status != 0:
        value_dic = {'status': status}
    else: #data is correct
        value_dic = {}
        user,nice,system,iowait,steal,idle = result.split()[2:]
        value_dic= {
            'user': user,
            'nice': nice,
            'system': system,
            'iowait': iowait,
            'steal': steal,
            'idle': idle,
            'status': status
        }
    return value_dic

