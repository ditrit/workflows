#!/usr/bin/python

import os
import sys

workflows = {
  'tosca.nodes.Root': {
     'install':
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
             { 'set_state': 'end'},
             ]
           }
         }
       },
     'uninstall':
       { 'steps':
         { 'install_sequence':
           { 'activities': [
             { 'set_state': 'stopping'},
             { 'call_operation': 'tosca.interfaces.node.lifecycle.Standard.stop' },
             { 'set_state': 'deleting'},
             { 'call_operation': 'tosca.interfaces.node.lifecycle.Standard.delete' },
             { 'set_state': 'deleted'}]
           }
         }
       }
     },
  'tosca.relationships.ConnectsTo': { 
     'install': { 
       'source_weaving': [
         { 'after': 'configuring',
#           'wait_target': 'created',
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
           'activity': 'tosca.interfaces.relationships.Configure.add_source' } ] }}
  }

facts = { 'A': 	{ 'type': 'tosca.nodes.Root', 'state': 'none', 'step':0, 'out': ['rab','rac'], 'in': []},
          'B': 	{ 'type': 'tosca.nodes.Root', 'state': 'none', 'step':0, 'out': ['rbd'], 'in': ['rab']},
          'C': 	{ 'type': 'tosca.nodes.Root', 'state': 'none', 'step':0, 'out': [], 'in': ['rac', 'rdc']},
          'D': 	{ 'type': 'tosca.nodes.Root', 'state': 'none', 'step':0, 'out': ['rdc'], 'in': ['rbd']},
		  'rab': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'B', 'done': [], 'source_weaving': 0, 'target_weaving': 0 },
		  'rac': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'C', 'done': [], 'source_weaving': 0, 'target_weaving': 0 },
		  'rbd': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'B', 'target': 'D', 'done': [], 'source_weaving': 0, 'target_weaving': 0 },
		  'rdc': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'D', 'target': 'C', 'done': [], 'source_weaving': 0, 'target_weaving': 0 }
        }


def call_operation(ope, fact):
	pass

def call_rel_operation(ope, fact, node):
	pass

class Rete(object):
	
	def __init__(self):
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

rete_input = Rete()
rete_states = []
states_order = {'none': 0 }

class ReteType(Rete):
	
	def __init__(self, type_node):
		super(ReteType, self).__init__()
		rete_input.add_parent(self)
		self.cond= lambda x : facts[x]['type'] == type_node


class ReteStateCond(Rete):

	def __init__(self, state, step, childs):
		super(ReteStateCond, self).__init__()
		self.state = state
		self.step = step
		self.reterelactions = set()
		self.cond= lambda x : (facts[x]['state'] == state) and (facts[x]['step'] == (step - 1))
		for child in childs:
			child.add_parent(self)
		rete_states.append(self)
		#print str(self)
	
	def add_reterelaction(self, reterelaction):
		self.reterelactions = self.reterelactions | set( [ reterelaction ])
		
	def __str__(self):
			return "ReteStateCond(state = " + self.state + ", step = " + str(self.step) + ", relsconds = [" + ",".join(map(str,self.reterelactions)) + "]"

	def insert_fact(self, fact):
		if self.cond(fact):
			self.facts = self.facts | set([fact])
			if all([ not len(set(facts[fact][relaction.direction]) - relaction.facts) for relaction in self.reterelactions ]):
				for parent in self.parents:
					parent.insert_fact(fact) 


class ReteRelCond(Rete):
	
	def __init__(self, direction, find_step, wait_step, step, childs):
		self.find_step = find_step
		self.wait_step = wait_step
		self.direction = direction
		self.step = step

		self.side = {'out': { 'weaving': 'source_weaving', 'find_step': 'source', 'wait_step': 'target'},
				     'in':  { 'weaving': 'target_weaving', 'find_step': 'target', 'wait_step': 'source'}
				    }[self.direction]

		super(ReteRelCond, self).__init__()
		
		self.cond= lambda r : (facts[r][self.side['weaving']] == (self.step - 1)) \
							  and (self.find_step == None or facts[facts[r][self.side['find_step']]]['step'] == (self.find_step - 1)) \
							  and (self.wait_step == None or facts[facts[r][self.side['wait_step']]]['step'] >= (self.wait_step - 1))
		for child in childs:
			child.add_parent(self)


	def __str__(self):
		return "ReteRelCond(" + self.direction + ", " + "find_step = " + str(self.find_step)  + ", " + "wait_step: = " + str(self.wait_step) + ", " + "rel_step: = " + str(self.step) + ")"

	def insert_fact(self, fact):
			
		if self.cond(fact):
			self.facts = self.facts | set([fact])
			for parent in self.parents:
				parent.insert_fact(fact) 



