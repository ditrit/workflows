#!/usr/bin/python

from flask import Flask
from flask_restplus import Api, Resource, reqparse
from werkzeug.datastructures import FileStorage

from cStringIO import StringIO

from linda import *
from upload import library, model
from run import prepare_instance, execute_workflow
from csar import parse_csar
import os

app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)

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
    parse.add_argument('model', required=True, help="Model name can not be blank")
    args = parse.parse_args()
    csarfile = args['file']
    model_name = args['model']
    stored_file = '/tmp/{}.{}'.format(time.time(),csarfile.filename)
    csarfile.save(stored_file)
    parse_csar(stored_file, model_name)
    return True

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0')

