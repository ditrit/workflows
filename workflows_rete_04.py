#!/usr/bin/python

import os
import sys

"""
	'types_def' is the literal yaml transcription of the both TOSCA normative types 
	in which default install and uninstall workflows are defined.

"""
types_def = {
  'tosca.nodes.Root':
     {'workflows':
       {'install':
         { 'steps':
           { 'install_sequence':
             { 'activities': [
               { 'set_state': 'creating'},
               { 'call_operation': 'tosca.interfaces.node.lifecycle.Standard.create' },
               { 'set_state': 'created' },
               { 'set_state': 'configuring'},
               { 'call_operation': 'tosca.interfaces.node.lifecycle.Standard.configure'},
               { 'set_state': 'configured'},
               { 'set_state': 'starting' },
               { 'call_operation': 'tosca.interfaces.node.lifecycle.Standard.start'},
               { 'set_state': 'started'},
               { 'set_state': 'ended'},
               ]
             }
           }
         },
        'uninstall':
         { 'steps':
           { 'uninstall_sequence':
             { 'activities': [
               { 'set_state': 'stopping'},
               { 'call_operation': 'tosca.interfaces.node.lifecycle.Standard.stop' },
               { 'set_state': 'deleting'},
               { 'call_operation': 'tosca.interfaces.node.lifecycle.Standard.delete' },
               { 'set_state': 'deleted'}]
             }
           }
         }
       }
     },
  'tosca.relationships.ConnectsTo':
     {'workflow':
       {'install': { 
         'source_weaving': [
           { 'after': 'configuring',
#             'wait_target': 'created',
             'wait_target': 'started',
		     'activity': 'tosca.interfaces.relationships.Configure.pre_configure_source'},
		   { 'before': 'configured',
		     'activity': 'tosca.interfaces.relationships.Configure.post_configure_source'},
           { 'before': 'starting',
             'wait_target': 'started'},
           { 'after': 'started',
             'activity': 'tosca.interfaces.relationships.Configure.add_target'} ] ,
         'target_weaving': [
           { 'after': 'configuring', 
             'after_source': 'created',
             'activity': 'tosca.interfaces.relationships.Configure.pre_configure_target'},
           { 'before': 'configured',
             'activity': 'tosca.interfaces.relationships.Configure.post_configure_target'},
           { 'after': 'started',
             'activity': 'tosca.interfaces.relationships.Configure.add_source' } ] }
       } 
	 }
  }

"""  'tosca.relationships.HostedOn':
     {'workflow':
       {'install': { 
         'source_weaving': [
           { 'before': 'configuring',
             'wait_target': 'started',
             'activity': 'tosca.interfaces.relationships.Configure.pre_configure_source' } 
             ] 
           }
       }
     }"""

""",
  'tosca.relationships.HostedOn':
     {'workflow':
       {'install': { 
         'source_weaving': [
           { 'before': 'configuring',
             'wait_target': 'started',
             'activity': 'tosca.interfaces.relationships.Configure.pre_configure_source' } 
             ] 
           }
       }
     }
"""


"""
	Example facts used to test the workflow	
"""

facts = { 'A': 	{ 'type': 'tosca.nodes.Root' },
          'B': 	{ 'type': 'tosca.nodes.Root' },
          'C': 	{ 'type': 'tosca.nodes.Root' },
          'D': 	{ 'type': 'tosca.nodes.Root' },
		  'rab': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'B' },
		  'rac': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'C' },
		  'rbd': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'B', 'target': 'D' },
		  'rdc': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'D', 'target': 'C' }
        }


# fake operation execution 
def call_operation(ope, fact):
	pass

def call_rel_operation(ope, fact, node):
	pass


class Rete(object):
	"""
		Parent cless for RETE objects.
	"""
	
	def __init__(self, workflow_name):
		self.workflow_name = workflow_name
		self.parents=set()
		self.childs=set()
		self.facts=set()
		self.cond= lambda x: True

	def insert_fact(self, fact):
		if self.cond(fact):
			self.facts = self.facts | set([fact])
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
	
	def __init__(self, workflow_name, type_node):
		super(ReteType, self).__init__(workflow_name)
		if workflow_name not in workflows_input:
			workflows_input[workflow_name] = Rete(workflow_name)
		workflows_input[workflow_name].add_parent(self)
		self.cond= lambda x : facts[x]['type'] == type_node

