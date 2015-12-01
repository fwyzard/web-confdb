# -*- coding: utf-8 -*-
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Sequence
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from confdb_tables.confdb_tables import *

__all__ = ['SAEngine']

class SAEngine(object):
    def __init__(self, connection_string=None):

        self.log = logging.getLogger(__name__)

        self.sa_engine_online = None
        self.connection_string_online = connection_string.connectUrlonline
        self.session_online = scoped_session(sessionmaker(autoflush=True,
                                                   autocommit=False))

        self.sa_engine_offline = None
        self.connection_string_offline = connection_string.connectUrloffline
        self.session_offline = scoped_session(sessionmaker(autoflush=True,
                                                   autocommit=False))

    def start(self):
#        self.log.info('Starting up DBs access')
        self.log.error('Starting up DBs access')

        self.sa_engine_offline = create_engine(self.connection_string_offline, echo=False)
        self.sa_engine_online = create_engine(self.connection_string_online, echo=False)

        Base.prepare(self.sa_engine_offline, reflect=True)


    def stop(self):
#        self.log.info('Stopping down DBs access')
        self.log.error('Stopping down DBs access')

        if self.sa_engine_online:
            self.sa_engine_online.dispose()
            self.sa_engine_online = None

        if self.sa_engine_offline:
            self.sa_engine_offline.dispose()
            self.sa_engine_offline = None


    def bind_online(self):
        """
        Bind the online session to the online engine, and return it to the caller.
        """

        self.session_online.configure(bind=self.sa_engine_online)
        return self.session_online


    def bind_offline(self):
        """
        Bind the offline session to the offline engine, and return it to the caller.
        """

        self.session_offline.configure(bind=self.sa_engine_offline)
        return self.session_offline


    def commit_online(self):
        """
        Commits the current transaction or rollbacks if an error occurs.

        In all cases, the current session is unbound and therefore
        not usable any longer.
        """
        try:
            self.session_online.commit()
        except:
            self.session_online.rollback()
            raise
        finally:
            self.session_online.remove()

    def commit_offline(self):
        """
        Commits the current transaction or rollbacks if an error occurs.

        In all cases, the current session is unbound and therefore
        not usable any longer.
        """
        try:
            self.session_offline.commit()
        except:
            self.session_offline.rollback()
            raise
        finally:
            self.session_offline.remove()
