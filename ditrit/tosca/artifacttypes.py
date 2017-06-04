#!/usr/bin/python

from tosca.template import ToscaTemplate
from tosca.properties import get_property_definitions, get_attribute_definitions, get_parameter_definitions
from tosca.derivedtypes import get_types
from utils.linda import *

def parse_artifact_types(toscayaml, model_name):
  """
      Create types internal representation
  """
  artifact_types = {}
  artifact_def = toscayaml.get('artifact_types')

  if type(artifact_def) is dict:
  for type_name, type_def in artifact_def.items():
    val = {}
    if type_name in artifact_types:
      val = artifact_types[type_name]
    val['name'] = type_name

    # get the list of parents
    val['types'] = get_types(artifact_def, type_name)
    if len(val['types'] > 0:
      val['derived_from'] = val['types'][0]
    else:
      print "ERROR : types list is empty for data type '{}'".format(type_name)
    
    # get the version of the node type
    val['version'] = str(Version(type_def.get('version')))

    # get metadata
    val['metadata'] = {}
    metadata = type_def.get('metadata')
    if isinstance(metadata, dict) and all(map(lambda x: isinstance(x, basestring), metadata.values())):
      val['metadata'] = metadata

    # get descrption
    val['description'] = ""
    descr = type_def.get('description')
    if descr is not None:
      val['description'] = descr

   # get mime_type
   val['mime_type'] = type_def.get('mime_type') 
   if not isinstance(val['mime_type'], basestring):
     val['mime_type']   = None

   # get file_exts
   exts = type_def.get('file_ext') 
   if isinstance(exts, list) and all(map(lambda x : isinstance(x, basestring), exts)):
     val['file_ext'] = exts
   else
     print "Syntax Error : syntax error for file extensions '{}' for artifact type '{}'".format(exts, type_name)
     val['file_ext'] = None

   # get properties
   val['properties'] = get_property_definitions(type_def.get('properties'))

   artifact_types[type_name] = val

  # store in the ditrit space
  for type_name, type_val in artifact_types:
    linda_out('types/artifacts/{}'.format(type_name), type_val)