class ReteStateCond(Rete):
	"""
		Rule condition for nodes.
		Simple as state comparison if no weaving is done.
		Have to consider the state of all facts related to ongoing and ingoing relations if weaving is done.
	"""

	def __init__(self, workflow_name, state, step, childs):
		super(ReteStateCond, self).__init__(workflow_name)
		self.state = state
		self.step = step
		self.reterelactions = set()
		self.cond= lambda x : (facts[x]['state'] == state) and (facts[x]['step'] == (step - 1))
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
			self.facts = self.facts | set([fact])
			# insert into parent only if all facts related to ingoing or outgoing relations have reached the expected state for weaving.
			if all([ not len(set(facts[fact][relaction.direction]) - relaction.facts) for relaction in self.reterelactions ]):
				for parent in self.parents:
					parent.insert_fact(fact) 


class ReteRelCond(Rete):
	"""
		Rule condition for relations.
		Simple as state comparison if no weaving is done.
		Have to consider the state of all facts related to ongoing and ingoing relations if weaving is done.
	"""
	
	def __init__(self, workflow_name, direction, find_step, wait_step, step, childs):
		self.find_step = find_step
		self.wait_step = wait_step
		self.direction = direction
		self.step = step

		self.side = {'out': { 'weaving': 'source_weaving', 'find_step': 'source', 'wait_step': 'target'},
				     'in':  { 'weaving': 'target_weaving', 'find_step': 'target', 'wait_step': 'source'}
				    }[self.direction]

		super(ReteRelCond, self).__init__(workflow_name)
		
		self.cond= lambda r : (facts[r][self.side['weaving']] == (self.step - 1)) \
							  and (self.find_step == None or facts[facts[r][self.side['find_step']]]['step'] == (self.find_step - 1)) \
							  and (self.wait_step == None or facts[facts[r][self.side['wait_step']]]['step'] >= (self.wait_step - 1))
		for child in childs:
			child.add_parent(self)


	def __str__(self):
		return "ReteRelCond(" + self.direction + ", " + "find_step = " + str(self.find_step)  + ", " + "wait_step: = " + str(self.wait_step) + ", " + "rel_step: = " + str(self.step) + ")"

	def insert_fact(self, fact):
			
		if self.cond(fact):
			#print "ReteRelCond OK =====> Fact = " + fact + " : " + str(facts[fact])
			#print "ReteRelCond OK =====> Source = " + facts[fact]['source'] + " : " + str(facts[facts[fact]['source']])
			self.facts = self.facts | set([fact])
			for parent in self.parents:
				parent.insert_fact(fact) 



class ReteAction(Rete):
	"""
		Rule action part for nodes.
	"""
	
	def __init__(self, workflow_name, actions, step, childs):
		super(ReteAction, self).__init__(workflow_name)
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
		if self.set_state is not None:
			facts[fact]['state'] = self.set_state
			print fact + ".state = " + self.set_state
		# A new step in the workflow is reached for the fact
		#print "Fact = " + fact + " : " + str(facts[fact])
		facts[fact]['step'] = self.step
		self.facts = self.facts | set([fact])
		# Action impacts current fact and potentially each fact related to ingoing or outgoing relations.
		workflows_input[self.workflow_name].insert_fact(fact)
		for r in facts[fact]['in']:
			workflows_input[self.workflow_name].insert_fact(r)
		for r in facts[fact]['out']:
			workflows_input[self.workflow_name].insert_fact(r)

	def __str__(self):
		return "ReteAction( actions = " + str(self.actions)  + ", " + "step: = " + str(self.step) + ")"



