#!/opt/anaconda/bin/python

#import site
import os
import sys
import atexit
import gzip

#sys.path.insert(0, '/data/TOUCAN')
#import toucan_config
from sensyf_ingest import Ingest

import cioppy
ciop = cioppy.Cioppy() 

# ----------------------------------------------------------------------------------------
# define some exit codes
SUCCESS = 0
ERR_NOINPUT=4

# add a trap to exit gracefully
def clean_exit(exit_code):
    log_level = 'INFO'
    if exit_code != SUCCESS:
        log_level = 'ERROR'  
   
    msg = {SUCCESS: 'Processing successfully concluded',
           ERR_NOINPUT: 'No input provided'}
 
    ciop.log(log_level, msg[exit_code])  


# ----------------------------------------------------------------------------------------
def main():
    # write a log entry
    ciop.log('INFO', '== Toucan ingestion ==')

    input_path = os.path.join(ciop.tmp_dir, 'input')
    os.makedirs(input_path)
    os.chdir(input_path)
    filecount = 0
    j = [{'filename':None, 'region_coords': [29.05, 28.05, 23.89, 22.89], 'instrument':'MERIS', 'region_name':'Libya4'}]

    ingestlog = [ ['SENSOR','REGION','DATE','FILENAME'] ]
    for inputfile in sys.stdin:
        # 2009-01-01..2009-01-02 is 1 image in the catalogue
        ciop.log('INFO', 'processing input: ' + inputfile)
        filecount += 1

        # catalogue products are gzipped
        prod = ciop.copy(inputfile, input_path, extract=True)
        bprod = os.path.basename(prod)
        ciop.log('INFO', 'Retrieved ' + bprod)
        j[0]['filename'] = prod
        i = Ingest('testdb', j)         # there is no database really
        d = i.ingest()
        if d is None:
            s = 'FAILED'
        else:
            s = d['datetime']
        ingestlog.append(['MERIS','Libya4',s,bprod])
        del i

    ciop.log('INFO', '%d source images.' % filecount)

    # ------------------------------------------------------------
    # create the output folder to store the output products and export it
    output_path = os.path.join(ciop.tmp_dir, 'output')
    os.makedirs(output_path)
    os.chdir(output_path)
    outputfile = 'ingestion.csv'
    p = os.path.join(output_path, outputfile)
    with open(p, 'w') as c:
        for l in ingestlog:
            print >>c, ','.join([str(e) for e in l])

    os.chdir(ciop.tmp_dir)      # not sure why
    ciop.log('INFO', 'Publishing ' + outputfile)
    ciop.publish(p, metalink=True)


# ----------------------------------------------------------------------------------------
try:
    main()
except SystemExit as e:
    if e.args[0]:
         clean_exit(e.args[0])
    raise
else:
    atexit.register(clean_exit, 0)

# finished
ciop.log('INFO', 'Finished ingestion.')

