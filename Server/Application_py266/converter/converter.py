# File converter.py Description:
#
# Class: Converter

from confdb_queries.confdb_queries import ConfDbQueries
from item_wrappers.FolderItem import *
from item_wrappers.ModuleDetails import *
from item_wrappers.Pathitem import *
from item_wrappers.Parameter import *
from item_wrappers.item_wrappers import *
from schemas.responseSchemas import *
from responses.responses import *
from data_builder import DataBuilder
import string
import re
import multiprocessing
import itertools

import os
import os.path
current_dir_log = os.path.dirname(os.path.abspath(__file__))

class Converter(object):

    queries = ConfDbQueries()

    def createConfig(self, ver=-2, cnf=-2, db = None, online="False", counter=None, current_dir="", use_cherrypy = False):

        if use_cherrypy:
            import cherrypy
            self.logger = cherrypy.log
        else:
            import multiprocessing, logging
            formatter = logging.Formatter("[%(asctime)s - %(levelname)s/%(processName)s] %(name)s: %(message)s")
            handler   = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger = multiprocessing.get_logger()
            self.logger.setLevel(logging.INFO)
            self.logger.addHandler(handler)

        version = None
        release = None
        try:
            version = DataBuilder.getRequestedVersion(ver, cnf, db)
        except Exception as e:
            msg = 'ERROR: Query getRequestedVersion Error: ' + e.args[0]
            self.logger.error(msg)

        if version == None:
            print "\nCould Not Find The Requested Version.\n"
            return

        self.data_builder = DataBuilder(db, version, self.logger)

        try:
            release = self.queries.getRelease(version.id_release, db, self.logger)
        except Exception as e:
            msg = 'ERROR: Query getRelease Error: ' + e.args[0]
            self.logger.error(msg)

        # Adding File's Headers
#        self.logger.info('retrieving header...')
        self.logger.error('retrieving header...')
        header = self.writeHeader(version.name, release.releasetag, version.processname)#version.config)
#        self.logger.info('done')
        self.logger.error('done')

        tasks = [
            ('modules',        'getModules'),
            ('psets',          'getGlobalPsets'),
            ('streams',        'getStreams'),
            ('datasets',       'getDatasetsPaths'),
            ('source',         'getEDSources'),
            ('esproducers',    'getESModules'),
            ('essources',      'getESSource'),
            ('services',       'getServices'),
            ('outputmodules',  'getOutputModules'),
            ('sequences',      'getSequences'),
            ('paths',          'getPaths'),
            ('endpaths',       'getEndPaths'),
            ('schedule',       'getSchedule'),
        ]

        # build each part of the configuration
        parts = {}
        import task
        pool = multiprocessing.Pool(processes = 8, initializer = task.initialize, initargs = (online, version, use_cherrypy))
        #task.initialize(online, version, use_cherrypy)
        for key, val in pool.imap_unordered(task.worker, tasks):
        #for key, val in itertools.imap(task.worker, tasks):
            parts[key] = val
        pool.close()
        pool.join()

        # combinine all parts
        data = \
            header + \
            parts['psets'] + \
            parts['streams'] + \
            parts['datasets'] + \
            parts['source'] + \
            parts['essources'] + \
            parts['esproducers'] + \
            parts['services'] + \
            parts['modules'] + \
            parts['outputmodules'] + \
            parts['sequences'] + \
            parts['paths'] + \
            parts['endpaths'] + \
            parts['schedule']

        try:
            file_name = current_dir + '/HLT.py'
            file = open(file_name,'w')
            file.write(data)
            file.close()
            return file_name
        except Exception as e:
            msg = 'ERROR: Writting to file Error: ' + file_name
            self.logger.error(msg)
            return None


    def writeHeader(self, version_name, release_tag, process_name):
        result = "# " + version_name + " (" + release_tag + ")" + "\n\n"
        result = result + 'import FWCore.ParameterSet.Config as cms\n\n'
        result = result + 'process = cms.Process( "' + process_name + '" )\n\n'
        result = result + 'process.HLTConfigVersion = cms.PSet(\n'
        result = result + self.data_builder.getTab(2) + "tableName = cms.string('" + version_name + "')\n)\n\n"

        return result

