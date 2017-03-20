#!/usr/bin/python

import os
import sys
import json
import base64
import time
from linda import *

def call_operation(fact_name, operation_name):
  """
    fake function to call_operation
  """
  print "EXEC : {}.{}".format(fact_name, operation_name)

def get_fact(fact_name):
  """
    read a fact from the Space 
  """
  f = linda_rd("Fact/{}".format(fact_name)) 
  if f:
    return eval(f)
  else:
    return None 
          
def set_fact(fact_name, fact_def):
  """
    write a fact into the Space
  """
  f = linda_out("Fact/{}".format(fact_name), fact_def) 

def insert_fact(workflow_name, fact_name):

  newtime = time.time()

  # change tracking
  rete_changed = fact_changed = False
  ret = 'nothing'
  keywait = 'ready/{}/{}'.format(workflow_name, fact_name)

  # Use linda in to lock other workers waiting on the current fact
  linda_in(keywait)

  # read the fact
  fact_def = get_fact(fact_name)

  # read the step of the workflow reached by the fact
  step =  fact_def['step']
  newstep = step + 1

  # if the fact reached the end of the workflow, do nothing
  if fact_def['state'] != 'ended':
    # if not, read the RETE rule matching to the node type and the step 
    keyrete = "ReteNode/{}/{}/{}".format(workflow_name, fact_def['type'], newstep)
    r = linda_rd(keyrete)
    rete = eval(r)
		
    # register the fact into the rete rule if not already
    if fact_name not in rete['facts']:
      rete['facts'].append(fact_name)
      rete_changed = True
		
    # Now, handle weaving condition for relationships
    ok = True
    # for ingoing and outgoing relationships on the current node
    for direction in ['in', 'out']:
      for typename, weaving in rete['weaving'][direction].items():
        # Check condition and state of the node at the other end of the relationship
        for other_name in fact_def[direction][typename]:
          # if the other node is not alreadey registered in the weaving part of the rule, check it
          if other_name not in weaving['facts']:
            other_def = get_fact(other_name)
            wait_step =  weaving['wait_step']
            # If the weaving condition is fulfilled, register the other node as weaved
            if wait_step is None or other_def['step'] >= wait_step - 1:
              weaving['facts'].append(other_name)
              rete_changed = True
              # call the weaving condition
              call_operation(fact_name, weaving['activity'])
            else:
              ok = False
          # allow workflow execution for the other name 
          linda_out("exec-wd/{}/fact/{}".format(workflow_name, other_name), newtime)
		
    # Now, if all conditions (on the node and weaving) are satisfied, update fact state and execute operation
    if ok == True:
      # newstep is reached
      fact_def['step'] = newstep
      fact_changed = True
      # update the state of the fact
      new_state = rete['set_state']
      if new_state:
        fact_def['state'] = new_state
        print "==> {}.state = {}".format(fact_name, new_state)
      # execute operation of needed 
      operation = rete['call_operation']
      if operation:
        call_operation(fact_name, operation)

    # update fact into the Space
    if fact_changed == True:
      set_fact(fact_name, fact_def)
      ret = 'changed'

    # update the rete rule into the Space
    if rete_changed == True:
      linda_out(keyrete, rete)
      ret = 'changed'

    # allow a new workflow execution for the current fact 
    linda_out("exec-wd/{}/fact/{}".format(workflow_name, fact_name), newtime)
	
  # release the tuple on the fact, allowing other workers toio take it
  linda_out(keywait, '')

  return ret 

def main(args=None):
        # Read parameters (if used by cli)
        workflow_name = sys.argv[1] if len(sys.argv) > 1 else None
        fact_name = sys.argv[2] if len(sys.argv) > 2 else None

        if workflow_name and fact_name:
          insert_fact(workflow_name, fact_name)
        else:
          # read parameters on stdin if launched by the Space (consul watch)
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
             

