# File exposed.py Description:
# This files contains the definitions of the classes mapping the tables in the DB
#
# Class: Pathidconf, Paths, Pathids, Pathelement, Pathitem, Pathitems, Paetypes,
#       Modelement, Moduleitem, ModTemplate, ModToTemp, ModTelement, Moduletypes
#       Directory, Configuration, Version


from sqlalchemy import Sequence
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, select, DateTime, case, and_, func, join, CLOB
from sqlalchemy.orm import relationship, backref, column_property, object_session
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql import text, literal_column

Base = automap_base()

#---------------- SoftRelease ------------
class Release(Base):
    # nome della tabella
    __tablename__ = 'u_softreleases'

    id = Column('id', Integer, primary_key=True)
    releasetag = Column(String)

#---------------- Path items: Paths, Paths in Version, Sequences, Moduels ------------
class Moduletypes(Base):
    __tablename__ = 'u_moduletypes'

    id = Column('id', Integer, primary_key=True)
    mtype = Column('type', String)

class ModTemplate(Base):
     # nome della tabella
    __tablename__ = 'u_moduletemplates'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)
    id_mtype = Column('id_mtype', Integer) #ForeignKey('u_moduletypes.id')
    mtype = column_property(
        select([Moduletypes.mtype]).where(Moduletypes.id == id_mtype)
    )

class ModToTemp(Base):
     # nome della tabella
    __tablename__ = 'u_mod2templ'

    id = Column('id', Integer, primary_key=True)
    id_pae = Column('id_pae', Integer, ForeignKey('u_paelements.id'))
    id_templ = Column('id_templ', Integer, ForeignKey('u_moduletemplates.id'))

class Pathidconf(Base):
    # nome della tabella
    __tablename__ = 'u_pathid2conf'

    id = Column('id', Integer, primary_key=True)
    id_confver = Column(ForeignKey('u_confversions.id'))
    id_pathid = Column(ForeignKey('u_pathids.id'))

class Paths(Base):
    # nome della tabella
    __tablename__ = 'u_paths'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)
    paetype = "pat"

class Pathids(Base):
    # nome della tabella
    __tablename__ = 'u_pathids'

    id = Column('id', Integer, primary_key=True)
    id_path = Column(ForeignKey('u_paths.id'))
    #isendpath = Column(Integer
    description = Column(CLOB)
    name = column_property(
        select([Paths.name]).where(Paths.id == id_path)
    )
    isEndPath = Column('isendpath', Integer)
    pit = "pat"

class Pathelement(Base):
    # nome della tabella
    __tablename__ = 'u_paelements'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)
    paetype = Column(Integer)
    id_templ = column_property(
        select([ModToTemp.id_templ]).where(ModToTemp.id_pae == id)
    )
    temp_name = column_property(
        select([ModTemplate.name]).where(and_(ModTemplate.id == ModToTemp.id_templ, ModToTemp.id_pae == id))
    )
    mtype = column_property(
        select([Moduletypes.mtype]).where(and_(Moduletypes.id == ModTemplate.id_mtype, ModTemplate.id == ModToTemp.id_templ, ModToTemp.id_pae == id))
    )

class Pathitems(Base):
    __tablename__ = 'u_pathid2pae'

    id = Column('id', Integer, primary_key=True)
    id_pathid = Column(Integer, ForeignKey('u_pathids.id'))
    id_pae = Column('id_pae', Integer, ForeignKey('u_paelements.id'))
    id_parent = Column(Integer)
    operator = Column(Integer)
    name = column_property(
        select([Pathelement.name]).where(Pathelement.id == id_pae)
    )
    paetype = column_property(
        select([Pathelement.paetype]).where(Pathelement.id == id_pae)
    )
    temp_name = column_property(
        select([Pathelement.name]).where(Pathelement.id == id_pae)
    )
    lvl = Column(Integer) #1, 'mod', 2, 'seq', 3, 'oum', 'Undefined'
    order = Column('ord', Integer)

class Paetypes(Base):
     # nome della tabella
    __tablename__ = 'u_paetypes'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)

class Variables(Base):
    # nome della tabella
    __tablename__ = 'u_variables'
    id = Column('id', Integer, primary_key=True)
    name = Column(String)

