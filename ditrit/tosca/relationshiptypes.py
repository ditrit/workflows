#!/usr/bin/python

from tosca.template import ToscaTemplate
from tosca.properties import get_property_definitions, get_attribute_definitions, get_parameter_definitions
from tosca.requirements import get_requirement_definitions
from tosca.capabilities import get_capability_definitions
from tosca.interfaces import get_interface_definitions
from tosca.derivedtypes import get_types
from utils.linda import *

def parse_relationship_types(toscayaml, model_name):
  """
      Create types internal representation
  """
  rel_types = {}
  # Part of the workflows defined in nodes have to be parsed before the part defined in relations. 
  rt_def = toscayaml.get('relationship_types')
  if type(rt_def) is dict:
  for type_name, type_def in rt_def.items():
    val = {}
    if type_name in rel_types:
      val = rel_types[type_name]
    val['name'] = type_name


    # get the list of parents
    val['types'] = get_types(rt_def, type_name)
    if len(val['types'] > 0:
      val['derived_from'] = val['types'][0]
    else:
      print "ERROR : types list is empty for relationship type '{}'".format(type_name)
    
    # for each declarative workflow defined in parents, get the nearest parent declaring the workflow
    types_for_workflows = {} 
    for parent_type in val['types']:
      parent_def = rt_def.get('parent_type')
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
    val['isDependsOn']  = 'tosca.relationships.DependsOn'  in val['types']
    val['isConnectsTo'] = 'tosca.relationships.ConnectsTo' in val['types']
    val['isHostedOn']   = 'tosca.relationships.HOstedOn'   in val['types']

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
   val['attributes']   = get_attribute_definitions(type_def.get('attributes'))
   val['properties']   = get_property_definitions(type_def.get('properties'))

   # get valid_target_types
   val['valid_target_types'] = []
   targets = type_def.get('valid_target_types')
   if isinstance(targets, list) and all(map(lambda x: isinstance(x, basestring), targets)):
     val['valid_target_types'] = targets

   # get interfaces
   val['interfaces'] = get_interfaces_definitions(type_def.get('interfaces'))
 
   # get workflows
   val['workflows'] = type_def.get('workflows')

   rel_types[type_name] = val

  # store in the ditrit space
  for type_name, type_val in rel_types:
    linda_out('types/relationships/{}'.format(type_name), type_val)

