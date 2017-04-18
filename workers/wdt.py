#!/usr/bin/python

import os
import sys
import json
import base64
import time
from linda import *
import threading

def call_operation(fact_id, operation_name):
  """
    fake function to call_operation
  """
  print "READY FOR OPERATION : {}.{}".format(fact_id, operation_name)
  time.sleep(2)
  linda_out("operation/{}/{}".format(fact_id, operation_name), True)

def get_fact(fact_id):
  """
    read a fact from the Space 
  """
  f = linda_rd("Fact/{}".format(fact_id)) 
  if f:
    return eval(f)
  else:
    return None 
          
def set_fact(fact_id, fact_def):
  """
    write a fact into the Space
  """
  f = linda_out("Fact/{}".format(fact_id), fact_def) 

def insert_fact(workflow_name, model_name, instance_name, fact_name, fact_idx):

  newtime = time.time()

  # change tracking
  rete_changed = fact_changed = False
  ret = 'nothing'
  fact_id = '{}/{}/{}/{}'.format(model_name, instance_name, fact_name, fact_idx)
  keywait = 'ready/{}/{}'.format(workflow_name, fact_id)

  # Use linda in to lock other workers waiting on the current fact
  linda_in(keywait)

  # read the fact
  fact_def = get_fact(fact_id)

  # read the step of the workflow reached by the fact
  step =  fact_def['step']
  newstep = step + 1

  # if the fact reached the end of the workflow, do nothing
  if fact_def['state'] == 'ended':
    linda_rm("exec_wdt/{}/{}".format(workflow_name, fact_id))
  else:
    # if not, read the RETE rule matching to the node type and the step 
    keyrete = "ReteNode/{}/{}/{}".format(workflow_name, fact_def['type'], newstep)
    r = linda_rd(keyrete)
    rete = eval(r)

    # register the fact into the rete rule if not already
    if fact_id not in rete['facts']:
      rete['facts'].append(fact_id)
      rete_changed = True

    # Now, handle weaving condition for relationships
    ok = True
    weaving_opes=[]
    # for ingoing and outgoing relationships on the current node
    for direction in ['in', 'out']:
      for typename, weaving in rete['weaving'][direction].items():
        operation = weaving['activity']
        # Check condition and state of the node at the other end of the relationship
        for other_id in fact_def[direction][typename]:
          # if the other node is not alreadey registered in the weaving part of the rule, check it
          if other_id not in weaving['facts']:
            other_def = get_fact(other_id)
            wait_step =  weaving['wait_step']
            # If the weaving condition is fulfilled, register the other node as weaved
            if wait_step is None or other_def['step'] >= wait_step - 1:
              # is operation already launched ?
              state_operation = linda_rd("operation/{}/{}".format(operation, fact_id))
              if state_operation is None:
                # operation has not been launched
                linda_out("exec_oet/{}/{}".format(operation, fact_id), newtime)
                # launch the operation
                #call_operation(operation, fact_id)
                ok = False
              else:
                # is operation ended ?
                if eval(state_operation) == True:
                  # operation is ended
                  weaving['facts'].append(other_id)
                  weaving_opes.append((operation,fact_id))
                  rete_changed = True
                else:
                  ok = False
            else:
              ok = False
          # allow workflow execution for the other name 
          linda_out("exec_wdt/{}/{}".format(workflow_name, other_id), newtime)

    # Now, if all conditions (on the node and weaving) are satisfied, update fact state and execute operation
    operation = None
    if ok == True:
      # is there an operation to be executed ?
      operation = rete['call_operation']
      if operation:
        ok = False
        # is operation already launched ?
        state_operation = linda_rd("operation/{}/{}".format(operation, fact_id))
        if state_operation is None:
          # operation has not been launched
          exec_oet = linda_rd("exec_oet/{}/{}".format(operation, fact_id))
          if exec_oet is None:
            linda_out("exec_oet/{}/{}".format(operation, fact_id), newtime)
          # launch the operation
          #call_operation(operation, fact_id)
        else:
          # is operation ended ?
          if eval(state_operation) == True:
            # operation is ended
            ok = True
    if ok == True:
      # newstep is reached
      fact_def['step'] = newstep
      fact_changed = True
      # update the state of the fact
      new_state = rete['set_state']
      if new_state:
        fact_def['state'] = new_state
        print "==> {}.state = {}".format(fact_id, new_state)

    # update fact into the Space
    if fact_changed == True:
      set_fact(fact_id, fact_def)
      if operation is not None:
            linda_rm("operation/{}/{}".format(operation, fact_id))
            linda_rm("exec_oet/{}/{}".format(operation, fact_id))
      ret = 'changed'

    # update the rete rule into the Space
    if rete_changed == True:
      linda_out(keyrete, rete)
      for (ope, f_id) in weaving_opes:
            linda_rm("operation/{}/{}".format(ope, f_id))
            linda_rm("exec_oet/{}/{}".format(ope, f_id))
      ret = 'changed'

    # allow a new workflow execution for the current fact 
    linda_out("exec_wdt/{}/{}".format(workflow_name, fact_id), newtime)

  # release the tuple on the fact, allowing other workers toio take it
  linda_out(keywait, '')
  linda_rm("ready/{}/{}".format(workflow_name, fact_id))

  return ret 

def main(args=None):

  watch_input = sys.stdin.readlines()
  if type(watch_input) is not list or len(watch_input) != 1:
    return
  try:
    list_input = eval(watch_input[0])
  except:
    return
  if type(list_input) is not list:
    print "Format error for the event sent to wdt : {}".format(watch_input)
    return
  for event_data in list_input:
    key = event_data.get('Key')
    if key is not None:
      key_args = key.split('/')
      workflow_name = key_args[1]
      model_name    = key_args[2]
      instance_name = key_args[3]
      fact_name     = key_args[4]
      fact_idx      = key_args[5]
      t = threading.Thread( target=insert_fact, args =(workflow_name,  model_name, instance_name, fact_name, fact_idx) )
      t.start()

if __name__ == '__main__':
    main()
             

