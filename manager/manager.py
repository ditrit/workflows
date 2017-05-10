#!/usr/bin/python

from flask import Flask
from flask_restplus import Api, Resource, reqparse
from werkzeug.datastructures import FileStorage

from cStringIO import StringIO
from boto.s3.connection import S3Connection
from boto.s3.key import Key as S3Key

from linda import *
from upload import library, model
from run import prepare_instance, execute_workflow
from csar import parse_csar
import zipfile
import os

app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)

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

@api.route('/library')
class Library(Resource):
  def get(self):
    nt_names = linda_rd('node_type_names')
    if nt_names is None:
      nt_names = []
    rt_names = linda_rd('relationship_type_names')
    if rt_names is None:
      rt_names = []
    return {'node_names': nt_names, 'relationship_names': rt_names }

  
  def put_into_s3(self):
    parse = reqparse.RequestParser()
    parse.add_argument('file', type=FileStorage, location='files', required=True)
    args = parse.parse_args()
    toscafile = args['file']
    imageFile = StringIO()
    toscafile.save(imageFile)
    keyname = '{0}.{1}'.format('toscatypes','yaml')
    content_type = application/x-yaml
    bucket_name  = 'mon_appli'
    file_url = upload_s3(imageFile, key_name, content_type, bucket_name) 
    #library(filename)
    return { 'file_url': file_url }

  def put(self):
    parse = reqparse.RequestParser()
    parse.add_argument('file', type=FileStorage, location='files', required=True)
    args = parse.parse_args()
    toscafile = args['file']
    storedFile = '/tmp/{}.{}'.format(time.time(),toscafile.filename)
    toscafile.save(storedFile)
    library(storedFile)
    return self.get()


@api.route('/model')
class ToscaModel(Resource):
  def get(self):
    model_names = linda_rd('Model')
    if model_names is None:
      model_names = []
    return { 'model_names': model_names }
  
  def put(self):
    parse = reqparse.RequestParser()
    parse.add_argument('file', type=FileStorage, location='files', required=True, help="Model have to be valid TOSCA file")
    parse.add_argument('name', required=True, help="Model name can not be blank")
    args = parse.parse_args()
    modelfile = args['file']
    modelname = args['name']
    storedFile = '/tmp/{}.{}.yaml'.format(time.time(),modelfile.filename)
    modelfile.save(storedFile)
    model(storedFile, modelname)
    return self.get()

@api.route('/instance')
class Instance(Resource):
  def get(self):
    parse = reqparse.RequestParser()
    parse.add_argument('model', required=True, help="Model name can not be blank")
    args = parse.parse_args()
    model_name = args['model']
    instance_names = linda_rd('Instance/{}'.format(model_name))
    if instance_names is None:
      instance_names = []
    return { 'model_name': model_name, 'instance_names': instance_names }
  
  def put(self):
    parse = reqparse.RequestParser()
    parse.add_argument('model', required=True, help="Model name can not be blank")
    parse.add_argument('name', required=True, help="Instance name can not be blank")
    args = parse.parse_args()
    model_name = args['model']
    instance_name = args['name']
    prepare_instance(model_name, instance_name)
    return self.get()

@api.route('/exec')
class ExecWorkflow(Resource):
  def put(self):
    parse = reqparse.RequestParser()
    parse.add_argument('workflow', required=True, help="Workflow name can not be blank")
    parse.add_argument('model', required=True, help="Model name can not be blank")
    parse.add_argument('instance', required=True, help="Instance name can not be blank")
    args = parse.parse_args()
    workflow_name = args['workflow']
    model_name = args['model']
    instance_name = args['instance']
    execute_workflow(workflow_name, model_name, instance_name)
    return True

@api.route('/csar')
class CSAR(Resource):
  def put(self):
    parse = reqparse.RequestParser()
    parse.add_argument('file', type=FileStorage, location='files', required=True, help="The file must be a valid CSAR archive")
    args = parse.parse_args()
    csarfile = args['file']
    storedFile = '/tmp/{}.{}'.format(time.time(),csarfile.filename)
    csarfile.save(storedFile)
    zip_ref = zipfile.ZipFile(storedFile, 'r')
    tmpdir="/tmp/{}".format(time.time())
    zip_ref.extractall(tmpdir)
    zip_ref.close()
    dircontent = os.listdir(tmpdir)
    if len(dircontent) == 1: 
      parse_csar('{}/{}'.format(tmpdir, dircentent[0])
    else:
      parse_csar(tmpdir)
    return True

if __name__ == '__main__':
  app.run(debug=True, host=0.0.0.0)

