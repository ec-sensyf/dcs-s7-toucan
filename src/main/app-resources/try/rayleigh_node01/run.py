#!/opt/anaconda/bin/python

# has to be anaconda, not /usr/bin/env, otherwise Hadoop won't set up the right environment. Cheers Hadoop.

#import site
import os
import sys
import atexit


import numpy as np
from datetime import datetime as dt
from calendar import isleap

sys.path.insert(0, '/data/TOUCAN')
import toucan_config
from imagedb import imagedb
import rayleigh

import cioppy
ciop = cioppy.Cioppy() 

# ----------------------------------------------------------------------------------------
# define the exit codes (from dcs-handson-10)
SUCCESS = 0
ERR_BEAM = 2
ERR_NOEXPR = 3
ERR_NOINPUT=4

# add a trap to exit gracefully
def clean_exit(exit_code):
    log_level = 'INFO'
    if exit_code != SUCCESS:
        log_level = 'ERROR'  
   
    msg = {SUCCESS: 'Processing successfully concluded',
           ERR_BEAM: 'Beam_expr failed to process product',
           ERR_NOEXPR: 'No expression provided',
           ERR_NOINPUT: 'No input provided'}
 
    ciop.log(log_level, msg[exit_code])  


# ----------------------------------------------------------------------------------------
def decyear(da):
    # get decimal year from da string
    d = dt.strptime(da, '%Y-%m-%d')
    doy = d.timetuple()[7]        # day-of-year from 1 (Jan 1st)
    y,m,d = da.split('-')
    days_in_year = 365.0
    if isleap(int(y)):
        days_in_year += 1.0

    return float(y) + (doy-1.0)/days_in_year

# ----------------------------------------------------------------------------------------
def main():
    # write a log entry
    ciop.log('INFO', 'Python DCS')

    """
    # only useful if you can actually set different parameters from different workflows
    chlconc = ciop.getparam('chlconc')
    try:
        chlconc = float(ciop.getparam('chlconc'))
    except:
        ciop.log('ERROR', 'Can\'t convert "%s"' % chlconc)
        sys.exit(1)
    """

    # hard-code
    chlconc = 0.035

    ciop.log('INFO', 'chlconc: %s' % chlconc)

    for line in sys.stdin:
        ciop.log('INFO', 'processing input: ' + line)

    # get list of snippets and metadata

    snippets = []

    im = imagedb('imagedb')
    # some 'valid' snippets
    #"""
    for y,f in ( (2003,'MER_RR__1PRMAP20030420_184537_000001942015_00385_05950_0001.N1'),
        (2003,'MER_RR__1PRMAP20030706_182546_000002002017_00485_07052_0001.N1'),
        (2007,'MER_RR__1PNMAP20070319_183412_000002002056_00299_26405_0001.N1'),
        (2008,'MER_RR__1PRMAP20080505_185410_000001862068_00199_32317_0001.N1'),
        (2009,'MER_RR__1PRMAP20090131_183658_000001972076_00070_36196_0001.N1'),
        (2009,'MER_RR__1PRMAP20090806_185954_000001832081_00242_38873_0001.N1'),
        (2010,'MER_RR__1PRBCM20100529_185911_000000562089_00471_43110_0001.N1'),
        (2011,'MER_RR__1PRBCM20110311_184839_000000563100_00214_47211_0001.N1'),
        (2011,'MER_RR__1PRBCM20110521_184635_000000563102_00372_48231_0001.N1') ):
        # should be just one search result per pair
        r = im.search( q={'instrument':'MERIS','region':'SPG','year':y,'source_filename':f }, sortfields=['date'] )
    #"""

    #r = im.search( q={'instrument':'MERIS', 'region':'SPG', 'year':{'$lte':2012} }, sortfields=['date'] )
    #r = im.search( q={'instrument':'MERIS', 'region':'BOUSSOLE', 'year':{'$lte':2012} }, sortfields=['date'] )
    for k in r:
        snippets.append( (k['date'], '%s/%s' % (k['archive_location'],k['archive_filename']),
            '%s/%s' % (k['source_location'],k['source_filename'])) )
    del im

    #for s in snippets:
    #    print s
    #exit(0)

    #r = rayleigh.RayleighScattering('meris')
    #coeff = r.run(snippets[0][1])
    #for l in r.actualparams['rrstoa']:
    #    print '%.6E' % l
    #sys.exit(0)

    r = rayleigh.RayleighScattering('meris', chl_conc=[chlconc])

    csv = []
    for (d,snippet_file,source_file) in snippets[:3]:
        line = ['%.3f' % decyear(d)]        # store decimal year as string to avoid reformatting
        coeff = r.run(snippet_file)
        a = r.actualparams
        for k in ('sza','vza','delta_phi','air_mass','u10','cloud_percent','pixel_count',
            'aerosol_reference_rho','aerosol_rho_r','aerosol_rcnr','tau550','used_tau550',
            'rho_path','total_trans','rho_w','rho_toa','meas_rho_toa','calib'):
            if k in a:
                if isinstance(a[k],list):
                    line += a[k]
                else:
                    line.append(a[k])
            else:
                line.append('N/A')

        csv.append(line)

    # ------------------------------------------------------------
    # create the output folder to store the output products and export it
    output_path = os.path.join(ciop.tmp_dir, 'output')
    os.makedirs(output_path)
    os.chdir(output_path)
    outputfile = 'rayleigh_output.csv'

    with open(outputfile, 'w') as csvfile:
        h = 'time,sza,vza,delta_phi,air_mass,u10,cloud_pct,pixel_count,aerosol_reference_rho,aerosol_rho_r,aerosol_rcnr,tau550,used_tau550,'
        for f in 'rho_path','t_tot','rho_w','rho_toa','meas_rho_toa','calib':
            for w in (413,443,490,510,560,620,665,681,709,754,762,779,865,885,900):
                h += '%s_%d,' % (f,w)

        print >>csvfile, '"%s"' % h.replace(',','","')
        for row in csv:
            line = []
            for e in row:
                if isinstance(e,float):
                    # includes numpy.float64
                    line.append('%.6E' % e)
                elif e is np.nan:
                    line.append('"NaN"')
                else:
                    line.append('"%s"' % str(e))
            print >>csvfile, ','.join(line)

    os.chdir(ciop.tmp_dir)      # not sure why
    ciop.log('INFO', 'Publishing ' + outputfile)
    ciop.publish(os.path.join(output_path, outputfile), metalink=True)


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
ciop.log('INFO', 'Finished Rayleigh job.')

