#!/usr/bin/python

from tosca.template import ToscaTemplate
from tosca.properties import get_property_definitions, get_attribute_definitions, get_parameter_definitions
from tosca.requirements import get_requirement_definitions
from tosca.capabilities import get_capability_definitions
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
  for type_name, type_def in nt_def.items():
    val = {}
    if type_name in node_types:
      val = node_types[type_name]
    val['name'] = type_name


    # get the list of parents
    val['types'] = get_types(nt_def, typename)
    if len(val['types'] > 0:
      val['derived_from'] = val['types'][0]
    else:
      print "ERROR : types list is empty for node type '{}'".format(typename)
    
    # for each declarative workflow defined in parents, get the nearest parent declaring the workflow
    types_for_workflows = {} 
    for parent_type in val['types']:
      parent_def = nt_defiget('parent_type')
      if parent_def is None:
        print "ERROR: node type '{}' is referenced but not defined".format(parent_def)
      else:
        workflows = parent_def.get('workflows')
        if isinstance(workflows, dict):
          for workflow_name in workflows.keys():
            workflow_type = types_for_workflows.get(workflow_name)
            if workflow_type is None: 
              types_for_workflows[workflow_name] = parent_type
    val['types_for_workflows'] = types_for_workflows

    # is the node type derived from Compute ?
    val['isCompute'] = 'tosca.nodes.Compute' in val['types']

    # get the version of the node type
    val['version'] = typedef.get('version')

    # get metadata
    val['metadata'] = {}
    metadata = typedef.get('metadata')
    if isinstance(metadata, dict) and all(map(lambda x: isinstance(x, basestring), metadata.values())):
      val['metadata'] = metadata

    # get descrption
    val['description'] = ""
    descr = typedef.get('description')
    if descr is not None:
      val['description'] = descr

   # get properties and attributes
   val['attributes']   = get_attribute_definitions(typedef.get('attributes'))
   val['properties']   = get_property_definitions(typedef.get('properties'))

   # get requirements and capabilities

   val['requirements'] = get_requirement_definitions(typedef.get('requirements'))
   val['capabilities'] = get_capability_definitions(typedef.get('capabilities'))
 
   node_types[nodename] = val

  # store in the ditrit space
  for typename, typeval in node_types:
    linda_out('types/nodes/{}'.format(typename), val)