class Values(Base):
    # nome della tabella
    __tablename__ = 'u_values'
    id = Column('id', Integer, primary_key=True)
    value = Column(String)

class PathToVarVal(Base):
    # nome della tabella
    __tablename__ = 'u_pathid2varval'
    id = Column('id', Integer, primary_key=True)
    id_pathid = Column(Integer, ForeignKey('u_pathids.id'))
    id_var = Column(Integer, ForeignKey('u_variables.id'))
    id_val = Column(Integer, ForeignKey('u_values.id'))
    name = column_property(
        select([Variables.name]).where(Variables.id == id_var)
    )
    value = column_property(
        select([Values.value]).where(Values.id == id_val)
    )

#------------------ Module items: Pset, VPset, Params ---------------
class Modelement(Base):
     # nome della tabella
    __tablename__ = 'u_moelements'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)
    moetype = Column(Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)

class Moduleitem(Base):
     # nome della tabella
    __tablename__ = 'u_pae2moe'

    id = Column('id', Integer, primary_key=True)
    id_pae = Column('id_pae', Integer, ForeignKey('u_paelements.id'))
    id_moe = Column('id_moe', Integer, ForeignKey('u_moelements.id'))
    lvl = Column(Integer)
    ord = Column('ord',Integer)
    moetype = column_property(
        select([Modelement.moetype]).where(Modelement.id == id_moe).correlate(Modelement.__table__)
    )
    paramtype = column_property(
        select([Modelement.paramtype]).where(Modelement.id == id_moe).correlate(Modelement.__table__)
    )
    tracked = column_property(
        select([Modelement.tracked]).where(Modelement.id == id_moe).correlate(Modelement.__table__)
    )
    name = column_property(
        select([Modelement.name]).where(Modelement.id == id_moe).correlate(Modelement.__table__)
    )
    value = column_property(
        select([Modelement.value]).where(Modelement.id == id_moe).correlate(Modelement.__table__)
    )
    valuelob = column_property(
        select([Modelement.valuelob]).where(Modelement.id == id_moe).correlate(Modelement.__table__)
    )

class ModuleitemFull(Base):
    __tablename__ = 'u_pae2moe, u_moelements'

    id        = Column('id',        Integer, primary_key=True)
    id_pae    = Column('id_pae',    Integer, ForeignKey('u_paelements.id'))
    id_moe    = Column('id_moe',    Integer, ForeignKey('u_moelements.id'))
    lvl       = Column('lvl',       Integer)
    ord       = Column('ord',       Integer)
    moetype   = Column('moetype',   Integer)
    paramtype = Column('paramtype', String)
    tracked   = Column('tracked',   Integer)
    name      = Column('name',      String)
    value     = Column('value',     String)
    valuelob  = Column('valuelob',  CLOB)

#-------------------- ED Template and elements ------------------
class ModTelement(Base):
     # nome della tabella
    __tablename__ = 'u_modtelements'

    id = Column('id', Integer, primary_key=True)
    id_modtemp = Column('id_modtemplate', Integer, ForeignKey('u_moduletemplates.id'))
    moetype = Column(Integer)
    name = Column(String)
    lvl = Column(Integer)
    order = Column('ord',Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)

class ModTemp2Rele(Base):
    # nome della tabella
    __tablename__ = 'u_modt2rele'

    id = Column('id', Integer, primary_key=True)
    id_modtemp = Column('id_modtemplate', Integer, ForeignKey('u_moduletemplates.id'))
    id_release = Column(Integer)


#------------ Directories and directory items --------------------

class Directory(Base):
    __tablename__ = 'u_directories'

    id = Column('id', Integer, primary_key=True)
    id_parentdir = Column(Integer)
    name = Column(String)
    created = Column(DateTime)

class Configuration(Base):
    __tablename__ = 'u_configurations'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)

class Version(Base):
    # nome della tabella
    __tablename__ = 'u_confversions'
    # definisco che id \'e un numero intero in sequenza e chiave primaria
    id = Column('id', Integer, primary_key=True)
    id_config = Column('id_config', Integer, ForeignKey('u_configurations.id'))
    id_parentdir = Column('id_parentdir', Integer, ForeignKey('u_directories.id'))
    name = Column(String)
    id_release = Column('id_release', Integer, ForeignKey('u_softreleases.id'))
    version = Column(Integer)
    created = Column(DateTime)
    creator = Column(String)
    processname = Column(String)
    config = Column(String)
    description = Column(CLOB)
    releasetag = column_property(
        select([Release.releasetag]).where(Release.id == id_release)
    )


