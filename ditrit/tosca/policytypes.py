#!/usr/bin/python

from tosca.template import ToscaTemplate
from tosca.properties import get_property_definitions, get_attribute_definitions, get_parameter_definitions
from tosca.interfaces import *
from tosca.capabilities import *
from tosca.requirements import *
from tosca.triggers import *
from tosca.derivedtypes import get_types
from utils.linda import *

def parse_policy_types(toscayaml, model_name):
  """
      Create types internal representation
  """
  pol_types = {}
  pol_def = toscayaml.get('policy_types')

  if type(pol_def) is dict:
  for type_name, type_def in pol_def.items():
    val = {}
    if type_name in pol_types:
      val = pol_types[type_name]
    val['name'] = type_name

    # get the list of parents
    val['types'] = get_types(pol_def, type_name)
    if len(val['types'] > 0:
      val['derived_from'] = val['types'][0]
    else:
      print "ERROR : types list is empty for policy type '{}'".format(type_name)
    
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

   # get properties and attributes
   val['properties']   = get_property_definitions(type_def.get('properties'))

   # get targets 
   ## TODO: verify each member is a node type or a group type
   val['targets'] = []
   targets = type_def.get('targets')
   if isinstance(targets, list) and all(map(lambda x: isinstance(x, basestring), targets)):
     val['targets'] = targets

   # get triggers
   val['triggers'] = get_trigger_definitions(type_def.get('triggers'))

   pol_types[type_name] = val

  # store in the ditrit space
  for type_name, type_val in pol_types:
    linda_out('types/policies/{}'.format(type_name), type_val)

