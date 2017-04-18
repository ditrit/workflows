#!/usr/bin/python

import os
import sys
import json
import base64
import time
from linda import *
import threading
import random

def exec_code(operation_name, fact_id):
  """
    fake code execution 
  """
  print "EXEC CODE FOR OPERATION : {}.{}".format(fact_id, operation_name)
  time.sleep(random.randint(2,10))
  print "END OF CODE EXECUTION : {}.{}".format(fact_id, operation_name)
  return True

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

def get_operation_state(operation_name, fact_id):
  """
    read a fact from the Space 
  """
  f = linda_rd("operation/{}/{}".format(operation_name, fact_id)) 
  if f:
    return eval(f)
  else:
    return None 
          
def set_operation_state(operation_name, fact_id, value):
  """
    execute an operation
  """
  f = linda_out("operation/{}/{}".format(operation_name, fact_id), value) 

def execute_operation(operation_name, model_name, instance_name, fact_name, fact_idx):

  fact_id = '{}/{}/{}/{}'.format(model_name, instance_name, fact_name, fact_idx)
  newtime = time.time()
  exec_operation = False

  # Use linda in to lock other workers waiting for the current operation
  keywait = 'ready/{}/{}'.format(operation_name, fact_id)
  linda_in(keywait)

  # read operation_state
  operation_val = get_operation_state(operation_name, fact_id)

  if operation_val is None:
    set_operation_state(operation_name, fact_id, newtime)
    exec_operation = True
  else:
    if type(operation_val) is float:
      if newtime - operation_val > 60:
        print "Operation {} for fact {} failed!!!!!!!!".format(operation_name, fact_id)
        fact_def = get_fact(fact_id)
        fact_def['state'] = 'FAILED'
        set_fact(fact_id, fact_def)

  # release lock 
  linda_rm(keywait)

  # execute operation 
  if exec_operation == True:
    res = exec_code(operation_name, fact_id)
    if res == False:
      print "Operation {} for fact {} failed!!!!!!!!".format(operation_name, fact_id)
      fact_def = get_fact(fact_id)
      fact_def['state'] = 'FAILED'
      set_fact(fact_id, fact_def)
    set_operation_state(operation_name, fact_id, True)
    

def main(args=None):

  command = sys.argv[1] if len(sys.argv) > 1 else None
  if command == 'test':
    execute_operation('tosca.interfaces.node.lifecycle.Standard.create','un_model', 'une_instance', 'srvA', '1')
    return

  watch_input = sys.stdin.readlines()
  if type(watch_input) is not list or len(watch_input) != 1:
    return
  try:
    list_input = eval(watch_input[0])
  except:
    return
  if type(list_input) is not list:
    print "Format error for the event sent to oet : {}".format(watch_input)
    return
  for event_data in list_input:
    key = event_data.get('Key')
    if key is not None:
      key_args = key.split('/')
      operation_name= key_args[1]
      model_name    = key_args[2]
      instance_name = key_args[3]
      fact_name     = key_args[4]
      fact_idx      = key_args[5]
      t = threading.Thread( target=execute_operation, args =(operation_name, model_name, instance_name, fact_name, fact_idx) )
      t.start()

if __name__ == '__main__':
    main()
             

