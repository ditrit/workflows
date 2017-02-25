#!/usr/bin/python

import os
import sys
import consulate
import json
from utils import consul_lock

# fake operation execution 
def call_operation(ope, fact):
	pass

def call_rel_operation(ope, fact, node):
	pass


class Rete(object):
	"""
		Parent class for RETE objects.
	"""
	
	def __init__(self, workflow_name, consul):
		self.kv = consul.kv
		self.workflow_name = workflow_name
		self.parents=set()
		self.childs=set()
		self.facts=set()
		self.cond= lambda x: True
		self.set_prefix([workflow_name])

	def set_prefix(self, infos):
		self.name = "rete/" + "/".join(map(str, infos)) + "/facts"
		self.kv[self.name] = []
		

	def get_set_of_facts(self):
		return set(json.loads(self.kv[self.name]))

	def add_a_fact(self, fact):
		self.kv[self.name] = list(self.get_set_of_facts() | set([fact]))

	def get_fact_def(self, fact):
		return json.loads(self.kv[fact])

	def insert_fact(self, fact):		
		if self.cond(fact):
			self.add_a_fact(fact)
			for parent in self.parents:
				parent.insert_fact(fact) 

	def add_parent(self, parent):
		self.parents = self.parents | set([ parent ])
		parent.childs = parent.childs | set( [ self ] )
		
	def remove_parent(self, parent):
		self.parents = self.parents - set( [ parent ])
		parent.childs = parent.childs - set( [ self ])

""" 
	'workflows_inputs' defines an entry point for each workflow.
"""
workflows_input = {}

# global variables used to manage weaving.
rete_states     = {}
states_order    = {}

class ReteType(Rete):
	"""
		First condition for each rule : type filtering.
	"""
	
	def __init__(self, workflow_name, typename, consul):
		super(ReteType, self).__init__(workflow_name, consul)
		self.set_prefix([workflow_name, typename])
		if workflow_name not in workflows_input:
			workflows_input[workflow_name] = Rete(workflow_name, consul)
		workflows_input[workflow_name].add_parent(self)
		self.cond= lambda x : self.get_fact_def(x)['type'] == typename

class ReteStateCond(Rete):
	"""
		Rule condition for nodes.
		Simple as state comparison if no weaving is done.
		Have to consider the state of all facts related to ongoing and ingoing relations if weaving is done.
	"""

	def __init__(self, workflow_name, typename, state, step, childs,  consul):
		super(ReteStateCond, self).__init__(workflow_name, consul)
		self.set_prefix([workflow_name, typename, step, state])
		self.state = state
		self.step = step
		self.reterelactions = set()
		self.cond= lambda x : (self.get_fact_def(x)['state'] == state) and (self.get_fact_def(x)['step'] == (step - 1))
		for child in childs:
			child.add_parent(self)
		if workflow_name not in rete_states:
			rete_states[workflow_name] = []
		rete_states[workflow_name].append(self)
	
	def add_reterelaction(self, reterelaction):
		self.reterelactions = self.reterelactions | set( [ reterelaction ])
		
	def __str__(self):
			return "ReteStateCond(state = " + self.state + ", step = " + str(self.step) + ", relsconds = [" + ",".join(map(str,self.reterelactions)) + "]"

	def insert_fact(self, fact):
		if self.cond(fact):
			self.add_a_fact(fact)
			# insert into parent only if all facts related to ingoing or outgoing relations have reached the expected state for weaving.
			if all([ not len(set([ f for f in self.get_fact_def(fact)[relaction.direction][relaction.typename] ]) \
								 - relaction.get_set_of_facts()) \
					for relaction in self.reterelactions ]):
				for parent in self.parents:
					parent.insert_fact(fact) 

