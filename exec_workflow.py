#!/usr/bin/python

import os
import sys
import consulate
import json
from utils import consul_lock

def call_operation(fact_name, operation_name):
	print "EXEC : {}.{}".format(fact_name, operation_name)
	
	

def insert_fact(workflow_name, fact_name):

	
	consul = consulate.Consul()
	session_id = consul.session.create()

	#with consul_lock(consul, session_id, 'locks/{}/{}'.format(workflow_name, fact_name)):
	if True:
		facts = consul.kv.find("Fact/")
		keyfact = "Fact/{}".format(fact_name)
		fact_def = json.loads(facts[keyfact])

		step =  fact_def['step']
		newstep = step + 1

		if fact_def['state'] != 'ended':
			
			keyrete = "ReteNode/{}/{}/{}".format(workflow_name, fact_def['type'], newstep)
			rete = json.loads(consul.kv[keyrete])
		
			rete_changed = fact_changed = False
			if fact_name not in rete['facts']:
				rete['facts'].append(fact_name)
				rete_changed = True
		
			ok = True
			for direction in ['in', 'out']:
				for typename, weaving in rete['weaving'][direction].items():
					for other_name in fact_def[direction][typename]:
						if other_name not in weaving['facts']:
							other_def = json.loads(facts["Fact/{}".format(other_name)])
							wait_step =  weaving['wait_step']
							if wait_step is None or other_def['step'] >= wait_step - 1:
								weaving['facts'].append(other_name)
								rete_changed = True
								call_operation(fact_name, weaving['activity'])
							else:
								ok = False
		
			if ok == True:
				fact_def['step'] = newstep
				fact_changed = True
				new_state = rete['set_state']
				if new_state:
					fact_def['state'] = new_state
					print "==> {}.state = {}".format(fact_name, new_state)
				operation = rete['call_operation']
				if operation:
					call_operation(fact_name, operation)
		
			if fact_changed == True:
				consul.kv[keyfact] = fact_def
			if rete_changed == True:
				consul.kv[keyrete] = rete
						
	session_ended = consul.session.destroy(session_id)
	if session_ended == False:
		print "Session non terminee"

def main(args=None):

	print "TOSCA parsing"
	workflow_name = sys.argv[1] if len(sys.argv) > 1 else None
	fact_name     = sys.argv[2] if len(sys.argv) > 2 else None
	
	insert_fact(workflow_name, fact_name)
			
if __name__ == '__main__':
    main()
             

