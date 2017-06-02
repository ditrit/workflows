# coding: utf8

import os
import sys
from tosca import yamlparser

ALLOWEDTOSCAVERSIONS = [ 'tosca_simple_yaml_1_0' ]

class ToscaException(Exception):
  pass

class ToscaObject(object):
  
  def __init__(self, yamldef, toscaversion):
    self.toscaversion = toscaversion
    self.defkeys_list = self.grammar[toscaversion]
    results = [ self.__valid_keys(yamldef, defkeys) for defkeys in self.defkeys_list ] 
    valid = any( [ ok for (ok, _ ) in results ])
    if not valid:
       raise ToscaException("\n OU BIEN \n".join( [ msg for ( _ , msg ) in results ] ))
    else: 
       self.yamldef = yamldef

  def __valid_keys(self, yamldef, defkeys):
    msg = []
    if isinstance(yamldef, dict):
      input_keys = yamldef.keys()
      valid_keys = defkeys.keys()

      # Vérifier que la définition ne comprend que des clefs valides
      if not set(input_keys).issubset(set(valid_keys)):
        msg.append("Les clefs {keys!s} ne sont pas valides pour la définition d'un {toscatype!s}".format(keys=[ k for k in input_keys if k not in valid_keys], toscatype=type(self)))
      # Vérifier que la définition renseigne bien les clefs obligatoires
      required_keys = [ x for x in valid_keys if defkeys[x]['required'] == True ] 
      if not set(required_keys).issubset(set(input_keys)):
        msg.append("Les clefs {keys!s} doivent être renseignées pour la définition d'un {toscatype!s}".format(keys=[ k for k in required_keys if k not in input_keys], toscatype=type(self)))
      # Dans le cas où la définition est valide (pas d'erreur détéctée), elle est interprétée
      valid = (len(msg) == 0)
      if valid:
        for key, value in yamldef.items():
          if 'f' in defkeys[key]:
            defkeys[key]['f'](self,  value)
          if 'subitems' in defkeys[key]:
            __valid_keys(self, value, defkeys[key]['subitems']) 
    return valid, "\n".join(msg)


class ToscaTemplate(ToscaObject):

  tosca_type = 'ToscaTemplate'

  grammar =  { 
    'tosca_simple_yaml_1_0': [{ 
      'tosca_definitions_version': 
         { 'required': True, 'kind': basestring },
      'metadata': 		   
         { 'required': False, 'kind': dict, 
           'subitems': {
              'template_name': 
                { 'required': False, 'kind': basestring  },
              'template_author':
                { 'required': False, 'kind': basestring },
              'template_version':
                { 'required': False, 'kind': basestring } }},
      'description': 		   
         { 'required': False, 'kind': basestring },
      'dsl_definitions': 	   
         { 'required': False, 'kind': dict },
      'imports':		   
         { 'required': False, 'kind': dict },   
      'repositories': 	           
         { 'required': False, 'kind': dict },
      'artifacts_types': 	   
         { 'required': False, 'kind': dict },
      'data_types': 	           
         { 'required': False, 'kind': dict },
      'capability_types':	
         { 'required': False, 'kind': dict },
      'interface_types': 	
         { 'required': False, 'kind': dict },
      'relationship_types':
         { 'required': False, 'kind': dict },
      'node_types':  	
         { 'required': False, 'kind': dict },
      'group_types':  	
         { 'required': False, 'kind': dict },
      'policy_types':  	
         { 'required': False, 'kind': dict },
      'topology_template': 
         { 'required': True, 'kind': dict }}]

    }
  
  def __init__(self, f):
    self.tpls = {}
    self.do_imports({ 'imports': [ f ] }, "")
    self.tpl = self.tpls.get(os.path.basename(f))
    toscaversion = self.tpl['tosca_definitions_version'] # existence et validite de la verison deja verifiees dans do_imports
    yamldef = {}
    alldefkeys = set( reduce( lambda a,b: a.keys()+b.keys(), ToscaTemplate.grammar[toscaversion] ))
    for filename in self.tpls.keys():
      filedef = self.tpls[filename]
      if not isinstance(filedef, dict):
        raise ToscaException("Le contenu du fichier {f} ne correspond pas à un template TOSCA".format(f=fillename))
      for key in filedef.keys():
        if key not in alldefkeys:
          raise ToscaException("Dans le fichier '{f}', le mot clef '{k}' n'est pas valide dans la definition d'un template TOSCA".format(f=filename, k=key)) 
        currentval = yamldef.get(key)
        newval = filedef[key]
        if currentval is None:
          yamldef[key] = newval
        else:
          if isinstance(currentval, dict) and isinstance(newval, dict):
            lencurrentval = len(currentval)
            lennewval = len(newval)
            currentval.update(newval)
            if len(yamldef[key]) < lencurrentval + lennewval:
              raise ToscaException("Le fichier '{f}' redefinit une entite '{k}' deja importee.".format(f=filename, k=key))
          elif isinstance(currentval, list) and isinstance(newval, list):
            yamldef[key] = currentval + newval
            if len(yamldef[key]) < len(currentval) + len(newval):
              raise ToscaException("Le fichier '{f}' redefinit une entite '{k}' deja importee.".format(f=filename, k=key))
          elif key == 'description':
            pass
          elif key == 'tosca_definitions_version':
            if newval != toscaversion:
              raise ToscaException("La version TOSCA importee dans le fichier '{f}' est incoherente avec le template parent".format(f=filename))
    yamldef['tosca_definitions_version'] = toscaversion
    yamldef['description'] = self.description
    ToscaObject.__init__(self, yamldef, toscaversion)  
    

  def do_imports(self, tpl, reldir):
    imports = tpl['imports'] if 'imports' in tpl else [] 
    if isinstance(imports, list):
      for import_def in imports:
        import_file = None
        if isinstance(import_def, basestring):
          import_file = import_def
        if isinstance(import_def, dict) and len(import_def) > 0:
          if len(import_def) == 1: 
            key = import_def.keys()[0]
            val = import_def.values()[0]
            if key not in ['repository', 'namespace_uri', 'namespace_prefix']:
              if isinstance(val, basestring):
                import_file = val
              else:
                if isinstance(val, dict):
                  import_file = val.get('file')
          else:
            if len(import_def) > 1:
              import_file = import_def.get('file') 
        if import_file is not None:
          reldir = reldir + "/" if len(reldir)> 0 else ""
          import_tpl = yamlparser.load_yaml(reldir + import_file) 
          if isinstance(import_tpl, dict):
            fimportname = os.path.basename(import_file)
            if fimportname in self.tpls.keys():
              raise ToscaException("import multiple du fichier: {f}".format(f=fimportname))
            self.tpls[fimportname] = import_tpl
            toscaversion = import_tpl.get('tosca_definitions_version')
            if toscaversion is None or toscaversion not in ALLOWEDTOSCAVERSIONS:
              raise ToscaException("Version TOSCA inconnue ou non definie dans le fichier '{d}{f}'".format(d=reldir,f=import_file))
            tplreldir = os.path.dirname(import_file)
            self.do_imports(import_tpl, reldir + tplreldir)
        

  @property
  def description(self):
     return self.tpl['description'] if 'description' in self.tpl else "" 


