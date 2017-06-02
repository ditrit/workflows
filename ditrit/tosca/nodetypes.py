#!/usr/bin/python

from tosca.template import ToscaTemplate
from tosca.properties import get_properties_definition, get_attributes_definition, get_properties_parameters
from utils.linda import *

def get_types(nt_def, typename):
  """ 
     Get the list of types the node derives from
  """ 
  if typename.split('.')[-1] == 'Root':
    return [ typename ] 
  else:
    typedef = nt_def[typename]
    parent_type = typedef.get('derived_from')
    if isinstance(parent_type, basestring):
      return get_types(parent_type).append(typename) 
    else:
      print "Syntax error"
      return []

def parse_types(toscayaml, model_name):
  """
      Create types internal representation
  """
  node_types = {}
  # Part of the workflows defined in nodes have to be parsed before the part defined in relations. 
  nt_def = toscayaml.get('node_types')
  if type(nt_def) is dict:
  for typename, typedef in nt_def.items():
    val = {}
    if typename in node_types:
      val = types[typename]
    val['type'] = typename
    val['types'] = get_types(nt_def, typename)
    val['type_for_workflow'] = 'tosca.nodes.Root'
    for parent in val['types']:
      type_for_workflow =  nt_def[parent].get(workflows)
      if type_for_workflow is not None:
        val['type_for_workflow'] = type_for_workflow
        break
    val['isCompute'] = 'tosca.nodes.Compute' in val['types']
    val['version'] = typedef.get('version')
    val['metadata'] = {}
    metadata = typedef.get('metadata')
    if isinstance(metadata, dict) and all(map(lambda x: isinstance(x, basestring), metadata.values())):
      val['metadata'] = metadata
    val['description'] = ""
    descr = typedef.get('description')
    if descr is not None:
      val['description'] = descr

   val['attributes'] = get_attributes_definitions(typedef.get('attributes'))
   val['properties'] = get_properties_definitions(typedef.get('properties'))
 
    node_types[nodename] = val

  for typename, typeval in node_types:
    linda_out('types/nodes/{}'.format(typename), val)

