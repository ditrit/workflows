#!/usr/bin/python


from cStringIO import StringIO
from boto.s3.connection import S3Connection
from boto.s3.connection import OrdinaryCallingFormat
from boto.s3.key import Key as S3Key

from linda import *
import os
import zipfile
import sys
import json
import base64
import time
import threading
import random

def cache_update(model_name, s3_path):
  print "cache update for model {} and path {}".format(model_name, s3_path)
  # Get idata for s3 connection 
  s3_host = None
  s3_service = linda_rd('S3', categ='catalog/service')
  if isinstance(s3_service, list) and len(s3_service) > 0:
    s3_host   = s3_service[0]['Address']
    s3_port   = s3_service[0]['ServicePort']
    s3_key    = linda_rd('s3/admin/access-key-id')
    s3_secret = linda_rd('s3/admin/secret-access-key')

    # Get CSAR file for the model
    if s3_host is not None:
      print "s3_hot ok"
      conn = S3Connection(s3_key, s3_secret, host=s3_host, port=s3_port, calling_format=OrdinaryCallingFormat(), is_secure=False)
      if conn is not None:
        print "conn OK"
        model_bucket = conn.get_bucket(model_name)
        s3key_name = '{}.csar.zip'.format(model_name)
        if model_bucket is not None:
          print "bucket ok"
          for key in model_bucket.list():
             print "{name}\t{size}".format(name = key.name, size = key.size)
          csar_key = model_bucket.get_key(s3key_name)
          print "csar_key_name = {}".format(s3key_name)
          if csar_key is not None:
            csar_zip_path = '/tmp/{}'.format(s3key_name)
            res = csar_key.get_contents_to_filename(csar_zip_path)
            print "res = {}".format(res)
            zip_ref = zipfile.ZipFile(csar_zip_path, 'r')
            csardir="/var/local/{}".format(model_name)
            zip_ref.extractall(csardir)

          else:
            print "Key {} does not exist in the bucket {}".format(model_name, s3_keyname)
        else:
          print "Bucket {} does not exist".format(model_name)
      else:
        print "Connection to S3 failed"

def main(args=None):

  watch_input = sys.stdin.readlines()
  if type(watch_input) is not list or len(watch_input) != 1:
    return
  try:
    print "\n>>>>>>>>>>>>>>>>>> exec_cache_csar: {}".format(watch_input)
    list_input = eval(watch_input[0])
  except:
    return
  if type(list_input) is not list:
    print "Format error for the event sent to oet : {}".format(watch_input)
    return
  for event_data in list_input:
    key = event_data.get('Key')
    val = event_data.get('Value')
    if key is not None:
      key_args = key.split('/')
      model_name    = key_args[1]
      print "model_name = {}".format(model_name)
      if val is not None:
        s3_path = base64.b64decode(val)
        print "s3_path = {}".format(s3_path)
        t = threading.Thread( target=cache_update, args =(model_name, s3_path) )
        t.start()

if __name__ == '__main__':
    main()
             