class ReteRelCond(Rete):
	"""
		Rule condition for relations.
		Simple as state comparison if no weaving is done.
		Have to consider the state of all facts related to ongoing and ingoing relations if weaving is done.
	"""
	
	def __init__(self, workflow_name, typename, direction, find_step, wait_step, step, childs, consul):
		self.find_step = find_step
		self.wait_step = wait_step
		self.direction = direction
		self.step = step

		self.side = {'out': { 'weaving': 'source_weaving', 'find_step': 'source', 'wait_step': 'target'},
				     'in':  { 'weaving': 'target_weaving', 'find_step': 'target', 'wait_step': 'source'}
				    }[self.direction]

		super(ReteRelCond, self).__init__(workflow_name, consul)
		self.set_prefix([workflow_name, typename, direction, find_step, wait_step, step])
		
		self.cond= lambda r : (self.get_fact_def(r)[self.side['weaving']] == (self.step - 1)) \
							  and (self.find_step == None or self.get_fact_def(self.get_fact_def(r)[self.side['find_step']])['step'] == (self.find_step - 1)) \
							  and (self.wait_step == None or self.get_fact_def(self.get_fact_def(r)[self.side['wait_step']])['step'] >= (self.wait_step - 1))
		for child in childs:
			child.add_parent(self)


	def __str__(self):
		return "ReteRelCond(" + self.direction + ", " + "find_step = " + str(self.find_step)  + ", " + "wait_step: = " + str(self.wait_step) + ", " + "rel_step: = " + str(self.step) + ")"

	def insert_fact(self, fact):
			
		if self.cond(fact):
			self.add_a_fact(fact)
			for parent in self.parents:
				parent.insert_fact(fact) 



class ReteAction(Rete):
	"""
		Rule action part for nodes.
	"""
	
	def __init__(self, workflow_name, typename, actions, step, childs, consul):
		super(ReteAction, self).__init__(workflow_name, consul)
		self.set_prefix([workflow_name, typename, step])
		for child in childs:
			child.add_parent(self)

		self.actions= actions
		self.step = step
		self.set_state = self.actions.get('set_state')
				
	def insert_fact(self, fact):
		# Action can be operation execution
		if 'call_operation' in self.actions:
			call_operation(self.actions['call_operation'], fact)
			print fact + " : " + self.actions['call_operation']
		# Action be a new state for the fact 
		factdef = self.get_fact_def(fact)
		if self.set_state is not None:
			factdef['state'] = self.set_state
			print fact + ".state = " + self.set_state
		# A new step in the workflow is reached for the fact
		#print "Fact = " + fact + " : " + str(facts[fact])
		factdef['step'] = self.step
		self.kv[fact] = factdef
		self.add_a_fact(fact)
		# Action impacts current fact and potentially each fact related to ingoing or outgoing relations.
		workflows_input[self.workflow_name].insert_fact(fact)
		for trel in self.get_fact_def(fact)['in'].values():
			for r in trel:
				workflows_input[self.workflow_name].insert_fact(r)
		for trel in self.get_fact_def(fact)['out'].values():
			for r in trel:
				workflows_input[self.workflow_name].insert_fact(r)

	def __str__(self):
		return "ReteAction( actions = " + str(self.actions)  + ", " + "step: = " + str(self.step) + ")"



class ReteRelAction(Rete):
	"""
		Rule action part for relations.
		The fact on weach on which the operation will be executed (source or target) depends on the weaving direction.
	"""

	def __init__(self, workflow_name, typename, activity, direction, step, childs, consul):
		super(ReteRelAction, self).__init__(workflow_name, consul)
		self.set_prefix([workflow_name, typename, direction, step])
		self.direction = direction
		self.activity = activity
		self.typename = typename
		self.step = step
		self.weavingdir= {'in':'target','out':'source'}[self.direction]
		for child in childs:
			child.add_parent(self)
		
	def insert_fact(self, fact):
		node = self.get_fact_def(fact)[self.weavingdir]
		# Execute operation
		call_rel_operation(self.activity, fact, node)
		print node + " : " + fact + "." + str(self.activity)
		# Define the new state for the fact.
		factdef = self.get_fact_def(fact)
		factdef['done'].append(self.activity)
		factdef[self.weavingdir + '_weaving'] = self.step
		self.kv[fact] = factdef
		self.add_a_fact(fact)
		# Action impacts current relation fact and the node on which action have been executed.
		workflows_input[self.workflow_name].insert_fact(node)
		workflows_input[self.workflow_name].insert_fact(fact)

	def __str__(self):
		return "ReteRelAction(" + self.direction + ", " + "activity = " + str(self.activity)  + ", " + "step: = " + str(self.step) + ")"

