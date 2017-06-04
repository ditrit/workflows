#!/usr/bin/python

from tosca.template import ToscaTemplate
from tosca.properties import get_property_definitions, get_attribute_definitions, get_parameter_definitions
from tosca.interfaces import *
from tosca.capabilities import *
from tosca.requirements import *
from tosca.derivedtypes import get_types
from utils.linda import *

def parse_data_types(toscayaml, model_name):
  """
      Create types internal representation
  """
  data_types = {}
  data_def = toscayaml.get('data_types')

  if type(data_def) is dict:
  for type_name, type_def in data_def.items():
    val = {}
    if type_name in data_types:
      val = data_types[type_name]
    val['name'] = type_name

    # get the list of parents
    val['types'] = get_types(data_def, type_name)
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

   # get constraints
   ## TODO: verify constraint is ok with parse_constraint (should retuirn None if not ok)
   val['constraints']   = type_def.get('constraints')

   # get properties
   val['properties'] = get_property_definitions(type_def.get('properties'))

   data_types[type_name] = val

  # store in the ditrit space
  for type_name, type_val in data_types:
    linda_out('types/datatypes/{}'.format(type_name), type_val)

