import sys
import requests
import base64
import time

urlprefix  = "http://localhost:8500/v1/kv/"

def linda_in(key):
  wait = True
  while wait:
    r = requests.get("{}{}".format(urlprefix, key))  
    if r.status_code == 200:
      jsonval = r.json()[0]
      valstr  = jsonval["Value"]
      index   = jsonval["ModifyIndex"] 
      if valstr is None:
        ret = requests.put("{}{}?cas={}".format(urlprefix, key, index), data=str(time.time()))
        wait = not ret.json()
      else:
        timelock = eval(base64.b64decode(valstr))
        newtime = time.time()
        if newtime - timelock > 1:
          ret = requests.put("{}{}?cas={}".format(urlprefix, key, index), data=str(time.time()))
          wait = not ret.json()
        else: 
          ret = requests.get("{}{}?wait=1s&index={}".format(urlprefix, key, index))
    else:
      if r.status_code == 404:
        ret = requests.put("{}{}".format(urlprefix, key), data=str(time.time()))
        wait = not ret.json()

def linda_out(key, value):
   ret = requests.put("{}{}".format(urlprefix, key), data=str(value))
   return ret.json()

def linda_rd(key):
  ret = requests.get("{}{}".format(urlprefix, key))
  val = None
  if ret.status_code == 200:
    valstr = ret.json()[0]["Value"]
    if valstr is not None:
      val = base64.b64decode(valstr)
  return val