class ReteRelAction(Rete):
	"""
		Rule action part for relations.
		The fact on weach on which the operation will be executed (source or target) depends on the weaving direction.
	"""

	def __init__(self, workflow_name, activity, direction, step, childs, ):
		super(ReteRelAction, self).__init__(workflow_name)
		self.direction = direction
		self.activity = activity
		self.step = step
		self.weavingdir= {'in':'target','out':'source'}[self.direction]
		for child in childs:
			child.add_parent(self)
		
	def insert_fact(self, fact):
		node = facts[fact][self.weavingdir]
		# Execute operation
		call_rel_operation(self.activity, fact, node)
		print node + " : " + fact + "." + str(self.activity)
		# Define the new state for the fact.
		facts[fact]['done'].append(self.activity)
		facts[fact][self.weavingdir + '_weaving'] = self.step
		self.facts = self.facts | set([fact])
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

	# Part of the workflows defined in nodes have to be parsed before the part defined in relations. 
	node_types = [ typename for typename in types_def if ".nodes." in typename ]
	rel_types =  [ typename for typename in types_def if ".relationships." in typename ]

        # Parsing of the part of workflows defined at nodes level.
	for typename in node_types:
		node = types_def[typename]
		if 'workflows' in node:
			node_workflows = node['workflows']
			for workflow_name in node_workflows:
				workflow = node_workflows.get(workflow_name)

				if workflow:
					steps = workflow.get('steps')
					if steps:
						# First condition avaluated in rules is the type of facts.
						rete_type = ReteType(workflow_name, typename)
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
								for actions in activities:
									new_state = actions.get('set_state')
									# First condition to be met for a fact is to be in the state defined at the preceding step. 
									# This condition can be 'weaved' with part of the workflow defined at relationships type level.
									rete_cond = ReteStateCond(workflow_name, old_state, step, [ rete_type ] )
									# Action can be a new state setting for the fact or execution of an operation for the fact. 
									rete_action = ReteAction(workflow_name, actions, step, [ rete_cond ])
									if new_state:
										# A same state can stay during several steps of the workflow 
										# and we have to be able to differentiate them for weaving.
										# So, we register each state and related steps of the workflow.
										states_order[workflow_name][new_state] = step
										old_state = new_state
									step = step + 1

        # Parsing of the part of workflows defined at relationships level. That is where the TOSCA weaving principle is used. 
	for typename in rel_types:
		rel = types_def[typename]
		if 'workflow' in rel:
			# Any reason to use 'workflow' for relationships and 'worflows' for nodes ?
			rel_workflows = rel['workflow']
			for workflow_name in rel_workflows:
				workflow = rel_workflows.get(workflow_name)

				if workflow:
					# First condition avaluated in rules is the type of facts.
					rete_type = ReteType(workflow_name, typename)
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
							rete_relcond = ReteRelCond(workflow_name, direction, find_step, wait_step, step, [ rete_type ])
							# Action on source or target is launched if condition is met.
							rete_relaction = ReteRelAction(workflow_name, action, direction, step, [ rete_relcond ])
							# Here is the key of the weaving process : condition on the status of all facts related to relations 
							# is insertedat the weaving point.
							find_cond.add_reterelaction(rete_relaction)
						
							step = step + 1

def prepare_facts(facts):
	""" 
        	Initializes necessary status information for each fact. 
                Also provides for each node instance the set of outgoing and ingoing relations. 
	"""
	for name, fact in facts.items():
		if ".nodes." in fact['type']:
			fact['state'] = 'none'
			fact['step']  = 0
			fact['out']   = []
			fact['in']    = []
		if ".relationships." in fact['type']:
			fact['done']           = []
			fact['source_weaving'] = 0
			fact['target_weaving'] = 0
			facts[fact['source']]['out'].append(name)
			facts[fact['target']]['in'].append(name)

def main(args=None):
	"""
		Main function to execute example
	"""
	buildRete()
	prepare_facts(facts)

	for fact in facts:
		workflows_input['install'].insert_fact(fact)

"""
	print "==============================="

	prepare_facts(facts)
	for fact in facts:
		workflows_input['uninstall'].insert_fact(fact)
"""	
			
if __name__ == '__main__':
    main()
             
