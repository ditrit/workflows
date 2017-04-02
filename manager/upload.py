#!/usr/bin/python

import os
import sys
import copy
from tosca_template import ToscaTemplate
from linda import *

def prepare_facts(topology_templates):
  """ 
        create facts for instance inserting necessary status information for each. 
        Also provides for each node instance the set of outgoing and ingoing relations. 
  """
  facts = {}
  node_nb = {}

  reltypes = { typename: [] for typename in eval(linda_rd('relationship_type_names')) }	
  for model_name, model_def in topology_templates.items():
    if type(model_def) is dict: 
      topology_template = model_def.get('topology_template')
      if type(topology_template) is dict:
        node_templates = topology_template.get('node_templates')
        if type(node_templates) is dict:
          for node_name, node_template in node_templates.items():
            fact_key = "{}/{}/{}".format(model_name, node_name, 1)
            fact_def = facts.get(fact_key)
            if fact_def is None:
              fact_def = {}
            fact_def['type'] = node_template.get('type')
            fact_def['name'] = node_name
            fact_def['state'] = 'none'
            fact_def['step']  = 0
            fact_def['out']   = copy.deepcopy(reltypes)
            if fact_def.get('in') is None:
              fact_def['in']  = copy.deepcopy(reltypes)
            requirements = node_template.get('requirements')  
            print "requirements de {} : {}".format(fact_key, requirements)
            if type(requirements) is list:
              for requirement in requirements:
                if type(requirement) is dict:
                  for req_name, req_def in requirement.items():
                    target_name = req_def.get('node')
                    rel_type =  req_def.get('relationship')
                    if isinstance(target_name, basestring) and isinstance(rel_type, basestring):
                      target_key =  "{}/{}/{}".format(model_name, target_name, 1)
                      fact_def['out'][rel_type].append(target_key)
                      target_def = facts.get(target_key)
                      if target_def is None:
                        facts[target_key] = copy.deepcopy({'in': reltypes})
                      facts[target_key]['in'][rel_type].append(fact_key)
            facts[fact_key] = fact_def

  linda_out("facts", facts.keys())
  for fact_key, fact_def in facts.items():
    linda_out("Fact/{}".format(fact_key), fact_def)

def prepare_workflows(toscayaml):
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
                      {	'weaving': {'in': {}, 'out': {}},
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

def upload(model_name):

  # defined here because we can not currently parse it
  topology_templates = { model_name: { 
  'topology_template': {
    'node_templates': { 
      'A': {'type': 'tosca.nodes.Root',
            'requirements': [
              { 'A2B': { 'relationship': 'tosca.relationships.ConnectsTo', 'node': 'B' }},
              { 'A2C': { 'relationship': 'tosca.relationships.ConnectsTo', 'node': 'C' }},
              { 'host': { 'relationship': 'tosca.relationships.HostedOn', 'node': 'srvA' }}]
           },
      'B': {'type': 'tosca.nodes.Root',
            'requirements': [
              { 'B2D': { 'relationship': 'tosca.relationships.ConnectsTo', 'node': 'D' }},
              { 'host': { 'relationship': 'tosca.relationships.HostedOn', 'node': 'srvB' }}]
           },
      'C': {'type': 'tosca.nodes.Root',
            'requirements': [
              { 'host': { 'relationship': 'tosca.relationships.HostedOn', 'node': 'srvC' }}]
           },
      'D': {'type': 'tosca.nodes.Root',
            'requirements': [
              { 'host': { 'relationship': 'tosca.relationships.HostedOn', 'node': 'srvD' }},
              { 'D2C': { 'relationship': 'tosca.relationships.ConnectsTo', 'node': 'C' }}]
           },
      'srvA': {'type': 'tosca.nodes.Root'},
      'srvB': {'type': 'tosca.nodes.Root'},
      'srvC': {'type': 'tosca.nodes.Root'},
      'srvD': {'type': 'tosca.nodes.Root'}}}}} 


  # Insert facts into kvstore
  prepare_facts(topology_templates)



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
  toscayaml = {}

  if command == 'library':
    filename = arg2
    if filename is not None:
      tosca = ToscaTemplate(filename)
      if tosca is not None:
        toscayaml = tosca.yamldef
        prepare_workflows(toscayaml)

  if command == 'model':
    model_name = arg2
    print "Push data into Consul"
    upload(model_name)
			
if __name__ == '__main__':
  main()
             