#------------ Service and Service Templates (plus items) --------------------

class SrvTemplate(Base):
    __tablename__ = 'u_srvtemplates'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)


class Srvt2Rele(Base):
    __tablename__ = 'u_srvt2rele'

    id = Column('id', Integer, primary_key=True)
    id_srvtemplate = Column('id_srvtemplate', Integer, ForeignKey('u_srvtemplates.id'))
    id_release = Column(Integer)

class SrvTempElement(Base):
    __tablename__ = 'u_srvtelements'

    id = Column('id', Integer, primary_key=True)
    id_srvtemplate = Column('id_srvtemplate', Integer, ForeignKey('u_srvtemplates.id'))
    moetype = Column(Integer)
    name = Column(String)
    lvl = Column(Integer)
    order = Column('ord',Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)

class Service(Base):
    __tablename__ = 'u_services'

    id = Column('id', Integer, primary_key=True)
    id_template = Column('id_template', Integer, ForeignKey('u_srvtemplates.id'))

class Conf2Srv(Base):
    __tablename__ = 'u_conf2srv'

    id = Column('id', Integer, primary_key=True)
    id_confver = Column('id_confver', Integer, ForeignKey('u_confversions.id'))
    id_service = Column('id_service', Integer, ForeignKey('u_services.id'))

class SrvElement(Base):
    __tablename__ = 'u_srvelements'

    id = Column('id', Integer, primary_key=True)
    id_service = Column('id_service', Integer, ForeignKey('u_services.id'))
    moetype = Column(Integer)
    name = Column(String)
    lvl = Column(Integer)
    order = Column('ord',Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)







#------------ Streams ------------------------------------------------------------


class Stream(Base):
    __tablename__ = 'u_streams'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)

class StreamId(Base):
    __tablename__ = 'u_streamids'

    id = Column('id', Integer, primary_key=True)
    id_stream = Column('id_stream', Integer, ForeignKey('u_streams.id'))
    fractodisk = Column(Integer)
    name = column_property(
        select([Stream.name]).where(Stream.id == id_stream)
    )

class PathidToOutM(Base):
    __tablename__ = 'u_pathid2outm'

    id = Column('id', Integer, primary_key=True)
    id_pathid = Column(Integer, ForeignKey('u_pathids.id'))
    id_streamid = Column('id_streamid', Integer, ForeignKey('u_streamids.id'))
    order = Column('ord',Integer)

#------------ Datasets ------------------------------------------------------------
class Dataset(Base):
    __tablename__ = 'u_datasets'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)

class DatasetId(Base):
    __tablename__ = 'u_datasetids'

    id = Column('id', Integer, primary_key=True)
    id_dataset = Column('id_dataset', Integer, ForeignKey('u_datasets.id'))
    name = column_property(
        select([Dataset.name]).where(Dataset.id == id_dataset)
    )

class PathidToStrDst(Base):
    __tablename__ = 'u_pathid2strdst'

    id = Column('id', Integer, primary_key=True)
    id_pathid = Column(Integer, ForeignKey('u_pathids.id'))
    id_streamid = Column('id_streamid', Integer, ForeignKey('u_streamids.id'))
    id_datasetid = Column('id_datasetid', Integer, ForeignKey('u_datasetids.id'))


class ConfToStrDat(Base):
    __tablename__ = 'u_conf2strdst'

    id = Column('id', Integer, primary_key=True)
    id_confver = Column('id_confver', Integer, ForeignKey('u_confversions.id'))
    id_datasetid = Column('id_datasetid', Integer, ForeignKey('u_datasetids.id'))
    id_streamid = Column('id_streamid', Integer, ForeignKey('u_streamids.id'))

#------------ Event Contents (with statements) ----------------------------------------
class EventContent(Base):
    __tablename__ = 'u_eventcontents'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)

class EventContentId(Base):
    __tablename__ = 'u_eventcontentids'

    id = Column('id', Integer, primary_key=True)
    id_evco = Column('id_evco', Integer, ForeignKey('u_eventcontents.id'))
    name = column_property(
        select([EventContent.name]).where(EventContent.id == id_evco)
    )

