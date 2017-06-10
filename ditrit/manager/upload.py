#!/usr/bin/python

import os
import sys
import copy
from tosca.template import ToscaTemplate
from tosca.workflows import *
from utils.linda import *

def is_capability_of_type(capability_type, capability_name, capability_def, node_type):
  """
       Is the capability 'capability_name' of type 'capability_type' ?
       For now, just equality between name and type, do be reviewed...
  """
  return capability_name == capability_type

def fill_node_properties(node_template, node_def):
  """
       Get properties of the node
  """
  properties = node_template.get('properties')  
  if type(properties) is dict:
    node_def['properties'] = properties

def fill_node_operations(node_template, node_def):
  operations = {}
  if node_def['type'].startswith("tosca.nodes."):
    interface_prefix = 'tosca.interfaces.node.lifecycle.'
  interfaces = node_template.get('interfaces')  
  if type(interfaces) is dict:
    for interface_name, interface_def in interfaces.items():
      if interface_name.find(".") == -1: 
        interface_id = interface_prefix + interface_name
      else:
        interface_id = interface_name
      inputs_interface = {}
      if type(interface_def) is dict:
        if 'inputs' in interface_def:
          inputs_interface = interface_def['inputs']
        operations_keys = interface_def.keys()
        operations_keys.remove('inputs')
        for operation_name in operations_keys:
          operation_def = interface_def[operation_name]
          operation_id = "{}.{}".format(interface_id, operation_name)
          operation_value = ""
          inputs = copy.deepcopy(inputs_interface) 
          if isinstance(operation_def, basestring):
            operation_value = operation_def
          else:
            if isinstance(operation_def, dict):
              implementation = operation_def.get('implementation')
              if isinstance(implementation, basestring):
                operation_value = implementation
              else:
                if isinstance(implementation, dict):
                  primary = implementation.get('primary')
                  if isinstance(primary, basestring):
                    operation_value = primary
              inputs_ope = operation_def.get('inputs')
              if isinstance(inputs_ope, dict):
                inputs.update(inputs_ope)
          operations[operation_id] = {'name': operation_value, 'inputs': inputs}
  node_def['operations'] = operations 

def fill_node_scalability_props(node_template, node_def):
  """
       Get min, max and default values for scaling values of the node
  """
  min_instances = max_instances = default_instances = 1
  capabilities = node_template.get('capabilities')  
  if type(capabilities) is dict:
    for capability_name, capability_def in capabilities.items():
      if is_capability_of_type('scalable', capability_name, capability_def, node_template.get('type')):
        if type(capability_def) is dict:
          properties = capability_def.get('properties')
          if type(properties) is dict:
            min_instances = properties.get('min_instances')
            if min_instances is None:
              min_instances = 1
            max_instances = properties.get('max_instances')
            if max_instances is None:
              max_instances = 1
            default_instances = properties.get('default_instances')
            if default_instances is None:
              default_instances = 1
  node_def['nb_min'] = min_instances
  node_def['nb_max'] = max_instances
  node_def['nb']     = default_instances

def fill_node_relationships(node_template, model_name, node_key, node_def, model, reltypes):
  """ 
      Parse node_template to extract relationships and fill 'in' and 'out' part of 'model_def'
  """
  requirements = node_template.get('requirements')  
  if type(requirements) is list:
    for requirement in requirements:
      if type(requirement) is dict:
        for req_name, req_def in requirement.items():
          target_name = req_def.get('node')
          rel_type =  req_def.get('relationship')
          if isinstance(target_name, basestring) and isinstance(rel_type, basestring):
            target_key =  "{}/{}".format(model_name, target_name)
            node_def['out'][rel_type].append(target_key)
            target_def = model.get(target_key)
            if target_def is None:
              model[target_key] = copy.deepcopy({'in': reltypes})
            model[target_key]['in'][rel_type].append(node_key)

def get_scalability_path(node_key, model):
  """
       Compute the scalability path of the current node i.e. from root to the node 
       Path is built throw 'hosted_on' relationships using the property 'default_instances'.
  """
  node_def = model.get(node_key)
  val = ""
  if type(node_def) is dict:
    nb = node_def.get('nb')
    if nb is None:
      nb = 1
    out = node_def.get('out')
    if type(out) is dict:
      hosted_on = out.get('tosca.relationships.HostedOn')
      if type(hosted_on) is list:
        if len(hosted_on) > 1:
          print "Error: '{}' is hosted on several nodes '{}'".format(node_key, hosted_on) 
        if len(hosted_on) == 1:
          val = "{}:{}".format(get_scalability_path(hosted_on[0], model), nb)
        else:
          val = nb
  return  val

def parse_model(toscayaml, model_name):
  """ 
        Create model internal representation preparing instance status information.
        Also provides for each node the set of outgoing and ingoing relations. 
  """
  model = {}
  node_nb = {}

  reltypes = { typename: [] for typename in eval(linda_rd('relationship_type_names')) }
  topology_template = toscayaml.get('topology_template')
  if type(topology_template) is dict:
    node_templates = topology_template.get('node_templates')
    if type(node_templates) is dict:
      for node_name, node_template in node_templates.items():
        node_key = "{}/{}".format(model_name, node_name)
        node_def = model.get(node_key)
        if node_def is None:
          node_def = {}
        node_def['type'] = node_template.get('type')
        node_def['name'] = node_name
        node_def['state'] = 'none'
        node_def['step']  = 0
        node_def['out']   = copy.deepcopy(reltypes)
        if node_def.get('in') is None:
          node_def['in']  = copy.deepcopy(reltypes)
        fill_node_properties(node_template, node_def)
        fill_node_relationships(node_template, model_name, node_key, node_def, model, reltypes)
        fill_node_scalability_props(node_template, node_def) 
        fill_node_operations(node_template, node_def) 
        model[node_key] = node_def

  model_names = linda_rd("Model")
  if model_names is None:
    model_names = [] 
  else:
    model_names = eval(model_names)
  model_names.append(model_name)
  linda_out("Model", list(set(model_names)))
  linda_out("Model/{}".format(model_name), time.time())
  linda_out("Model/{}/keys".format(model_name), model.keys())
  for node_key, node_def in model.items():
    node_def['scalability_path'] = get_scalability_path(node_key, model)
    linda_out("Model/{}".format(node_key), node_def)

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

def parse_tosca(filename):
  toscayaml = None
  if filename is not None:
    tosca = ToscaTemplate(filename)
    if tosca is not None:
      toscayaml = tosca.yamldef
  return toscayaml

def library(filename):
  toscayaml = parse_tosca(filename)
  if toscayaml is not None:
      parse_declarative_workflows(toscayaml)

def model(filename, model_name):
  toscayaml = parse_tosca(filename)
  if toscayaml is not None:
      parse_model(toscayaml, model_name) 

def main(args=None):
  """
    Upload a TOSCA template given in arguments (imports is ok).
    Workflow definition is uploaded from a TOSCA template.
    Facts are not currently loaded from the template.
  """

  print "TOSCA parsing"
  command = sys.argv[1] if len(sys.argv) > 1 else None
  arg2 = sys.argv[2] if len(sys.argv) > 2 else None
  arg3 = sys.argv[3] if len(sys.argv) > 3 else None

  if command == 'library':
    filename = arg2
    library(filename)

  if command == 'model':
    filename = arg2
    model_name = arg3
    model(filename, model_name)

if __name__ == '__main__':
  main()
             
