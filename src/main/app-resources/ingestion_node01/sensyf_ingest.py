#!/opt/anaconda/bin/python

import sys
import os.path
from os import makedirs
import argparse
import importlib
#import json
#import numpy as np

# Toucan modules
#sys.path.insert(0, '/opt/anaconda/pkgs/toucan-0.2.1-py27_0/lib/python2.7/site-packages/TOUCAN')
##import toucan_config
#import libingest
#from imagedb import imagedb
#from toucanio import toucanio

# packaged version on cluster
#import TOUCAN.toucan_config as toucan_config
from TOUCAN.instruments import libingest

# -------------------------------------------------------------------------------------------
class Ingest:
    def __init__(self, db, parameter_json): #parameter_file):
        # keep parameter file local (for now) - i.e. don't use toucanio object here
        #self.user_params_all = json.load(open(parameter_file, 'r'))
        self.user_params_all = parameter_json
        #try:
        #    self.Image = imagedb(db)
        #except:
        #    raise NameError('Can\'t connect to database.')

    # ----------------------
    def ingest(self):
        # read each user parameter section (JSON entry) and process image
        for self.user_params in self.user_params_all:
            self.filename = self.user_params.get('filename', '')
            self.inputdir = '.'
            #self.inputdir = self.user_params.get('inputdir', '')
            #self.outputdir = self.user_params.get('outputdir', '')

            # more specific error-reporting needed
            #if self.filename=='' or self.inputdir=='' or self.outputdir=='':
            #    print 'Error in file input parameter(s).'
            #    continue

            # Does current filename plus region match any ingested ones?
            #f = self.Image.search( {'source_filename':self.filename, 'region':self.user_params['region_name'].upper()} )
            #if f!=[]:
            #    print '%s already ingested.' % self.filename
            #    continue

            print 'Ingesting %s ..' % self.filename
            # Make directory tree for archive data, if needed.
            #try:
            #    toucanio.make_dirtree(self.outputdir)
            #except:
            #    # tree already created, no action required
            #    pass

            # the call will read self.user_params and create self.metadata for each direction
            self.read_data()
            if self.data is None:
                # there has been an error reading the file - continue to next file
                print 'Error reading file:', self.filename
                continue

            # use same filename for every snippet entry - only one quicklook file
            self.quicklook_filename = '%s.jpg' % (os.path.splitext(self.user_params['filename'])[0])
            #libingest.make_quicklook(self)

            # one pass for each viewing direction (could be just one, i.e. default)
            for direction in self.metadata['directions']:
                # for adding to database
                if direction is None:
                    self.archive_filename = '%s.tif' % (os.path.splitext(self.user_params['filename'])[0])
                else:
                    self.archive_filename = '%s_%s.tif' % (os.path.splitext(self.user_params['filename'])[0], direction)
                #libingest.save_geotiff(self, direction)
                #self.add_to_database(direction)
                return self.metadata[direction]


    # ----------------------
    def read_data(self):
        """
        Read in data from the current data file (reflectance, coordinates, etc). This
        method is a wrapper to call various others depending on the file type

        :return: Dictionary holding all the data
        :raises IOError: if the requested instrument type is not coded
        """

        instrument = self.user_params['instrument']
        linstrument = self.user_params['instrument'].lower()               # canonicalise to lower-case
        try:
            reader = importlib.import_module('TOUCAN.instruments.%s.ingest_%s' % (instrument,linstrument))
            # e.g. import TOUCAN.instruments.MERIS.ingest_meris -> reader=ingest_meris
        except ImportError:
            raise IOError('No reader for instrument %s.' % instrument)

        # every reader module has a read_image function
        self.data = reader.read_image(self)


    # ----------------------
    def array_mean(self, a):
        """
        Calculate the mean of a 2D Numpy array, properly taking into account NaNs, without warnings or errors.
        """

        if np.isnan(a).all():
            # consists of all NaNs
            return np.NaN
        else:
            return float(np.nanmean(a))


    # ----------------------
    def add_to_database(self, direction):
        """
        Add the current image to the database

        :param direction: Current viewing direction to use; could be None for default direction.
        """

        # get image data and metadata for specified direction
        data = self.data[direction]
        metadata = self.metadata[direction]

        coords = self.user_params['region_coords']

        # Store the auxiliary data, if defined. Set to None if not.
        aux = {}
        for aux_var in 'atm_press', 'ozone', 'rel_hum', 'zonal_wind', 'merid_wind':
            if aux_var in metadata:
                aux[aux_var] = self.array_mean(data[metadata[aux_var]])
            else:
                aux[aux_var] = None

        # store various representations of date/timestamp for convenience
        datetime_string = metadata['datetime'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        date_string = metadata['datetime'].strftime('%Y-%m-%d')
        year = int(metadata['datetime'].year)

        region_name = self.user_params['region_name'].upper()
        instrument = self.user_params['instrument'].upper()

        #u = libingest.units_and_name(self.metadata['vartype'])
        d = {   # denormalised ('embedded') fields - will need to think about references instead (maybe), in some cases.
            'region': region_name,
            'instrument': instrument,
            'proclevel': self.user_params['proclevel'],
            'measurement_type': metadata['vartype'].lower(),
            'measurement_units': 'NA',       # u['units'],
            'measurement_long_name': 'NA',   # u['long_name'],
            'wavelengths': metadata['wavelengths'],

            'source_location': self.inputdir,
            'archive_location': self.outputdir,
            'source_filename': self.filename,
            'archive_filename': self.archive_filename,
            'quicklook_filename': self.quicklook_filename,
            'top_left_point': 'POINT({0} {1})'.format(coords[2], coords[1]),
            'bot_right_point': 'POINT({0} {1})'.format(coords[3], coords[0]),
            'datetime': datetime_string,                  # Python datetime object as string - in ISO8601 format (and UTC)
            'date': date_string,                          # Data as string, for convenience in sort/search
            'year': year,                                 # Year as int for convenience in sort/search
            'direction': direction,
            'atm_press': aux['atm_press'],
            'zonal_wind': aux['zonal_wind'],
            'merid_wind': aux['merid_wind'],
            'rel_hum': aux['rel_hum'],
            'ozone': aux['ozone'],
        }

        if self.Image.search(d)!=[]:
            print 'Metadata already entered!'
        else:
            # store means of viewing angles (or NaN if none), with lower-case names
            for angle in 'SZA','SAA','VZA','VAA':
                d[angle.lower()] = self.array_mean(data[angle])
            self.Image.insert(d)
            print 'Inserted new metadata.'


    # ----------------------
    def __del__(self):
        # finished with database here
        try:
            del self.Image
        except:
            # ignore if connection not created in the first place
            pass

