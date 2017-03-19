#!/usr/bin/python

import os
import sys
import copy
from tosca_template import ToscaTemplate
from linda import *



def prepare_facts(node_facts, rel_facts, toscayaml):
	""" 
        	Initializes necessary status information for each fact. 
                Also provides for each node instance the set of outgoing and ingoing relations. 
	"""
	reltypes = { typename: [] for typename in toscayaml.get('relationship_types') }	
	for name, fact in node_facts.items():
			fact['state'] = 'none'
			fact['step']  = 0
			fact['out']   = copy.deepcopy(reltypes)
			fact['in']    = copy.deepcopy(reltypes)
	for name, fact in rel_facts.items():
			node_facts[fact['source']]['out'][fact['type']].append(fact['target'])
			node_facts[fact['target']]['in'][fact['type']].append(fact['source'])

	linda_out("node_facts", node_facts.keys())
	for name, fact in node_facts.items():
		linda_out("Fact/{}".format(name), fact)

def prepare_workflows(toscayaml):
	"""
		This function builds the RETE network parsing the provided workflows definition.
                Workflows defintion is extracted from the set of 'node_types' and 'relationship_types' definition 
	"""
	states_order    = {}
	
	# Part of the workflows defined in nodes have to be parsed before the part defined in relations. 
	nt_def = toscayaml.get('node_types')
	rt_def = toscayaml.get('relationship_types')

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
										{ 	'weaving':			{'in': {}, 'out': {}},
											'facts': 			[], 
											'set_state': 		new_state, 
											'call_operation': 	operation }
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
		




def upload(toscayaml):

	# defined here because we can not currently parse
	node_facts = { 
		'A': 	{ 'type': 'tosca.nodes.Root' },
		'B': 	{ 'type': 'tosca.nodes.Root' },
		'C': 	{ 'type': 'tosca.nodes.Root' },
		'D': 	{ 'type': 'tosca.nodes.Root' },
		'srvA': { 'type': 'tosca.nodes.Root' },
		'srvB': { 'type': 'tosca.nodes.Root' },
		'srvC': { 'type': 'tosca.nodes.Root' },
		'srvD': { 'type': 'tosca.nodes.Root' }}

	# defined here because we can not currently parse it
	rel_facts = {
		'rab': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'B' },
		'rac': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'C' },
		'rbd': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'B', 'target': 'D' },
		'rdc': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'D', 'target': 'C' },
		'ha':   { 'type': 'tosca.relationships.HostedOn', 'source': 'A', 'target': 'srvA' },
		'hb':   { 'type': 'tosca.relationships.HostedOn', 'source': 'B', 'target': 'srvB' },
		'hc':   { 'type': 'tosca.relationships.HostedOn', 'source': 'C', 'target': 'srvC' },
		'hd':   { 'type': 'tosca.relationships.HostedOn', 'source': 'D', 'target': 'srvD' }}


	# Insert facts into kvstore
	prepare_facts(node_facts, rel_facts, toscayaml)

	# Parse and insert workflows into Consul
	prepare_workflows(toscayaml)


def main(args=None):
	"""
		Upload a TOSCA template given in arguments (imports is ok).
		Workflow definition is uploaded from a TOSCA template.
		Facts are not currently loaded from the template.
	"""

	print "TOSCA parsing"
	filename = sys.argv[1] if len(sys.argv) > 1 else None
	toscayaml = {}
	
	if filename is not None:
		tosca = ToscaTemplate(filename)
		if tosca is not None:
			toscayaml = tosca.yamldef

	print "Push data into Consul"
	upload(toscayaml)
			
if __name__ == '__main__':
    main()
             