class ConfToEvCo(Base):
    __tablename__ = 'u_conf2evco'

    id = Column('id', Integer, primary_key=True)
    id_evcoid = Column('id_evcoid', Integer, ForeignKey('u_eventcontentids.id'))
    id_confver = Column('id_confver', Integer, ForeignKey('u_confversions.id'))


class EvCoStatement(Base):
    __tablename__ = 'u_evcostatements'

    id = Column('id', Integer, primary_key=True)
    classn = Column(String)
    modulel = Column(String)
    extran = Column(String)
    processn = Column(String)
    statementtype = Column(String)
#    rank = column_property(
#        select([EvCoToStat.statementrank]).where(EvCoToStat.id_stat == id)
#    )

class EvCoToStat(Base):
    __tablename__ = 'u_evco2stat'

    id = Column('id', Integer, primary_key=True)
    id_evcoid = Column('id_evcoid', Integer, ForeignKey('u_eventcontentids.id'))
    id_stat = Column('id_stat', Integer, ForeignKey('u_evcostatements.id'))
    id_pathid = Column(Integer, ForeignKey('u_pathids.id'))
    statementrank = Column(Integer)


class EvCoToStream(Base):
    __tablename__ = 'u_evco2stream'

    id = Column('id', Integer, primary_key=True)
    id_evcoid = Column('id_evcoid', Integer, ForeignKey('u_eventcontentids.id'))
    id_streamid = Column('id_streamid', Integer, ForeignKey('u_streamids.id'))




#-------------------- ES Template and elements ------------------
class ESModTemplate(Base):
     # nome della tabella
    __tablename__ = 'u_esmtemplates'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)

class EsmtToRele(Base):
    __tablename__ = 'u_esmt2rele'

    id = Column('id', Integer, primary_key=True)
    id_esmtemplate = Column('id_esmtemplate', Integer, ForeignKey('u_esmtemplates.id'))
    id_release = Column(Integer)

class ESMTempElement(Base):
     # nome della tabella
    __tablename__ = 'u_esmtelements'

    id = Column('id', Integer, primary_key=True)
    id_esmtemplate = Column('id_esmtemplate', Integer, ForeignKey('u_esmtemplates.id'))
    moetype = Column(Integer)
    name = Column(String)
    lvl = Column(Integer)
    order = Column('ord',Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)

#-------------------- ES Module and elements ------------------
class ESModule(Base):
     # nome della tabella
    __tablename__ = 'u_esmodules'

    id = Column('id', Integer, primary_key=True)
    id_template = Column('id_template', Integer, ForeignKey('u_esmtemplates.id'))
    name = Column(String)

class ConfToEsm(Base):
    __tablename__ = 'u_conf2esm'

    id = Column('id', Integer, primary_key=True)
    id_confver = Column('id_confver', Integer, ForeignKey('u_confversions.id'))
    id_esmodule = Column('id_esmodule', Integer, ForeignKey('u_esmodules.id'))
    order = Column('ord',Integer)

class ESMElement(Base):
     # nome della tabella
    __tablename__ = 'u_esmelements'

    id = Column('id', Integer, primary_key=True)
    id_esmodule = Column('id_esmodule', Integer, ForeignKey('u_esmodules.id'))
    moetype = Column(Integer)
    name = Column(String)
    lvl = Column(Integer)
    order = Column('ord',Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)




#-------------------- Output Module elements ------------------
class OumElement(Base):
     # nome della tabella
    __tablename__ = 'u_outmelements'

    id = Column('id', Integer, primary_key=True)
    id_streamid = Column('id_streamid', Integer, ForeignKey('u_streamids.id'))
    moetype = Column(Integer)
    name = Column(String)
    lvl = Column(Integer)
    order = Column('ord',Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)

#------------- Global PSET and Elements ---------------
class Globalpset(Base):
    __tablename__ = 'u_globalpsets'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)
    tracked = Column(Integer)

class Conf2Gpset(Base):
    __tablename__ = 'u_conf2gpset'

    id = Column('id', Integer, primary_key=True)
    id_confver = Column('id_confver', Integer, ForeignKey('u_confversions.id'))
    id_gpset = Column('id_gpset', Integer, ForeignKey('u_globalpsets.id'))
    order = Column('ord',Integer)

