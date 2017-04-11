import sys
import requests
import base64
import time


""" 
    A very simple Linda interface using Consul as backend. 
    Tuples are defined as 'keys' in the Consul kvstore.

    Generally, the implementation of 'in' removes the tuple in the Space. 
    It is a resiliency problemn if the worker dies.
    Instead, we write a timestamp as value when the tuple is taken and '' (None) when the tuple is released.

    We consider workers shoud take less than 1 second to terminate. 
    After one second, the tuple is released and another worker can take the worker
    Long time locking is achieved using state of facts.

    By default, operations handle the kvstore of Consul, but the 'categ' parameter allow to manage other parts of consul (catallog, health, etc.)
"""

urlprefix  = "http://localhost:8500/v1"


def linda_in(key, categ='kv'):
  """
    Implement the 'in' operator of Linda.
  """
  wait = True
  while wait:
    r = requests.get("{}/{}/{}".format(urlprefix, categ, key))  
    # if the tuple exists, wait until it is released
    if r.status_code == 200:
      jsonval = r.json()[0]
      valstr  = jsonval["Value"]
      index   = jsonval["ModifyIndex"] 
      # if the tuple is released, take it writing a timestamp as value
      if valstr is None:
        ret = requests.put("{}/{}/{}?cas={}".format(urlprefix, categ, key, index), data=str(time.time()))
        wait = not ret.json()
      else:
        # if the tuple is already taken, verify if the delay (1s) is expired
        timelock = eval(base64.b64decode(valstr))
        newtime = time.time()
        # if the delay is expired, take the tuple
        if newtime - timelock > 1:
          ret = requests.put("{}/{}/{}?cas={}".format(urlprefix, categ, key, index), data=str(time.time()))
          wait = not ret.json()
        # if the delay is not expired, wait until the tuple is released
        else: 
          ret = requests.get("{}/{}/{}?wait=1s&index={}".format(urlprefix, categ, key, index))
    else:
      # if the tuple does not exist, juste create it
      if r.status_code == 404:
        ret = requests.put("{}/{}/{}".format(urlprefix, categ, key), data=str(time.time()))
        wait = not ret.json()

def linda_out(key, value, categ='kv'):
  """
    Implement the 'out' operator of Linda.
  """
  # as simple as writing a value
  ret = requests.put("{}/{}/{}".format(urlprefix, categ, key), data=str(value))
  return ret.json()

def linda_rd(key, categ='kv'):
  """
    Implement the 'rd' operator of Linda.
  """
  # as simple as reading a value
  ret = requests.get("{}/{}/{}".format(urlprefix, categ, key))
  val = None
  if ret.status_code == 200:
    if categ == 'kv':
      valstr = ret.json()[0]["Value"]
      if valstr is not None:
        val = base64.b64decode(valstr)
    else:
      val = ret.json()
  return val

def linda_rm(key, categ='kv'):
  """
    Implement 'delete' operator.
  """
  ret = requests.delete("{}/{}/{}".format(urlprefix, categ, key))
  return ret.json()

