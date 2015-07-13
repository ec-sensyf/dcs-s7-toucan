#!/usr/bin/env python

import site
import os
import sys


import numpy as np
import sys
from datetime import datetime as dt
from calendar import isleap

sys.path.insert(0, '/data/TOUCAN')
import toucan_config
from imagedb import imagedb
import rayleigh

# add cioppy to the search path
sys.path.append('/usr/lib/ciop/python/')
import cioppy
ciop = cioppy.Cioppy() 

# write a log entry
ciop.log('INFO', 'Python DCS')

"""
# input comes from STDIN (standard input)
for line in sys.stdin:
 	# do elaboration
    ciop.log('INFO', 'processing input: ' + line)
"""

param1 = ciop.getparam('param1')
param2 = ciop.getparam('param2')
print 'param1 = %s' % param1
print 'param2 = %s' % param2