class GpsetElement(Base):
    __tablename__ = 'u_gpsetelements'

    id = Column('id', Integer, primary_key=True)
    id_gpset = Column('id_gpset', Integer, ForeignKey('u_globalpsets.id'))
    moetype = Column(Integer)
    name = Column(String)
    lvl = Column(Integer)
    order = Column('ord',Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)

#-------------- ED SOURCE Templates and Elements --------
class EDSourceTemplate(Base):
     # nome della tabella
    __tablename__ = 'u_edstemplates'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)

class EdstToRele(Base):
    __tablename__ = 'u_edst2rele'

    id = Column('id', Integer, primary_key=True)
    id_edstemplate = Column('id_edstemplate', Integer, ForeignKey('u_edstemplates.id'))
    id_release = Column(Integer)

class EDSTempElement(Base):
     # nome della tabella
    __tablename__ = 'u_edstelements'

    id = Column('id', Integer, primary_key=True)
    id_edstemplate = Column('id_edstemplate', Integer, ForeignKey('u_edstemplates.id'))
    moetype = Column(Integer)
    name = Column(String)
    lvl = Column(Integer)
    order = Column('ord',Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)


#------------ ED SOURCE and Elements -----------------
class EDSource(Base):
     # nome della tabella
    __tablename__ = 'u_edsources'

    id = Column('id', Integer, primary_key=True)
    id_template = Column('id_template', Integer, ForeignKey('u_edstemplates.id'))


class ConfToEds(Base):
    __tablename__ = 'u_conf2eds'

    id = Column('id', Integer, primary_key=True)
    id_confver = Column('id_confver', Integer, ForeignKey('u_confversions.id'))
    id_edsource = Column('id_edsource', Integer, ForeignKey('u_edsources.id'))
    order = Column('ord',Integer)

class EDSElement(Base):
     # nome della tabella
    __tablename__ = 'u_edselements'

    id = Column('id', Integer, primary_key=True)
    id_edsource = Column('id_edsource', Integer, ForeignKey('u_edsources.id'))
    moetype = Column(Integer)
    name = Column(String)
    lvl = Column(Integer)
    order = Column('ord',Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)

#-------------- ES SOURCE Templates and Elements --------
class ESSourceTemplate(Base):
     # nome della tabella
    __tablename__ = 'u_esstemplates'

    id = Column('id', Integer, primary_key=True)
    name = Column(String)

class EsstToRele(Base):
    __tablename__ = 'u_esst2rele'

    id = Column('id', Integer, primary_key=True)
    id_esstemplate = Column('id_esstemplate', Integer, ForeignKey('u_esstemplates.id'))
    id_release = Column(Integer)

class ESSTempElement(Base):
     # nome della tabella
    __tablename__ = 'u_esstelements'

    id = Column('id', Integer, primary_key=True)
    id_esstemplate = Column('id_esstemplate', Integer, ForeignKey('u_esstemplates.id'))
    moetype = Column(Integer)
    name = Column(String)
    lvl = Column(Integer)
    order = Column('ord',Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)


#------------ ES SOURCE and Elements -----------------
class ESSource(Base):
     # nome della tabella
    __tablename__ = 'u_essources'

    id = Column('id', Integer, primary_key=True)
    id_template = Column('id_template', Integer, ForeignKey('u_esstemplates.id'))
    name = Column(String)

class ConfToEss(Base):
    __tablename__ = 'u_conf2ess'

    id = Column('id', Integer, primary_key=True)
    id_confver = Column('id_confver', Integer, ForeignKey('u_confversions.id'))
    id_essource = Column('id_essource', Integer, ForeignKey('u_essources.id'))
    order = Column('ord',Integer)

class ESSElement(Base):
     # nome della tabella
    __tablename__ = 'u_esselements'

    id = Column('id', Integer, primary_key=True)
    id_essource = Column('id_essource', Integer, ForeignKey('u_essources.id'))
    moetype = Column(Integer)
    name = Column(String)
    lvl = Column(Integer)
    order = Column('ord',Integer)
    paramtype = Column(String)
    value = Column(String)
    valuelob = Column(CLOB)
    tracked = Column(Integer)