class ReteAction(Rete):
	
	def __init__(self, actions, step, childs):
		super(ReteAction, self).__init__()
		for child in childs:
			child.add_parent(self)

		self.actions= actions
		self.step = step
		self.set_state = self.actions.get('set_state')
				
	def insert_fact(self, fact):
		if 'call_operation' in self.actions:
			call_operation(self.actions['call_operation'], fact)
			print fact + " : " + self.actions['call_operation']
		if self.set_state is not None:
			facts[fact]['state'] = self.set_state
			print fact + ".state = " + self.set_state
		facts[fact]['step'] = self.step
		self.facts = self.facts | set([fact])
		rete_input.insert_fact(fact)
		for r in facts[fact]['in']:
			rete_input.insert_fact(r)
		for r in facts[fact]['out']:
			rete_input.insert_fact(r)

	def __str__(self):
		return "ReteAction( actions = " + str(self.actions)  + ", " + "step: = " + str(self.step) + ")"



class ReteRelAction(Rete):

	def __init__(self, activity, direction, step, childs, ):
		super(ReteRelAction, self).__init__()
		self.direction = direction
		self.activity = activity
		self.step = step
		self.weavingdir= {'in':'target','out':'source'}[self.direction]
		for child in childs:
			child.add_parent(self)
		
	def insert_fact(self, fact):
		node = facts[fact][self.weavingdir]
		call_rel_operation(self.activity, fact, node)
		print node + " : " + fact + "." + str(self.activity)
		facts[fact]['done'].append(self.activity)
		facts[fact][self.weavingdir + '_weaving'] = self.step
		self.facts = self.facts | set([fact])
		rete_input.insert_fact(node)
		rete_input.insert_fact(fact)

	def __str__(self):
		return "ReteRelAction(" + self.direction + ", " + "activity = " + str(self.activity)  + ", " + "step: = " + str(self.step) + ")"


def buildRete():

	node_workflows = workflows['tosca.nodes.Root']
	install_workflow = node_workflows.get('install')

	if install_workflow:
		steps = install_workflow.get('steps')
		if steps:
			rete_type = ReteType('tosca.nodes.Root')
			subworkflow = steps.get('install_sequence')
			if subworkflow:
				activities = subworkflow.get('activities')
				step = 1
				old_state = 'none'
				if activities:
					for actions in activities:
						cond = lambda x : facts[x]['state'] == old_state
						new_state = actions.get('set_state')
						rete_cond = ReteStateCond(old_state, step, [ rete_type ] )
						rete_action = ReteAction(actions, step, [ rete_cond ])
						if new_state:
							states_order[new_state] = step
							old_state = new_state
						step = step + 1

	rel_workflows = workflows['tosca.relationships.ConnectsTo']
	install_workflow = rel_workflows.get('install')

	if install_workflow:
		rete_type = ReteType('tosca.relationships.ConnectsTo')
		for (node_direction, node_weaving) in install_workflow.items():
			step = 1
			if node_direction == 'source_weaving':
				direction, wait, after, before, activity = 'out', 'wait_target', 'after', 'before', 'activity'
			if node_direction == 'target_weaving':
				direction, wait, after, before, activity = 'in', 'after_source', 'after', 'before', 'activity'
			for weave in node_weaving:
				after_state = weave.get(after)
				before_state = weave.get(before)
				wait_state  = weave.get(wait)
				action  = weave.get(activity)
				if after in weave:
					weaving_state = after_state
				if before in weave:
					weaving_state = before_state
				for rete_cond in rete_states:
					if rete_cond.state == weaving_state:
						break
				if before_state:
					find_cond = rete_states[rete_states.index(rete_cond) - 1]
				if after_state:
					find_cond = rete_cond
				find_step = find_cond.step

				wait_step = None
				if wait_state:
					wait_step = states_order[wait_state] + 1

				source_state, target_state = None, None
				rete_relcond = ReteRelCond(direction, find_step, wait_step, step, [ rete_type ])
				rete_relaction = ReteRelAction(action, direction, step, [ rete_relcond ])
				find_cond.add_reterelaction(rete_relaction)
				
				step = step + 1

							
def main(args=None):
	buildRete()

	for fact in facts:
		rete_input.insert_fact(fact)
			
if __name__ == '__main__':
    main()
             
