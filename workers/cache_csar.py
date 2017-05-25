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

def download_s3(bucket, csarfile, content_type, model_name):
    """Uploads a given StringIO object to S3. Closes the file after upload.
    Returns the URL for the object uploaded.
    bucket -- The bucket where file needs to be uploaded.
    stringio -- StringIO object which needs to be uploaded.
    content_type -- content type that needs to be set for the S3 object.
    """
    # upload the file after getting the right bucket
    obj = S3Key(bucket)
    obj.name = model_name
    obj.content_type = content_type
    obj.set_contents_from_filename(csarfile)
    obj.set_acl('public-read')

    return obj.generate_url(expires_in=0, query_auth=False)

def parse_csar(csarfile, model_name = None):

  # unzip csarfile
  zip_ref = zipfile.ZipFile(csarfile, 'r')
  csardir="/tmp/{}".format(time.time())
  zip_ref.extractall(csardir)
  zip_ref.close()
  dircontent = os.listdir(csardir)
  if len(dircontent) == 1:
    csardir = '{}/{}'.format(csardir, dircontent[0])

  s3_host = None
  s3_service = linda_rd('S3', categ='catalog/service')
  if isinstance(s3_service, list) and len(s3_service) > 0:
    s3_host   = s3_service[0]['Address']
    s3_key    = linda_rd('s3/admin/access-key-id')
    s3_secret = linda_rd('s3/admin/secret-access-key')
 
    # init s3 with a bucket for the model
    if s3_host is not None:
      conn = S3Connection(s3_key, s3_secret, host=s3_host, port=8080, calling_format=OrdinaryCallingFormat(), is_secure=False)
      model_bucket = conn.create_bucket(model_name)
      upload_s3(model_bucket, csarfile, 'application/zip', model_name)

    # Event to update cache for csars
    linda_out('exec_cache_csar/{}'.format(model_name), time.time())
 

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

def cache_update(model_name, s3_path):
  print "cache update for model {} and path {}".format(model_name, s3_path)
  # Get idata for s3 connection 
  s3_host = None
  s3_service = linda_rd('S3', categ='catalog/service')
  if isinstance(s3_service, list) and len(s3_service) > 0:
    s3_host   = s3_service[0]['Address']
    s3_key    = linda_rd('s3/admin/access-key-id')
    s3_secret = linda_rd('s3/admin/secret-access-key')

    # Get CSAR file for the model
    if s3_host is not None:
      print "s3_hot ok"
      conn = S3Connection(s3_key, s3_secret, host=s3_host, port=8080, calling_format=OrdinaryCallingFormat(), is_secure=False)
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
            res = csar_key.get_contents_to_filename('/tmp/{}'.format(s3key_name))
            print "res = {}".format(res)
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
             

