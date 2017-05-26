#!/usr/bin/python


from cStringIO import StringIO
from boto.s3.connection import S3Connection
from boto.s3.connection import OrdinaryCallingFormat
from boto.s3.key import Key as S3Key

from linda import *
from upload import parse_tosca, parse_declarative_workflows, parse_model
from run import prepare_instance, execute_workflow
import os
import zipfile

def upload_s3(bucket, csarfile, content_type, filename):
    """Uploads a given StringIO object to S3. Closes the file after upload.
    Returns the URL for the object uploaded.
    bucket -- The bucket where file needs to be uploaded.
    stringio -- StringIO object which needs to be uploaded.
    content_type -- content type that needs to be set for the S3 object.
    """
    # upload the file after getting the right bucket
    print ">>>>>>>>>>>>>>>> csarfile = {}".format(csarfile)
    nbbytes_file = os.path.getsize(csarfile)
    print "nbbytes_file = {}".format(nbbytes_file)
    obj = S3Key(bucket)
    obj.name = filename
    obj.content_type = content_type
    nbbytes_s3 = obj.set_contents_from_filename(csarfile)
    print "nbbytes_s3 = {}".format(nbbytes_s3)
    obj.set_acl('public-read-write')

    for key in bucket.list():
       print "{name}\t{size}".format(name = key.name, size = key.size)

    res = obj.get_contents_to_filename("/tmp/test.zip")
    print "res = {}".format(res)


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

  # find the CSAR entry point
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

  # First step of the parsing : yaml 
  toscayaml = None
  if entry_file is not None:
    toscayaml = parse_tosca("{}/{}".format(csardir, entry_file))

  # Second step : parse TOSCA types en topology (model)
  if toscayaml is not None:
    parse_declarative_workflows(toscayaml)
    if model_name is not None:
      parse_model(toscayaml, model_name)
      
  # Get s3 connection data
  s3_host = None
  s3_service = linda_rd('S3', categ='catalog/service')
  if isinstance(s3_service, list) and len(s3_service) > 0:
    s3_host   = s3_service[0]['Address']
    s3_port   = s3_service[0]['ServicePort']
    s3_key    = linda_rd('s3/admin/access-key-id')
    s3_secret = linda_rd('s3/admin/secret-access-key')
 
    # init s3 with a bucket for the model
    if s3_host is not None:
      conn = S3Connection(s3_key, s3_secret, host=s3_host, port=s3_port, calling_format=OrdinaryCallingFormat(), is_secure=False)
      model_bucket = conn.create_bucket(model_name)
      url_s3_csar = upload_s3(model_bucket, csarfile, 'application/zip', '{}.csar.zip'.format(model_name))
      print "url_s3_csar =  {}'".format(url_s3_csar)

    # Event to update cache for csars
    linda_out('exec_cache_csar/{}'.format(model_name), url_s3_csar)
 
   
  


