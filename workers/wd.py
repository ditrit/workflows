#!/usr/bin/python

import os
import sys
import json
import base64
import time
from linda import *

def call_operation(fact_name, operation_name):
	print "EXEC : {}.{}".format(fact_name, operation_name)

def get_fact(fact_name):
	f = linda_rd("Fact/{}".format(fact_name)) 
        if f:
	  return eval(f)
        else:
          return None 
          
def set_fact(fact_name, fact_def):
	f = linda_out("Fact/{}".format(fact_name), fact_def) 

def insert_fact(workflow_name, fact_name):

        newtime = time.time()

	rete_changed = fact_changed = False
	ret = 'nothing'
        keywait = 'ready/{}/{}'.format(workflow_name, fact_name)

        linda_in(keywait)

        fact_def = get_fact(fact_name)

	step =  fact_def['step']
	newstep = step + 1

	if fact_def['state'] != 'ended':
		keyrete = "ReteNode/{}/{}/{}".format(workflow_name, fact_def['type'], newstep)
		r = linda_rd(keyrete)
		rete = eval(r)
		
		if fact_name not in rete['facts']:
			rete['facts'].append(fact_name)
			rete_changed = True
		
		ok = True
		for direction in ['in', 'out']:
			for typename, weaving in rete['weaving'][direction].items():
				for other_name in fact_def[direction][typename]:
					if other_name not in weaving['facts']:
						other_def = get_fact(other_name)
						wait_step =  weaving['wait_step']
						if wait_step is None or other_def['step'] >= wait_step - 1:
							weaving['facts'].append(other_name)
							rete_changed = True
							call_operation(fact_name, weaving['activity'])
						else:
							ok = False
					linda_out("exec-wd/{}/fact/{}".format(workflow_name, other_name), newtime)
		
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
			set_fact(fact_name, fact_def)
			ret = 'changed'
		if rete_changed == True:
			linda_out(keyrete, rete)
			ret = 'changed'
		linda_out("exec-wd/{}/fact/{}".format(workflow_name, fact_name), newtime)
	

        linda_out(keywait, '')

	return ret 

def main(args=None):
        workflow_name = sys.argv[1] if len(sys.argv) > 1 else None
        fact_name = sys.argv[2] if len(sys.argv) > 2 else None

        if workflow_name and fact_name:
          insert_fact(workflow_name, fact_name)
        else:
	  watch_input = sys.stdin.readlines()
	  dict_input = eval(watch_input[0])
          keystr = dict_input['Key']

          args = keystr.split("/")
          if len(args) == 4:
            workflow_name = args[1]
            fact_name     = args[3]
            insert_fact(workflow_name, fact_name)

if __name__ == '__main__':
    main()
             

