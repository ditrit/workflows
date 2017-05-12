#!/usr/bin/python

import os
import sys
import copy
from tosca_template import ToscaTemplate
from linda import *

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

def parse_declarative_workflows(toscayaml):
  """
    This function builds the RETE network parsing the provided workflows definition.
    Workflows defintion is extracted from the set of 'node_types' and 'relationship_types' definition 
  """
  states_order    = {}

  # Part of the workflows defined in nodes have to be parsed before the part defined in relations. 
  nt_def = toscayaml.get('node_types')
  rt_def = toscayaml.get('relationship_types')
  linda_out('node_type_names',         nt_def.keys())
  linda_out('relationship_type_names', rt_def.keys())

  rete = {}
  # Parsing of the part of workflows defined at nodes level.
  for typename, node in nt_def.iteritems():
    states_order[typename] = {}
    if 'workflows' in node:
      node_workflows = node['workflows']
      for workflow_name in node_workflows:
        workflow = node_workflows.get(workflow_name)

        if workflow:
          linda_out("DeclarativeWorkflow/{}".format(workflow_name), time.time())
          steps = workflow.get('steps')
          if steps:
            # States and related steps of the workflow have to be registered for weaving.
            if workflow_name not in states_order[typename]:
              states_order[typename][workflow_name] = {'none': 0 }
            # Seems to be a rule to use the name of the workflow with suffix '_sequence'.
            subworkflow = steps.get(workflow_name + '_sequence')
            if subworkflow:
              activities = subworkflow.get('activities')
              # Each activity is a step in the workflow
              step = 1
              old_state = 'none'
              if activities:
                activities.append({ 'set_state': 'ended'})
                for action in activities:
                  new_state = action.get('set_state')
                  operation = action.get('call_operation')
                  rete['ReteNode/{}/{}/{}'.format(workflow_name, typename, step)] = \
                      { 'weaving': {'in': {}, 'out': {}},
                        'facts': [], 
                        'set_state': new_state, 
                        'call_operation': operation }
                  if new_state:
                    # A same state can stay during several steps of the workflow 
                    # and we have to be able to differentiate them for weaving.
                    # So, we register each state and related steps of the workflow.
                    states_order[typename][workflow_name][new_state] = step
                  step = step + 1

  # Parsing of the part of workflows defined at relationships level. That is where the TOSCA weaving principle is used. 
  for typename, rel in rt_def.iteritems():
    if 'workflow' in rel:
      # Any reason to use 'workflow' for relationships and 'worflows' for nodes ?
      rel_workflows = rel['workflow']
      if rel_workflows is None:
        rel_workflows = rel['workflows']
      for workflow_name in rel_workflows:
        workflow = rel_workflows.get(workflow_name)

        if workflow:
          # First condition avaluated in rules is the type of facts.
          for (node_direction, node_weaving) in workflow.items():
            if node_direction == 'source_weaving':
              direction, wait, after, before, activity = 'out', 'wait_target', 'after', 'before', 'activity'
            if node_direction == 'target_weaving':
              direction, wait, after, before, activity = 'in', 'after_source', 'after', 'before', 'activity'
            for weave in node_weaving:
              # An activity can be weaved just 'after' or just 'before' a state as been reached for the node 
              # (source node or target node of the relation depending of its direction).
              after_state = weave.get(after)
              before_state = weave.get(before)
              wait_state  = weave.get(wait)
              action  = weave.get(activity)

              for nodetype in nt_def:

                # Rete_states is used to find the step 'just after' or 'just before' the 'weaving_state' is reached.
                # The condition found (find_cond) for this step is the weaving point.
                if before_state:
                  find_step = states_order[nodetype][workflow_name][before_state]
                if after_state:
                  find_step = states_order[nodetype][workflow_name][after_state]

                # 'wait_state' and related 'wait_step' concern the condition to be observed on the other node of the relation.
                wait_step = None
                if wait_state:
                  wait_step = states_order[nodetype][workflow_name][wait_state] + 1

                keyrete  = 'ReteNode/{}/{}/{}'.format(workflow_name, nodetype, find_step)
                rete[keyrete]['weaving'][direction][typename]= {'wait_step': wait_step, 'facts': [], 'activity': action }

  # insertion du reseau rete dans Consul
  for key in rete:
    linda_out(key, rete[key])

def parse_tosca(filename):
  toscayaml = None
  if filename is not None:
    tosca = ToscaTemplate(filename)
    if tosca is not None:
      toscayaml = tosca.yamldef
  return toscayaml

def library(filename):
  toscayaml = tosca_parser(filename)
  if toscayaml is not None:
      parse_declarative_workflows(toscayaml)

def model(filename, model_name):
  toscayaml = tosca_parser(filename)
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
             
