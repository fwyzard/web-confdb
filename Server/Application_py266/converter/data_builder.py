# File data_builder.py Description:
# 
# Class: DataBuilder

from confdb_queries.confdb_queries import ConfDbQueries
from item_wrappers.FolderItem import *
from item_wrappers.ModuleDetails import *
from item_wrappers.Pathitem import *
from item_wrappers.Parameter import *
from item_wrappers.item_wrappers import *
from schemas.responseSchemas import *
from responses.responses import *
from marshmallow import Schema, fields, pprint
#from ordereddict import OrderedDict
from marshmallow.ordereddict import OrderedDict
from exposed.exposed import *
from utils import * 
import string
import re
from multiprocessing import Process, Pipe
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

class DataBuilder(object):

    queries = ConfDbQueries()
    params_builder = ParamsBuilder()

    global_datasets = None
    global_paths = None
    global_endPaths = None
    global_paths_str = None
    global_endpaths_str = None

    def getGlobalPsets(self, ver_id, db, log):
        queries = self.queries
        result = ""

        global_psets = None

        try:
            global_psets = queries.getConfGPsets(ver_id, db, log)
        except Exception as e:
            msg = 'ERROR: Query getConfGPsets Error: ' + e.args[0]
            log.error(msg)
            return result

        template_params = None

        for gpset in global_psets:
            result = result + "process." + gpset.name + ' = cms.PSet(\n'

            try:
                template_params = self.params_builder.gpsetParamsBuilder(gpset.id, queries, db,log)
            except Exception as e:
                msg = 'ERROR: Query gpsetParamsBuilder Error: ' + e.args[0]
                log.error(msg)
                return result

            new_result = self.createParameterString(template_params)
            if new_result == "":
                result = result[:-2] + " )\n"
            else:
                result = result + new_result

        if result == "":
            return result
        else:
            return result + "\n"

    def getStreams(self, ver_id, db):

        result = ""
        global global_datasets

        streams = None
        global_datasets = None
        relations = None

        try:
            streams = self.queries.getConfStreams(ver_id,db)
            global_datasets = self.queries.getConfDatasets(ver_id,db)
            relations = self.queries.getConfStrDatRels(ver_id,db)
        except Exception as e:
            msg = 'ERROR: Steams Query Error: ' + e.args[0]
            log.error(msg)
            return result

        relations_dict = dict((x.id_datasetid, x.id_streamid) for x in relations)

        streams.sort(key=lambda par: par.name)
        global_datasets.sort(key=lambda par: par.name)

        for stream in streams:
            result = result + self.getTab(2) + stream.name + " = cms.vstring( "
            new_result = ""
            for dataset in global_datasets: 
                if(stream.id == relations_dict.get(dataset.id)):
                    new_result = new_result + "'" + dataset.name + "'" + ",\n" + self.getTab(4)

            if new_result != "":
                result = result + new_result[:-6] + " ),\n"
            else:
                result = result + " ),\n"

        result = result[:-2] + "\n)\n"

        return result + "\n"

    def getDatasetsPaths(self, ver_id, db):

        result = ""

        paths = None

        for dataset in global_datasets:
            result = result + self.getTab(2) + dataset.name + " = cms.vstring( "

            try:
                paths = self.queries.getDatasetPathids(ver_id, dataset.id, db)
            except Exception as e:
                msg = 'ERROR: Query getDatasetPathids Error: ' + e.args[0]
                log.error(msg)
                return result
            
            paths.sort(key=lambda par: par.name)
            if len(paths) == 0:
                result = result + "\n" + self.getTab(4)
            elif len(paths) < 255:
                for path in paths: 
                    result = result + "'" + path.name + "'" + ",\n" + self.getTab(4)
            else:
                result = result + "*( "
                for path in paths: 
                    result = result + "'" + path.name + "'" + ",\n" + self.getTab(4)
                result = result[:-6] + "),\n" + self.getTab(4)
            result = result[:-6] + " ),\n" 
        result = result[:-2] + "\n)\n"
        
        return result + "\n"

    def getEDSources(self, ver_id, id_rel, db = None):

        result = ""
        queries = self.queries

        modules = None
        templates = None
        conf2eds = None

        try:
            modules = queries.getConfEDSource(ver_id,db)
            templates = queries.getEDSTemplates(id_rel,db)
            conf2eds = queries.getConfToEDSRel(ver_id,db) 
        except Exception as e:
            msg = 'ERROR: EDSources Query Error: ' + e.args[0]
            log.error(msg)
            return result  
            
        templates_dict = dict((x.id, x) for x in templates)
        conf2eds_dict = dict((x.id_edsource, x.order) for x in conf2eds)
        
        edsources = []
        
        for m in modules:
            if (templates_dict.has_key(m.id_template) and conf2eds_dict.has_key(m.id)):
                temp = templates_dict.get(m.id_template)
                c2e = conf2eds_dict.get(m.id)
                eds = EDSource(m.id, m.id_template, temp.name, c2e)
                eds.gid = m.id  
            if (eds != None):
                edsources.append(eds)            
        
        edsources.sort(key=lambda par: par.order)

        template = None
        tempelements = None

        for edsource in edsources:
            result = result + 'process.source = cms.Source( "'  + edsource.name + '",\n'

            try:
                template = queries.getEDSTemplateByEds(edsource.id,db) 
                tempelements = queries.getEDSTemplateParams(template.id,db)
            except Exception as e:
                msg = 'ERROR: EDSources Query Error: ' + e.args[0]
                log.error(msg)
                return ""              
            for tempel in tempelements:
                tracked, val = self.buildParamValue(tempel, 4, 6)
                result = result + self.getTab(4) + tempel.name + " = cms." + tracked + tempel.paramtype + val
            result = result[:-2] + "\n)\n\n" 

        return result

    def getESSource(self, ver_id, id_rel, db = None, log=None):

        queries = self.queries
        result = ""

        modules = None
        templates = None
        conf2ess = None

        try:
            modules = queries.getConfESSource(ver_id,db)
            templates = queries.getESSTemplates(id_rel,db)
            conf2ess = queries.getConfToESSRel(ver_id,db) 
        except Exception as e:
            msg = 'ERROR: ESSource Query Error: ' + e.args[0]
            log.error(msg)
            return result    
        
        templates_dict = dict((x.id, x) for x in templates)
        modules_dict = dict((x.id, x) for x in modules)
        conf2ess_dict = dict((x.id_essource, x.order) for x in conf2ess)

        for module in modules:
            if (templates_dict.has_key(module.id_template) and conf2ess_dict.has_key(module.id)):
                template = templates_dict.get(module.id_template)
                result = result + "process." + module.name + ' = cms.ESSource( "' + template.name + '",\n'
                template_params = self.params_builder.esSourceParamsBuilder(module.id, self.queries, db, log) 
                new_result = self.createParameterString(template_params)
                if new_result == "":
                    result = result[:-2] + " )\n"
                else:
                    result = result + new_result

        return result + "\n"

    def getESModules(self, ver_id, id_rel, db = None, log=None):

        queries = self.queries
        result = ""

        modules = None
        templates = None
        conf2esm = None

        try:
            modules = queries.getConfESModules(ver_id,db)
            templates = queries.getESMTemplates(id_rel,db)
            conf2esm = queries.getConfToESMRel(ver_id,db)   
        except Exception as e:
            msg = 'ERROR: ESModules Query Error: ' + e.args[0]
            log.error(msg)
            return result  
            
        templates_dict = dict((x.id, x) for x in templates)
        modules_dict = dict((x.id, x) for x in modules)
        conf2esm_dict = dict((x.id_esmodule, x.order) for x in conf2esm)
        
        for module in modules:
            if (templates_dict.has_key(module.id_template) and conf2esm_dict.has_key(module.id)):
                template = templates_dict.get(module.id_template)
                result = result + "process." + module.name + ' = cms.ESProducer( "' + template.name + '",\n'
                template_params = self.params_builder.esModuleParamsBuilder(module.id, self.queries, db, log) 
                new_result = self.createParameterString(template_params)
                if new_result == "":
                    result = result[:-2] + " )\n"
                else:
                    result = result + new_result

        return result + "\n"

    def getServices(self, ver_id, id_rel, db = None, log=None):
        
        queries = self.queries
        result = ""

        services = None
        templates = None

        try:
            services = queries.getConfServices(ver_id,db)
            templates = queries.getRelSrvTemplates(id_rel,db)
        except Exception as e:
            msg = 'ERROR: Services Query Error: ' + e.args[0]
            log.error(msg)
            return result  

        templates_dict = dict((x.id, x) for x in templates)

        for service in services:
            if (templates_dict.has_key(service.id_template)):
                template = templates_dict.get(service.id_template)
                result = result + "process." + template.name + ' = cms.Service( "' + template.name + '",\n'
                template_params = self.params_builder.serviceParamsBuilder(service.id, self.queries, db, log) 
                new_result = self.createParameterString(template_params)
                if new_result == "":
                    result = result[:-2] + " )\n"
                else:
                    result = result + new_result

        return result + "\n"

    def getModules(self, ver_id = -2, id_rel = -2, db = None):  

        import cherrypy 
        log = cherrypy.log

        queries = self.queries
        result = ""

        modules = None
        module_parameters = None
        module_template = None

        try:
            modules = self.queries.getModules(ver_id, db, log)
            module_parameters = self.queries.getModuleElements(ver_id, db, log)
            module_template = self.queries.getModuleTemplateParameters(id_rel, db, log)
        except Exception as e:
            msg = 'ERROR: Modules Query Error: ' + e.args[0]
            log.error(msg)
            return result  

        module_para_dict = dict()
        module_temp_dict = dict()

        for param in module_parameters:
            if param.id_pae not in module_para_dict:
                module_para_dict[param.id_pae] = []
                module_para_dict[param.id_pae].append(param)
            else:
                module_para_dict[param.id_pae].append(param)

        for template in module_template:
            if template.id_modtemp not in module_temp_dict:
                module_temp_dict[template.id_modtemp] = []
                module_temp_dict[template.id_modtemp].append(template)
            else:
                module_temp_dict[template.id_modtemp].append(template)

        modules.sort(key=lambda par: par.name)

        for module in modules:
            result = result + "process." + module.name + " = cms." + module.mtype + '( "' + module.temp_name + '",\n' 
            template = module_temp_dict.get(module.id_templ) 
            parameters = module_para_dict.get(module.id)
            if parameters is not None:
                parameters.sort(key=lambda par: par.id_moe)
            if template is not None:
                template.sort(key=lambda par: par.id)
            template_params = self.moduleParamsBuilder(template, parameters, log)

            new_result = self.createParameterString(template_params)

            if new_result == "":
                result = result[:-2] + " )\n"
            else:
                result = result + new_result

        return result + "\n"

    def getOutputModules(self, ver_id, id_rel, db = None, log=None):

        queries = self.queries
        global global_endPaths, global_endpaths_str

        result = ""
        global_endpaths_str = ""

        global_endPaths = None

        try:
            global_endPaths = queries.getEndPaths(ver_id,db, log)
        except Exception as e:
            msg = 'ERROR: Query getEndPaths Error: ' + e.args[0]
            log.error(msg)
            return result  
        
        for path in global_endPaths:
            global_endpaths_str = global_endpaths_str + "process." + path.name + ", " 
            outmodule = queries.getOumStreamid(path.id, db, log)
            if outmodule == None:
                continue
            stream = queries.getStreamid(outmodule.id_streamid, db, log)
            result = result + "process.hltOutput"+ stream.name + ' = cms.OutputModule( "ShmStreamConsumer",\n'
            template_params = self.params_builder.outputModuleParamsBuilder(stream.id,queries,db,log)
            new_result = self.createParameterString(template_params)
            if new_result == "":
                result = result[:-2] + " )\n"
            else:
                result = result + new_result
                
        return result + "\n"

    def getSequences(self, ver_id, id_rel, db = None, log=None):

        queries = self.queries
        result = ""

        seqsMap = SequencesDict()
        idgen = Counter()
        modsMap = ModulesDict()

        global global_paths, global_paths_str

        global_paths = None

        try:
            global_paths = queries.getPaths(ver_id, db, log)
        except Exception as e:
            msg = 'ERROR: Query getPaths Error: ' + e.args[0]
            log.error(msg)
            return result  

        global_paths_str = ""

        children = []
        written_sequences = []

        elements = None
        seq_items = None

        for path in global_paths:
            global_paths_str = global_paths_str + "process." + path.name + ", "

            try:
                elements = queries.getCompletePathSequences(path.id, ver_id, db, log)
                seq_items = queries.getCompletePathSequencesItems(path.id, ver_id, db, log)
            except Exception as e:
                msg = 'ERROR: Sequences Query Error: ' + e.args[0]
                log.error(msg)
                return result  

            seq_elems_dict = dict((x.id, x) for x in elements)
            
            counter = 0

            while counter < len(seq_items):
                elem = seq_elems_dict[seq_items[counter].id_pae]
                item = Pathitem(seq_items[counter].id_pae, elem.name, seq_items[counter].id_pathid, elem.paetype, seq_items[counter].id_parent, seq_items[counter].lvl, seq_items[counter].order)
                counter = counter + 1
                if(item.paetype == 2 and item.name not in written_sequences):
                    new_result, counter, new_children, written_sequences = self.getSequenceChildren(counter, written_sequences, seq_items, seq_elems_dict, item.lvl+1)
                    result = result + new_result + "process." + item.name + " = cms.Sequence( "
                    for child in new_children:
                        result = result + "process." + child + " + " 
                    result = result[:-2] + ")\n"
                    written_sequences.append(item.name)
            
        return result + "\n"

    def getPaths(self, ver_id, id_rel, db = None, log=None):
        queries = self.queries
        modsMap = ModulesDict()
        seqsMap = SequencesDict()
        idgen = Counter()
        result = ""

        elements = None
        items = None
        lista = None
        lvlzelems = None

        for path in global_paths:
            result = result + "process." + path.name + " = " + "cms.Path( "

            try:
                elements = queries.getCompletePathSequences(path.id, ver_id, db, log)
                items = queries.getCompletePathSequencesItems(path.id, ver_id, db, log)
            except Exception as e:
                msg = 'ERROR: Paths Query Error: ' + e.args[0]
                log.error(msg)
                return result  

            elements_dict = dict((x.id, x) for x in elements)
        
            seq = {}
            lvlZeroSeq_Dict = {}
        
            for p in items:
                elem = elements_dict[p.id_pae]
                item = Pathitem(p.id_pae, elem.name, p.id_pathid, elem.paetype, p.id_parent, p.lvl, p.order, p.operator)

                if (item.paetype == 2):
                    item.gid = seqsMap.put(idgen,elem,p.id_pathid,p.order,p.lvl)
                    seq[item.gid]=item  
                    if (item.lvl == 0): 
                        iid = item.id   
                        lvlZeroSeq_Dict[item.gid] = iid

            try:
                lista = queries.getLevelZeroPathItems(path.id, ver_id, db, log)
                lvlzelems = queries.getLevelZeroPaelements(path.id, ver_id, db, log)

            except Exception as e:
                msg = 'ERROR: Paths Query Error: ' + e.args[0]
                log.error(msg)
                return result              

            lvlzelems_dict = dict((x.id, x) for x in lvlzelems)
            pats = []
                
            for l in lista:
                elem = lvlzelems_dict[l.id_pae]
                item = Pathitem(l.id_pae ,elem.name, l.id_pathid, elem.paetype, l.id_parent, l.lvl, l.order, l.operator)
                item.gid = modsMap.putItem(idgen,elem,l.id_pathid,l.order,l.lvl)
                pats.insert(item.order,item)
            
            lvlZeroSeq_Dict_keys = lvlZeroSeq_Dict.keys()
            for lzseq in lvlZeroSeq_Dict_keys:
                lzsequence = seq[lzseq] 
                pats.insert(lzsequence.order, lzsequence)

            for pat in pats:
                if pat.operator == 0: 
                    result = result + "process." + pat.name + " + "
                elif pat.operator == 2:
                    result = result + "cms.ignore(process." + pat.name + ")" + " + "
                elif pat.operator == 1:
                    result = result + "~process." + pat.name + " + "
            
            result = result[:-2] + ")\n"

        return result + "\n"

    def getEndPaths(self, ver_id, id_rel, db = None, log=None):
        queries = self.queries
        modsMap = ModulesDict()
        seqsMap = SequencesDict()
        oumodsMap = OutputModulesDict()
        idgen = Counter()
        result = ""

        lvlZeroSeq_Dict = {}

        for path in global_endPaths:
            result = result + "process." + path.name + " = " + "cms.EndPath( "

            elements = queries.getCompletePathSequences(path.id, ver_id, db, log)
            if(len(elements)!=0):
                items = queries.getCompletePathSequencesItems(path.id, ver_id, db, log)

                elements_dict = dict((x.id, x) for x in elements)
            
                seq = {} 
            
                for p in items:
                    elem = elements_dict[p.id_pae]
                    item = Pathitem(p.id_pae, elem.name, p.id_pathid, elem.paetype, p.id_parent, p.lvl, p.order)

                    if (item.paetype == 2):
                        item.gid = seqsMap.put(idgen,elem,p.id_pathid,p.order,p.lvl)
                        seq[item.gid]=item  
                        if (item.lvl == 0): 
                            iid = item.id   
                            lvlZeroSeq_Dict[item.gid] = iid 

            lista = queries.getLevelZeroPathItems(path.id, ver_id, db, log)
            lvlzelems = queries.getLevelZeroPaelements(path.id, ver_id, db, log)

            lvlzelems_dict = dict((x.id, x) for x in lvlzelems)
            pats = []
                
            for l in lista:
                elem = lvlzelems_dict[l.id_pae]
                item = Pathitem(l.id_pae ,elem.name, l.id_pathid, elem.paetype, l.id_parent, l.lvl, l.order)
                item.gid = modsMap.putItem(idgen,elem,l.id_pathid,l.order,l.lvl)
                pats.insert(item.order,item)
            
            lvlZeroSeq_Dict_keys = lvlZeroSeq_Dict.keys()
            for lzseq in lvlZeroSeq_Dict_keys:
                lzsequence = seq[lzseq] 
                pats.insert(lzsequence.order, lzsequence)  

            outmodule = queries.getOumStreamid(path.id, db, log)
            if (outmodule != None):
                stream = queries.getStreamid(outmodule.id_streamid, db, log)
            
                oumName = "hltOutput"+stream.name
                oum = Pathitem(outmodule.id_streamid, oumName, outmodule.id_pathid, 3, -1, 0, outmodule.order)

                oum.gid = oumodsMap.put(idgen,oum)  

                pats.insert(oum.order, oum) 

            for pat in pats:
                result = result + "process." + pat.name + " + "
            
            result = result[:-2] + ")\n"

        return result + "\n"

    def getSchedule(self):

        if global_paths_str + global_endpaths_str == "":
            return "process.HLTSchedule = cms.Schedule( )"

        else:
            result = "process.HLTSchedule = cms.Schedule( *(" + global_paths_str + global_endpaths_str
            return result[:-2] + " ))"

    ## -- Helper Functions -- ##  

    def moduleParamsBuilder(self, template, parameters, log):
        params = []

        if template == None:
            template = {}
        
        #Build template parameters
        temp_pset = {}
        temp_vpset = {}
        temp_parents = {}
        temp_parents[0]=-1
        
        #Build all the vpsets/psets 
        
        temp_params = []
        temp_params_dict = {}
        temp_params_name_dict = {}
        
        for p in template:
            parent = temp_parents.get(p.lvl)
            clvl = p.lvl+1
            parValue = None
            if (p.valuelob == None or p.valuelob == "") and (p.moetype == 1):
                parValue = p.value
                
            else:
                parValue = p.valuelob
        
            item = Parameter(p.id, p.name, parValue, p.moetype, p.paramtype, parent, p.lvl, p.order, p.tracked)
            item.default = True
            
            temp_params_name_dict[item.name] = item
            
            # It is a vpset
            if (item.moetype == 3):
                temp_parents[clvl] = p.id
                item.expanded = False
                temp_vpset[item.id] = item
        
            # It is a pset
            elif (item.moetype == 2):
                temp_parents[clvl] = p.id
                item.expanded = False
                temp_pset[item.id]=item
                if (temp_vpset.has_key(item.id_parent)):                
                    temp_vpset[item.id_parent].children.insert(item.order, item)

            # It is a param
            else:
                if(item.lvl == 0):
                    temp_params.insert(item.order,item)
                    temp_params.sort(key=lambda par: par.order)
                else:
                    tps = temp_pset[item.id_parent].children
                    tps.insert(item.order, item)
                    tps.sort(key=lambda par: par.order)
           
        #complete Pset construction
        temp_psets = temp_pset.values() 
        for s in temp_psets:
            if (s.lvl != 0):
                if (temp_pset.has_key(s.id_parent)):
                    tps = temp_pset[s.id_parent].children
                    tps.insert(s.order, s)
                    tps.sort(key=lambda par: par.order)

        #merge the psets created
        temp_psKeys = temp_pset.keys()               
        
        for ss in temp_psKeys:
            s = temp_pset.get(ss)
            if(s.lvl==0):
                temp_params.insert(s.order, s)
        
        #merge the vpsets created
        temp_vpsKeys = temp_vpset.keys()               
        
        for ss in temp_vpsKeys:
            s = temp_vpset.get(ss)
            if(s.lvl==0):
                temp_params.insert(s.order, s)
        
        temp_params_dict = dict((x.id, x) for x in temp_params)
        
        #------------------------------------------------------------------------------------------------------------
        #Retreive all the parameters of the module

        pset = {}
        vpset = {}
        parents = {}
        
        parents[0]=-1
        
        not_in = []
        params = []
        pset_name_dict = {}
        vpset_name_dict = {}
        params_mod_name_dict = {}

        if parameters != None:
        
            for param in parameters:
                parent = parents.get(param.lvl)
                clvl = param.lvl+1
                parValue = None
                if (param.valuelob == None or param.valuelob == "") and (param.moetype == 1):
                    parValue = param.value
                    
                else:
                    parValue = param.valuelob
                
                item = Parameter(param.id_moe, param.name, parValue, param.moetype, param.paramtype, parent, param.lvl, param.ord, param.tracked)
                 
                params_mod_name_dict[item.name]=item
                #Set default
                if (temp_params_name_dict.has_key(item.name)):
                    if temp_params_name_dict.get(item.name).value == item.value:
                        item.default = True
                
                # It is a vpset
                if (item.moetype == 3):
                    parents[clvl] = param.id_moe
                    item.expanded = False
                    vpset[item.id] = item
                    vpset_name_dict[item.name]=item
            
                # It is a pset
                elif (item.moetype == 2):
                    parents[clvl] = param.id_moe
                    item.expanded = False
                    pset[item.id]=item
                    pset_name_dict[item.name]=item
                    if (vpset.has_key(item.id_parent)):                
                        vpset[item.id_parent].children.insert(item.order, item)

                # It is a param
                else:
                    if(item.lvl == 0):
                        params.insert(item.order,item)
                        params.sort(key=lambda par: par.order)
                    else:
                        tps = pset[item.id_parent].children
                        tps.insert(item.order, item)
                        tps.sort(key=lambda par: par.order)
        
        #Check ok temp params
        names = temp_params_name_dict.keys()
        for pn in names:
            if (not(params_mod_name_dict.has_key(pn))): 
                not_in.append(temp_params_name_dict.get(pn))
        
        
        #Fill the remaining params from Template
        if (len(not_in) > 0):
            for n in not_in:
                if (n.lvl != 0):
                    if (n.id_parent in temp_vpset.keys()):
                        if(vpset_name_dict.has_key(temp_vpset.get(n.id_parent).name)):
                            vpset_name_dict.get(temp_vpset.get(n.id_parent).name).children.insert(n.order,n)

                    if (n.id_parent in temp_pset.keys()):
                        if(pset_name_dict.has_key(temp_pset.get(n.id_parent).name)):
                            pset_name_dict.get(temp_pset.get(n.id_parent).name).children.insert(n.order,n)
                    
                    else:
                        log.error('ERROR: Module Param Error Key')
        
        #complete Pset construction
        psets = pset.values() 
        for s in psets:
            if (s.lvl != 0):
                if (pset.has_key(s.id_parent)):
                    tps = pset[s.id_parent].children
                    tps.insert(s.order, s)
                    tps.sort(key=lambda par: par.order)

        #merge the psets created
        psKeys = pset.keys() #pset.viewkeys()               
        
        for ss in psKeys:
            s = pset.get(ss)
            if(s.lvl==0):
                params.insert(s.order, s)
        
        #merge the vpsets created
        vpsKeys = vpset.keys()               
        
        for ss in vpsKeys:
            s = vpset.get(ss)
            if(s.lvl==0):
                params.insert(s.order, s)
        
        #Merge the remaining template params
        for p in not_in:
            if(p.lvl==0):
                tp = temp_params_dict.get(p.id)
                params.insert(tp.order, p)
                
        params.sort(key=lambda par: par.order)
        
        return params

    def createParameterString(self, template_params):
        result = ""
        for template_param in template_params:
            tracked = '' if template_param.tracked else 'untracked.'
            if template_param.paramtype == "VPSet":
                result = result + self.getTab(4) + template_param.name + " = cms." + tracked
                new_result = self.buildVPSetChildren(template_param, 6, 8)
                if len(template_param.children) < 255:
                    result = result + "VPSet(\n"
                    if new_result == "\n":
                        result =  result + self.getTab(4) + "),\n"
                    else:
                        result = result + new_result + self.getTab(4) + "),\n"
                else:
                    result = result +"VPSet(  *(\n" + new_result + self.getTab(4) + ") ),\n"

            elif template_param.paramtype == "PSet":
                new_result = ""
                new_result = self.buildPsetChildren(template_param, 6, 8)

                if len(template_param.children) < 255:
                    result = result + self.getTab(4) + template_param.name + " = cms." + tracked + "PSet(\n"
                    if new_result == "\n":
                        result = result[:-1] + "  ),\n"
                    else:
                        result = result = result + new_result + self.getTab(4) + "),\n"
                else:
                    result = result + self.getTab(4) + template_param.name + " = cms." + tracked + "PSet(  *(\n"
                    result = result + new_result + self.getTab(4) + ") ),\n"
            
            else:
                tracked, val = self.buildParamValue(template_param, 4, 6)
                result = result + self.getTab(4) + template_param.name + " = cms." + tracked + template_param.paramtype + val

        if result == "":
            return result  
        else:
            return result[:-2] + "\n)\n"

    def buildVPSetChildren(self, template_param, pset_tab, param_tab):
        result = ""
        psets = template_param.children

        for pset in psets:
            if pset.paramtype == "VPSet":
                result = result + self.getTab(pset_tab) + pset.name + " = cms." + tracked
                new_result = self.buildVPSetChildren(template_param, pset_tab+2, param_tab+2)
                if len(pset.children) < 255:
                    result = result + "VPSet(\n"
                    if new_result == "\n":
                        result =  result + self.getTab(pset_tab) + "),\n"
                    else:
                        result = result + new_result + self.getTab(pset_tab) + "),\n"
                else:
                    result = result +"VPSet(  *(\n" + new_result + self.getTab(pset_tab) + ") ),\n"
            else:
                new_result = self.buildPsetChildren(pset,pset_tab+2,param_tab+2)
                if len(pset.children) < 255:
                    pset_name = "cms.PSet(\n" if (pset.name == None) else pset.name + " = cms.PSet(\n"
                    result = result + self.getTab(pset_tab) + pset_name 
                    if new_result == "\n":
                        result = result[:-1] + "  ),\n"
                    else:
                        result = result + new_result + self.getTab(pset_tab) + "),\n"
                else:
                    pset_name = "cms.PSet(  *(\n" if (pset.name == None) else pset.name + " = cms.PSet(  *(\n"
                    result = result + self.getTab(pset_tab) + pset_name 
                    result = result + new_result + self.getTab(pset_tab) + "),\n"

        result = result[:-2] + "\n"
        return result

    def buildPsetChildren(self, template_params, pset_tab, param_tab):
        result = ""
        params = template_params.children

        for param in params:
            if param.paramtype == "VPSet":
                result = result + self.getTab(pset_tab) + param.name + " = cms." + tracked
                new_result = self.buildVPSetChildren(template_param, pset_tab+2, param_tab+2)
                if len(param.children) < 255:
                    result = result + "VPSet(\n"
                    if new_result == "\n":
                        result =  result + self.getTab(pset_tab) + "),\n"
                    else:
                        result = result + new_result + self.getTab(pset_tab) + "),\n"
                else:
                    result = result +"VPSet(  *(\n" + new_result + self.getTab(pset_tab) + ") ),\n"
            elif param.paramtype == "PSet":
                new_result = self.buildPsetChildren(param, pset_tab+2, param_tab+2)
                if len(param.children) < 255:
                    pset_name = "cms.PSet(\n" if (param.name == None) else param.name + " = cms.PSet(\n"
                    result = result + self.getTab(pset_tab) + pset_name 
                    if new_result == "\n":
                        result = result[:-1] + "  ),\n"
                    else:
                        result = result + new_result + self.getTab(pset_tab) + "),\n"
                else:
                    pset_name = "cms.PSet(  *(\n" if (param.name == None) else param.name + " = cms.PSet(  *(\n"
                    result = result + self.getTab(pset_tab) + pset_name 
                    result = result + new_result + self.getTab(pset_tab) + "),\n"
            else:
                tracked, val = self.buildParamValue(param, pset_tab, param_tab)
                result = result + self.getTab(pset_tab) + param.name + " = cms." + tracked + param.paramtype + val
        result = result[:-2] + "\n"
        return result

    def modifyTemplateParameters(self, templateparams, params):
        data = []
        counter = 0
        for templateparam in templateparams:
            data.append(templateparam)
            for param in params:
                if templateparam.name == param.name:
                    data[counter] = param
            counter = counter + 1
        return data

    def checkIfInTemplate(self, templateparams, params):
        flag = False
        for param in params:
            for templateparam in templateparams:
                if param.name == templateparam.name:
                    flag = True
                    break
                else: 
                    flag = False
            if flag == False:
                return False
        return True

    def buildParamValue(self, template_params, pset_tab, param_tab):

        tracked = '' if template_params.tracked else 'untracked.'
        val = ""

        if (template_params.paramtype == "vstring"):
            if template_params.value == None or template_params.value == "{}" or template_params.value == "{ }":
                val = '( "" ),\n'
            if template_params.value != None:
                elems = template_params.value[1:-1].split(",")
                value = ""
                for elem in elems:
                    value = value + elem + ",\n" + self.getTab(param_tab) if '"' in elem else value + '"' + elem + '"' + ",\n" + self.getTab(param_tab) 
                if len(elems) < 255:
                    val = val + '(' + value[:- (len(self.getTab(param_tab)) + 2)] + '),\n'
                else:
                    val = val + '( *(' + value[:- (len(self.getTab(param_tab)) + 2)] + ') ),\n'

        elif (template_params.paramtype == "vint32"):
            if template_params.value == None:
                val = '( ' + str(template_params.value) + ' ),\n'
            else:
                if len(template_params.value[1:-1].split(",")) < 255:
                    val = '(' + template_params.value[1:-1] + '),\n'
                else:
                    val = '( *(' + template_params.value[1:-1] + ') ),\n'

        elif (template_params.paramtype == "vuint32"):
            if template_params.value == None:
                val = '( ' + str(template_params.value) + ' ),\n'
            else:
                if len(template_params.value[1:-1].split(",")) < 255:
                    val = '(' + template_params.value[1:-1] + '),\n' 
                else:
                    val = '( *(' + template_params.value[1:-1] + ') ),\n'

        elif (template_params.paramtype == "vdouble"):
            if len(template_params.value[1:-1].split(",")) < 255:
                val = '( ' + template_params.value[1:-1] + ' ),\n'
            else:
                val = '( *(' + template_params.value[1:-1] + ') ),\n'

        elif(template_params.paramtype == "VInputTag"):
            val = "( '" + template_params.value[2:-2] + "' ),\n" if template_params.value[2:-2] != '' else "(  ),\n"

        elif (template_params.paramtype == "string"):
            if template_params.value == None or template_params.value == "" or template_params.value == "none" or template_params.value == "None":
                val = '( "" ),\n'
            else:
                val = '( "' + template_params.value.replace("'","").replace('"',"") + '" ),\n'

        elif (template_params.paramtype == "FileInPath"):
            if template_params.value == None or template_params.value == "" or template_params.value == "none" or template_params.value == "None":
                val = '( "" ),\n'
            else:
                val = '( "' + template_params.value.replace("'","").replace('"',"") + '" ),\n'

        elif (template_params.paramtype == "bool"):
            if template_params.value == None:
                val = '( ' + str(template_params.value) + ' ),\n'
            else:
                val = '( True ),\n' if (int(template_params.value)) else '( False ),\n' 

        elif (template_params.paramtype == "uint64"):
            if template_params.value == None:
                val = '( ' + str(template_params.value) + ' ),\n'
            else:
                val = '( ' + hex(int(template_params.value)).replace("-","") + ' ),\n'

        elif (template_params.paramtype == "double"):
            if template_params.value == None:
                val = '( ' + str(template_params.value) + ' ),\n'
            else:
                val = '( ' + str(float(template_params.value)) + ' ),\n'

        elif(template_params.paramtype == "InputTag"):
            if template_params.value == None:
                val = '( ' + str(template_params.value) + ' ),\n'
            else: 
                if template_params.value == '""':
                    val = '( ' + template_params.value + ' ),\n'
                else:
                    val = '( '
                    for elem in template_params.value.split(":"):
                        val = val + "'" + elem + "', "
                    val = val[:-2] + ' ),\n'

        else:
            if (template_params.value != None):
                val = '( ' + template_params.value + ' ),\n'
            else:
                val = '( ' + str(template_params.value) + ' ),\n'

        return tracked, val

    def getSequenceChildren(self, counter, written_sequences, seq_items, seq_elems_dict, level):
        children = []
        result = ""
        while(counter < len(seq_items) and seq_items[counter].lvl == level):
            elem = seq_elems_dict[seq_items[counter].id_pae]
            item = Pathitem(seq_items[counter].id_pae, elem.name, seq_items[counter].id_pathid, elem.paetype, seq_items[counter].id_parent, seq_items[counter].lvl, seq_items[counter].order)
            children.append(item.name)
            counter = counter + 1
            if (item.paetype == 2 and item.name not in written_sequences):
                new_result, counter, new_children, written_sequences = self.getSequenceChildren(counter, written_sequences, seq_items, seq_elems_dict, item.lvl+1)
                result = result + new_result + "process." + item.name + " = cms.Sequence( "
                for child in new_children:
                    result = result + "process." + child + " + " 
                result = result[:-2] + ")\n"
                written_sequences.append(item.name)

        return result, counter, children, written_sequences

    def getRequestedVersion(self, ver=-2, cnf=-2, db = None):    
        
        ver_id = -1
        version = None
        queries = self.queries
        
        if((ver == -2) and (cnf == -2)):
            print "VER CNF ERROR"

        elif(cnf != -2 and cnf != -1):
            configs = queries.getConfVersions(cnf, db)
            configs.sort(key=lambda par: par.version, reverse=True)
            ver_id = configs[0].id
            version = queries.getVersion(ver_id,db)

        elif(ver != -2):
            ver_id = ver
            version = queries.getVersion(ver,db)
            
        return version

    def getTab(self, n):
        return "\t".expandtabs(n)