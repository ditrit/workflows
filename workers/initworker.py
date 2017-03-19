import requests
import base64
import os
import sys
import time

def path_rd(path):
  url = "http://localhost:8500/{}".format(path)
  return requests.get(url)
  
def path_out(path, data=None):
  url = "http://localhost:8500/{}".format(path)
  return requests.put(url, data)
  

def catalog_rd(key):
  ret = path_rd("v1/catalog/{}".format(key))
  value = None
  if ret.status_code == 200:
    value = ret.json()
  return value

def rd(key):
  ret = path_rd("v1/kv/{}".format(key))
  value = None
  if ret.status_code == 200:
    value = base64.b64decode(ret.json()[0]["Value"])
  return value

def rd_raw(key):
  ret = path_rd("v1/kv/{}?raw".format(key))
  value = None
  if ret.status_code == 200:
    value = ret.text
  return value
  
def out(key, value):
  url = "http://localhost:8500/{}{}".format("v1/kv/", key)
  ret = requests.put(url, data=str(value))
  return ret
   
def dl(key):
  url = "http://localhost:8500/{}{}".format("v1/kv/", key)
  ret = requests.delete(url)
  return ret
   
 
def workernodes():
    ret = catalog_rd('nodes')
    nodes = [ node['Node'] for node in ret if node['Node'].startswith("workflow") ]
    return nodes

def getfacts():
    return eval(rd_raw('node_facts'))
    
def myname():
  ret = path_rd("v1/agent/self")
  if ret.status_code == 200:
    value = ret.json()
    return value['Member']['Name']

def reload_me():
  os.system("systemctl restart consul")

def update_watches(workflow_name):
   me = myname()
   workerurl = "workflows/workers/{}".format(me)

   oldval = rd_raw(workerurl)
   if oldval:
     oldnodes = sorted(eval(oldval))
   else:
     oldnodes = []
   currentnodes = sorted(workernodes())

   if oldnodes != currentnodes:
     time.sleep(3)
     nodes = sorted(workernodes())
     if oldnodes != nodes:
   
        out(workerurl, nodes)

        facts = sorted(getfacts())
        myindex = nodes.index(me)
        nbnodes = len(nodes)
        nbfacts = len(facts)
        nbbynode = nbfacts / nbnodes
        delta = nbfacts % nbnodes
        if myindex < delta:
          nbbynode = nbbynode + 1 
   
        numfacts = [(myindex + d + nbnodes * n) % nbfacts for n in range(0, nbbynode) for d in range(0,2)]
        listindex = [(d,n) for n in range(0, nbbynode) for d in range(0,2)]
        myfacts =    [ facts[(myindex + d + nbnodes * n) % nbfacts] for n in range(0, nbbynode) for d in range(0,2)]
        watches =    [ '  {"type": "key","key": "exec-wd/' + workflow_name + '/fact/' + factname + '","handler": "python /usr/local/bin/wd.py ' + factname + ' >> /opt/execs"}' for factname in myfacts]
        watches_def = '{"watches": [\n' + ',\n'.join(watches) + '\n]}'

        with open("/etc/consul.d/watches.json", "w") as fwatches:
          fwatches.write(watches_def)

        reload_me()
      
def update_workers(workflow_name):
  update_watches(workflow_name) 

def main(args=None):
  workflow_name = sys.argv[1] if len(sys.argv) > 1 else None

  if workflow_name is not None:
    update_workers(workflow_name)

if __name__ == '__main__':
    main()
