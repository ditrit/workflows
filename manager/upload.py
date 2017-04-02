#!/usr/bin/python

import os
import sys
import copy
from tosca_template import ToscaTemplate
from linda import *

def prepare_facts(node_list, rel_list, instance_name):
  """ 
        create facts for instance inserting necessary status information for each. 
        Also provides for each node instance the set of outgoing and ingoing relations. 
  """
  facts = {}
  node_nb = {}
  reltypes = { typename: [] for typename in eval(linda_rd('relationship_type_names')) }	
  for node in node_list:
    node_nb[node['name']] = node['nb']
    for n in range(0,node['nb']):
      fact_key = "{}/{}/{}".format(instance_name, node['name'], n)
      fact_def = {}
      fact_def['type'] = node['type']
      fact_def['name'] = node['name']
      fact_def['state'] = 'none'
      fact_def['step']  = 0
      fact_def['out']   = copy.deepcopy(reltypes)
      fact_def['in']    = copy.deepcopy(reltypes)
      facts[fact_key]= fact_def
  for node in rel_list:
    source_name = node['source']
    nb_source   = node_nb[source_name]
    target_name = node['target']
    nb_target   = node_nb[target_name]
    for index_source in range(0, nb_source):
      source_key = "{}/{}/{}".format(instance_name, source_name, index_source)
      for index_target in range(0, nb_target):
        target_key = "{}/{}/{}".format(instance_name, target_name, index_target) 
        facts[source_key]['out'][node['type']].append(target_key)
        facts[target_key]['in'][node['type']].append(source_key)

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

def upload(toscayaml, instance_name):

  # defined here because we can not currently parse
  node_list = [ 
    { 'name': 'A', 'type': 'tosca.nodes.Root', 'nb': 1},
    { 'name': 'B', 'type': 'tosca.nodes.Root', 'nb': 1},
    { 'name': 'C', 'type': 'tosca.nodes.Root', 'nb': 1},
    { 'name': 'D', 'type': 'tosca.nodes.Root', 'nb': 1},
    { 'name': 'srvA', 'type': 'tosca.nodes.Root', 'nb': 1},
    { 'name': 'srvB', 'type': 'tosca.nodes.Root', 'nb': 2},
    { 'name': 'srvC', 'type': 'tosca.nodes.Root', 'nb': 1},
    { 'name': 'srvD', 'type': 'tosca.nodes.Root', 'nb': 5} ]

  # defined here because we can not currently parse it
  rel_list = [
    { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'B' },
    { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'C' },
    { 'type': 'tosca.relationships.ConnectsTo', 'source': 'B', 'target': 'D' },
    { 'type': 'tosca.relationships.ConnectsTo', 'source': 'D', 'target': 'C' },
    { 'type': 'tosca.relationships.HostedOn', 'source': 'A', 'target': 'srvA' },
    { 'type': 'tosca.relationships.HostedOn', 'source': 'B', 'target': 'srvB' },
    { 'type': 'tosca.relationships.HostedOn', 'source': 'C', 'target': 'srvC' },
    { 'type': 'tosca.relationships.HostedOn', 'source': 'D', 'target': 'srvD' }]

  # Insert facts into kvstore
  prepare_facts(node_list, rel_list, instance_name)



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
    upload(toscayaml, model_name)
			
if __name__ == '__main__':
  main()
             
