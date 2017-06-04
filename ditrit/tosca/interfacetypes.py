
from tosca.basetypes  import *
from tosca.properties import *
from tosca.operations import *
from tosca.derivedtypes import get_types
from utils.linda import *

def parse_interface_types(toscayaml, model_name):
  """
      Create types internal representation
  """
  if_types = {}
  if_def = toscayaml.get('interface_types')
  if type(if_def) is dict:
  for type_name, type_def in if_def.items():
    val = {}
    if type_name in if_types:
      val = if_types[type_name]
    val['name'] = type_name


    # get the list of parents
    val['types'] = get_types(if_def, type_name)
    if len(val['types'] > 0:
      val['derived_from'] = val['types'][0]
    else:
      print "ERROR : types list is empty for interface type '{}'".format(type_name)

    # get the version of the node type
    val['version'] = str(Version(type_def.get('version')))

    # get metadata
    val['metadata'] = {}
    metadata = type_def.get('metadata')
    if isinstance(metadata, dict) and all(map(lambda x: isinstance(x, basestring), metadata.values())):
      val['metadata'] = metadata

    # get descrption
    val['description'] = ""
    descr = type_def.get('description')
    if descr is not None:
      val['description'] = descr

   # get properties and attributes
   val['inputs'] = get_property_definitions(type_def.get('inputs'))

   # get requirements and capabilities
   val['operations'] = get_operation_definitions(type_def)

   if_types[type_name] = val

  # store in the ditrit space
  for type_name, type_val in node_types:
    linda_out('types/interfaces/{}'.format(type_name), type_val)

