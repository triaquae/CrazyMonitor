from django.test import TestCase

# Create your tests here.


# if cpu.idle < 10 or cpu.iowait > 30 and mem.usage > 90  = warning
#
#
#     10:10:00    10:11:00
# 10:09:10    10:10:10


from django.db import models

class Host(models.Model):
    pass

class