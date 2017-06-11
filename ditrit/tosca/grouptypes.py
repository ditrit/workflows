#!/usr/bin/python

from tosca.template import ToscaTemplate
from tosca.properties import get_property_definitions, get_attribute_definitions, get_parameter_definitions
from tosca.interfaces import *
from tosca.capabilities import *
from tosca.requirements import *
from tosca.derivedtypes import get_types
from utils.linda import *

def parse_group_types(toscayaml, model_name):
  """
      Create types internal representation
  """
  grp_types = {}
  grp_def = toscayaml.get('group_types')

  if type(grp_def) is dict:
    for type_name, type_def in grp_def.items():
      val = {}
      if type_name in grp_types:
        val = grp_types[type_name]
      val['name'] = type_name

      # get the list of parents
      val['types'] = get_types(grp_def, type_name)
      if len(val['types']) > 0:
        val['derived_from'] = val['types'][0]
      else:
        print "ERROR : types list is empty for group type '{}'".format(type_name)
    
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

      # get requirements and capabilities
      val['requirements'] = get_requirement_definitions(type_def.get('requirements'))
      val['capabilities'] = get_capability_definitions(type_def.get('capabilities'))

      # get members 
      ## TODO: verify each member is a nodei type, a capability type or a group type
      val['members'] = []
      members = type_def.get('members')
      if isinstance(members, list) and all(map(lambda x: isinstance(x, basestring), members)):
        val['members'] = members

      # get interfaces
      val['interfaces'] = get_interface_definitions(type_def.get('interfaces'))

      grp_types[type_name] = val

  # store in the ditrit space
  for type_name, type_val in grp_types.items():
    linda_out('types/{}/groups/{}'.format(model_name, type_name), type_val)

