#_*_coding:utf-8_*_
__author__ = 'Alex Li'


import subprocess

def monitor(frist_invoke=1):
    value_dic = {}
    shell_command = 'uptime'
    result = subprocess.Popen(shell_command,shell=True,stdout=subprocess.PIPE).stdout.read()

    #user,nice,system,iowait,steal,idle = result.split()[2:]
    value_dic= {
        'uptime': result,

        'status': 0
    }
    return value_dic


print monitor()