def buildRete():
	"""
		This function builds the RETE network parsing the provided workflows definition.
                Workflows defintion is extracted from the set of 'node_types' and 'relationship_types' definition 
		(currently stored in the global 'types_def' variable).
	"""

	# Consul session initialisation 
	consul = consulate.Consul()
	session_id = consul.session.create()
	
	# Part of the workflows defined in nodes have to be parsed before the part defined in relations. 
	ntnames = json.loads(consul.kv['node_types'])
	nt_def = { tname: json.loads(consul.kv[tname]) for tname in ntnames }
	rtnames =  json.loads(consul.kv['rel_types'])
	rt_def = { tname: json.loads(consul.kv[tname]) for tname in rtnames }

    # Parsing of the part of workflows defined at nodes level.
	for typename, node in nt_def.iteritems():
		if 'workflows' in node:
			node_workflows = node['workflows']
			for workflow_name in node_workflows:
				workflow = node_workflows.get(workflow_name)

				if workflow:
					steps = workflow.get('steps')
					if steps:
						# First condition avaluated in rules is the type of facts.
						rete_type = ReteType(workflow_name, typename, consul)
						# States and related steps of the workflow have to be registered for weaving.
						if workflow_name not in states_order:
							states_order[workflow_name] = {'none': 0 }
						# Seems to be a rule to use the name of the workflow with suffix '_sequence'.
						subworkflow = steps.get(workflow_name + '_sequence')
						if subworkflow:
							activities = subworkflow.get('activities')
							# Each activity is a step in the workflow
							step = 1
							old_state = 'none'
							if activities:
								activities.append({ 'set_state': 'ended'})
								for actions in activities:
									new_state = actions.get('set_state')
									# First condition to be met for a fact is to be in the state defined at the preceding step. 
									# This condition can be 'weaved' with part of the workflow defined at relationships type level.
									rete_cond = ReteStateCond(workflow_name, typename, old_state, step, [ rete_type ], consul )
									# Action can be a new state setting for the fact or execution of an operation for the fact. 
									rete_action = ReteAction(workflow_name, typename, actions, step, [ rete_cond ], consul)
									if new_state:
										# A same state can stay during several steps of the workflow 
										# and we have to be able to differentiate them for weaving.
										# So, we register each state and related steps of the workflow.
										states_order[workflow_name][new_state] = step
										old_state = new_state
									step = step + 1

	# Parsing of the part of workflows defined at relationships level. That is where the TOSCA weaving principle is used. 
	for typename, rel in rt_def.iteritems():
		if 'workflow' in rel:
			# Any reason to use 'workflow' for relationships and 'worflows' for nodes ?
			rel_workflows = rel['workflow']
			for workflow_name in rel_workflows:
				workflow = rel_workflows.get(workflow_name)

				if workflow:
					# First condition avaluated in rules is the type of facts.
					rete_type = ReteType(workflow_name, typename, consul)
					for (node_direction, node_weaving) in workflow.items():
						# Weaving steps are different for each direction (ingoing or outgoing relation)
						step = 1
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
							if after in weave:
								weaving_state = after_state
							if before in weave:
								weaving_state = before_state
							# Rete_states is used to find the step 'just after' or 'just before' the 'weaving_state' is reached.
							# The condition found (find_cond) for this step is the weaving point.
							for rete_cond in rete_states[workflow_name]:
								if rete_cond.state == weaving_state:
									break
								if before_state:
									#find_cond = rete_states[workflow_name][rete_states[workflow_name].index(rete_cond) - 1]
									find_cond = rete_cond
								if after_state:
									#find_cond = rete_cond
									find_cond = rete_states[workflow_name][rete_states[workflow_name].index(rete_cond) + 1]
								find_step = find_cond.step
		
							# 'wait_state' and related 'wait_step' concern the condition to be observed on the other node of the relation.
							wait_step = None
							if wait_state:
								wait_step = states_order[workflow_name][wait_state] + 1
		
							# A condition on source and target is created on relations.
							rete_relcond = ReteRelCond(workflow_name, typename, direction, find_step, wait_step, step, [ rete_type ], consul)
							# Action on source or target is launched if condition is met.
							rete_relaction = ReteRelAction(workflow_name, typename, action, direction, step, [ rete_relcond ], consul)
							# Here is the key of the weaving process : condition on the status of all facts related to relations 
							# is insertedat the weaving point.
							find_cond.add_reterelaction(rete_relaction)

							step = step + 1

	consul.session.create(session_id)


def main(args=None):
	"""
		Main function to execute example
	"""
	buildRete()


	# Consul session initialisation 
	consul = consulate.Consul()
	session_id = consul.session.create()
	print "==================="

	for fact in json.loads(consul.kv['node_facts']):
		workflows_input['install'].insert_fact(fact)
	for fact in json.loads(consul.kv['rel_facts']):
		workflows_input['install'].insert_fact(fact)
		
	print "==================="

			
if __name__ == '__main__':
    main()
             
