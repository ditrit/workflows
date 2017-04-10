#!/usr/bin/python

import os
import sys
import copy
from tosca_template import ToscaTemplate
from linda import *



def all_index(numlist):
  if isinstance(numlist, list):
    if len(numlist) == 0:
      return [] 
    nb = eval(numlist[0])
    if isinstance(nb, int):
      if len(numlist) == 1:
        return range(0, nb) 
      res = []
      for n in range(0, nb):
        res = res + [ "{}/{}".format(n, suffix) for suffix in all_index(numlist[1:]) ] 
      return res 
  return []

def prepare_instance(model_name, instance_name):
  """
        Instanciate a model
  """
  facts = {}
  model2facts = {}
  model_keys_str = linda_rd("Model/{}/keys".format(model_name))
  if model_keys_str is not None:
    model_keys = eval(model_keys_str)
    if type(model_keys) == list:
      for model_key in model_keys:
        model2facts[model_key] = []
        model_def_str = linda_rd("Model/{}".format(model_key))
        if model_def_str is not None:
          model_def = eval(model_def_str)
          if type(model_def) is dict:
            name =     model_def['name']
            idx_path = model_def['scalability_path']
            idx_list = str(idx_path).split("/")
            out_hostedOn = model_def['out']['tosca.relationships.HostedOn']
            if len(out_hostedOn) > 1:
              print "Erreur : noeud hoste sur plusieurs noeuds"
            else:
              for idx in all_index(idx_list):
                fact_def = copy.deepcopy(model_def)
                fact_key = "{}/{}/{}/{}".format(model_name, instance_name, name, idx)
                if len(out_hostedOn) == 1:
                  parent_model = out_hostedOn[0]
                  parent_name  = parent_model.split('/')[1]
                  last = idx.rfind('/')
                  if last > -1:
                    parent_idx = idx[0:last]
                    fact_def['fact'] = fact_key
                    fact_def['out']['tosca.relationships.HostedOn'] = ["{}/{}/{}/{}".format(model_name, instance_name, parent_name, parent_idx)]
                fact_def['in']['tosca.relationships.HostedOn']   = [] 
                fact_def['in']['tosca.relationships.ConnectsTo'] = [] 
                fact_def['in']['tosca.relationships.DependsOn']  = [] 
                facts[fact_key] = fact_def
                model2facts[model_key].append(fact_key)

      for fact_key, fact_def in facts.items():
        # Compute 'in' side of 'hostedOn' relationships
        hostedOn = fact_def['out']['tosca.relationships.HostedOn'] 
        if len(hostedOn) == 1:
          host_key = hostedOn[0] 
          facts[host_key]['in']['tosca.relationships.HostedOn'].append(fact_key)
        # Compute 'connectsTo' relationships
        connectsTo = fact_def['out']['tosca.relationships.ConnectsTo']
        connected_facts = reduce(lambda x, y : x + y, [ model2facts[model_key] for model_key in connectsTo ], [] )
        fact_def['out']['tosca.relationships.ConnectsTo'] = connected_facts
        for connected_fact in connected_facts:
          facts[connected_fact]['in']['tosca.relationships.ConnectsTo'].append(fact_key)
        # Compute 'dependsOn' relationships
        dependsOn = fact_def['out']['tosca.relationships.DependsOn']
        dependent_facts = reduce(lambda x, y : x + y, [ model2facts[model_key] for model_key in dependsOn ], [] )
        fact_def['out']['tosca.relationships.DependsOn'] = dependent_facts
        for dependent_fact in dependent_facts:
          facts[dependent_fact]['in']['tosca.relationships.DependsOn'].append(fact_key)

      for fact_key, fact_def in facts.items():
        linda_out("Fact/{}".format(fact_key), fact_def)
      linda_out("Fact/{}/{}/keys".format(model_name, instance_name), facts.keys())

def main(args=None):
  """
    Run a workflow for an instance of model 
  """

  print "RUN instance"
  command = sys.argv[1] if len(sys.argv) > 1 else None
  arg2 = sys.argv[2] if len(sys.argv) > 2 else None
  arg3 = sys.argv[3] if len(sys.argv) > 3 else None
  toscayaml = {}

  if command == 'instanciate':
    model_name    = arg2
    instance_name = arg3
    if model_name is not None and instance_name is not None:
      if linda_rd("instance/{}/{}".format(model_name, instance_name)) is None:
        if linda_rd("Model/{}".format(model_name)) is not None:
          prepare_instance(model_name, instance_name)
        else:
          print "Model '{}' does not exist !".format(model_name)
    else:
      print "USAGE: python run.py instanciate <model_name> <instance_name>"


  if command == 'defpath': 
    path = arg2
    print defpath(path.split('/'))

if __name__ == '__main__':
  main()
 