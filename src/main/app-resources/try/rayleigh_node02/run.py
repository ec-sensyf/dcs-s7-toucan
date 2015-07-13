#!/opt/anaconda/bin/python

import os
import sys

import cioppy
ciop = cioppy.Cioppy() 

import subprocess

src = 's3://toucan/snippets/imagedb/Site_SPG/MERIS/Proc_3rd_Reprocessing/2011/MER_RR__1PRBCM20110521_184635_000000563102_00372_48231_0001.tif'

output_path = os.path.join(ciop.tmp_dir, 'output')
os.makedirs(output_path)
dest = os.path.join(output_path, 'a.tif')

cmd = ['/usr/bin/s3cmd', 'get', src, dest]
try:
    retcode = subprocess.call(cmd)
    if retcode!=0:
        raise IOError
except:
    raise IOError('Error running s3cmd: "%s"' % cmd)
print "Success."
