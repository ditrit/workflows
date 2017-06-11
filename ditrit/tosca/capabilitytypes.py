#!/usr/bin/python

from tosca.template import ToscaTemplate
from tosca.properties import get_property_definitions, get_attribute_definitions, get_parameter_definitions
from tosca.derivedtypes import get_types
from tosca.basetypes import Version
from utils.linda import *

def parse_capability_types(toscayaml, model_name):
  """
      Create types internal representation
  """
  capa_types = {}
  # Part of the workflows defined in nodes have to be parsed before the part defined in relations. 
  capa_def = toscayaml.get('capability_types')
  if type(capa_def) is dict:
    for type_name, type_def in capa_def.items():
      val = {}
      if type_name in capa_types:
        val = capa_types[type_name]
      val['name'] = type_name

      # get the list of parents
      val['types'] = get_types(capa_def, type_name)
      if len(val['types']) > 0:
        val['derived_from'] = val['types'][0]
      else:
        print "ERROR : types list is empty for node type '{}'".format(type_name)
      
      # get the version of the node type
      val['version'] = str(Version(type_def.get('version')))

      # get descrption
      val['description'] = ""
      descr = type_def.get('description')
      if descr is not None:
        val['description'] = descr

      # get properties and attributes
      val['attributes']   = get_attribute_definitions(type_def.get('attributes'))
      val['properties']   = get_property_definitions(type_def.get('properties'))

      # get valid_source_types
      val['valid_source_types'] = []
      sources = type_def.get('valid_source_types')
      if isinstance(sources, list) and all(map(lambda x: isinstance(x, basestring), sources)):
        val['valid_source_types'] = sources

      capa_types[type_name] = val

  # store in the ditrit space
  for type_name, type_val in capa_types.items():
    linda_out('types/{}/capabilities/{}'.format(model_name, type_name), type_val)

