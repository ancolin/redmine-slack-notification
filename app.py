# coding: utf-8
import sys
from utils import Utils

u = Utils()
u.setFlgDebug(True)

try:
    argv = sys.argv

    if len(argv) < 2:
        print('this script need 1 argument.')
        print('#1 configure file (ex. ./configure.json)')
    else:
        # set configure
        u.setConfigure(argv[1])

        # set monitoring ticket ids
        u.setMonitoringTicketIds()

        # check atom
        u.checkAtoms()

        # notify
        u.notify()
except Exception as e:
    u.log(e)
