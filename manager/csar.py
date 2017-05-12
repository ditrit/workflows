#!/usr/bin/python


from cStringIO import StringIO
from boto.s3.connection import S3Connection
from boto.s3.key import Key as S3Key

from linda import *
from upload import parse_tosca, parse_declarative_workflows, parse_model
from run import prepare_instance, execute_workflow
import os

def upload_s3(file, key_name, content_type, bucket_name):
    """Uploads a given StringIO object to S3. Closes the file after upload.
    Returns the URL for the object uploaded.
    Note: The acl for the file is set as 'public-acl' for the file uploaded.
    Keyword Arguments:
    file -- StringIO object which needs to be uploaded.
    key_name -- key name to be kept in S3.
    content_type -- content type that needs to be set for the S3 object.
    bucket_name -- name of the bucket where file needs to be uploaded.
    """
    AWS_ACCESS_KEY_ID = 'aws-access-key-id'
    AWS_SECRET_ACCESS_KEY = 'aws-secret-access-key'

    # create connection
    conn = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, host=leofs, port=8080)

    # upload the file after getting the right bucket
    bucket = conn.get_bucket(bucket_name)
    obj = S3Key(bucket)
    obj.name = key_name
    obj.content_type = content_type
    obj.set_contents_from_string(file.getvalue())
    obj.set_acl('public-read')

    # close stringio object
    file.close()

    return obj.generate_url(expires_in=0, query_auth=False)

def parse_csar(csardir, model_name = None):
  entry_file = None
  if os.path.isdir(csardir):
    if 'TOSCA-Metadata' in os.listdir(csardir):
      tm_dir = os.path.join(csardir, 'TOSCA-Metadata')
      if os.path.isdir(tm_dir) and 'TOSCA.meta' in os.listdir(tm_dir): 
        tm_file = os.path.join(tm_dir, 'TOSCA.meta')
        if os.path.isfile(tm_file):
          meta = {}
          with open(tm_file, 'r') as f:
            for line in f:
              tokens = line.split(':')
              if len(tokens) == 2:
                meta[tokens[0].strip()] = tokens[1].strip()
          if str(meta.get('CSAR-Version')) == '1.1' and str(meta.get('TOSCA-Meta-File-Version')) == '1.0' and 'Entry-Definitions' in meta.keys():
            entry_file = meta['Entry-Definitions']
          else:
            print "Error in the provided TOSCA meta file inside the CSAR" 
    yamlfiles = [ filename for filename in os.listdir(csardir) if os.path.splitext(filename)[1] in ['.yaml', '.yml'] ]
    if len(yamlfiles) == 1:
      entry_file = yamlfiles[0]
    else:
      print "A uniq yaml file have to be provided at the root of the CSAR if it does not contain a TOSCA-Metadata directory"

    toscayaml = parse_tosca("{}/{}".format(csardir, entry_file))

    if toscayaml is not None:
      parse_declarative_workflows(toscayaml)
      if model_name is not None:
        parse_model(toscayaml, model_name)
    


