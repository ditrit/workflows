import requests
import base64
import os
import sys
import time
from linda import *

def workernodes():
  """ 
      'workernodes' function return the set of workflow workers which are alive.
      A node is considered alive if it is an active member of the Consul cluster 
      and its 'serfHealth' status is 'passing'.
  """
  ret = linda_rd('nodes', categ='catalog')
  nodes = [ node['Node'] for node in ret if node['Node'].startswith("workflow") ]
  healthy_nodes = []
  for node in nodes:
    health = linda_rd('node/{}'.format(node), categ='health')
    ok = True
    for ele in health:
       if ele['CheckID'] == 'serfHealth' and ele['Status'] != 'passing':
         ok = False
    if ok:
      healthy_nodes.append(node)
  return healthy_nodes

def getfacts():
  """ 
      get_facts simply returns the set of facts for the workflow 
  """ 
  return eval(linda_rd('node_facts'))
    
def myname():
  """
      returns the name of the current worker
  """
  val = linda_rd("self", categ="agent")
  if val:
    return val['Member']['Name']
  else:
    return None

def reload_me():
  """
      reload the consul agent configuraiton
  """
  os.system("systemctl restart consul")

def update_watches(workflow_name):
  """
     'update_watches' Updates the Consul configuration of watches 
     to balance the load in case the set of active workers changed.
     It provides resiliency and high availibility.
     Balancing is based on facts assignement to nodes using watches :
	- each fact can be consumed by two diffetent workers at a time 
        - fact assignements is recomputed each time the set of active workers has changed. 
  """
  me = myname()
  workerurl = "workflows/workers/{}/{}".format(me, workflow_name)

  # Last known set of active workers
  oldval = linda_rd(workerurl)
  if oldval:
     oldnodes = sorted(eval(oldval))
  else:
     oldnodes = []

  # Current set of active workers
  currentnodes = sorted(workernodes())

  # Do nothing if nothing changed
  if oldnodes != currentnodes:
    # If something changed, wait 3 second and reverify (do not react if something like a reloading of the configuraiton occurs).
     time.sleep(3)
     nodes = sorted(workernodes())
     if oldnodes != nodes:
   
        linda_out(workerurl, nodes)

        facts = sorted(getfacts())
        myindex = nodes.index(me)
        nbnodes = len(nodes)
        nbfacts = len(facts)
        nbbynode = nbfacts / nbnodes
        delta = nbfacts % nbnodes
        if myindex < delta:
          nbbynode = nbbynode + 1 

        # Compute the list of facts to be assigned to the current worker
        myfacts =    [ facts[(myindex + d + nbnodes * n) % nbfacts] for n in range(0, nbbynode) for d in range(0,2)]

        # Define watches definition for the facts to be assigned 
        watches =    [ '  {"type": "key","key": "exec-wd/' + workflow_name + '/fact/' + factname + '","handler": "python /usr/local/bin/wd.py ' + factname + ' >> /opt/execs"}' for factname in myfacts]
        watches_def = '{"watches": [\n' + ',\n'.join(watches) + '\n]}'

        # Write watches configuration for the local Consul agent
        with open("/etc/consul.d/watches.json", "w") as fwatches:
          fwatches.write(watches_def)

        # reload Consul configuration
        reload_me()
      
def update_workers(workflow_name):
  update_watches(workflow_name) 

def main(args=None):
  workflow_name = sys.argv[1] if len(sys.argv) > 1 else None

  if workflow_name is not None:
    update_workers(workflow_name)

if __name__ == '__main__':
    main()
