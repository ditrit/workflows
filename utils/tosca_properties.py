
from tosca_basetypes   import *
from tosca_constraints import *


def get_base_keynames(yaml_def, val, name):
  """
     Extract from yaml definition the common keynames for properties, attributes and parameters
  """

  # Get the description
  val['description'] = yaml_def.get('description')
  if val['description'] is None:
  val['description'] = ''
  if not isinstance(val['description'], basestring):
    print "Error: description for property '{}' is not a string".format(name)

  # Default status is 'supported'
  status = yaml_def.get('status')
  if status is None:
    status = 'supported'
  if status in [ 'supported', 'unsupported', 'experimental', 'deprecated' ]:
    val['status'] = status
  else:
    print "Error: bad value '{}' for the status of the property '{}'".format(val['status'], name)
    val['status'] = None

  # Type is required
  val['type'] = yaml_def.get('type')
  if val['type'] is None:
    print "Error: property '{}' doesi have a type".format(name)
  if not isinstance(val['type'], basestring):
    print "Error: type for property '{}' is not correct".format(name)

  # Default value
  default = get_value(yaml_def.get('default'), val['type'])
  val['default'] = default
  if constraints(default) == False:
    print "Error : default value '{}' breaks the constraints '{}'".format(default, yaml_def.get('constraint'))


def get_extra_keynames(yaml_def, val, name):
  """
     Extract from yaml definition the additional keynames used by properties and parameters
  """

  # Is the value required ? (yes by default)
  if yaml_def.get('required') in [ 'false', False ]:
    val['required'] = False
  else:
    val['required'] = True

  # Constraints to be applied
  val['constraints_def'] = yaml_def.get('constraints')
  constraints = get_constraints(yaml_def.get('constraints'), val['type'])
  val['constraints'] = constraints

  # Entry schema (for list or map types)
  val['entry_schema'] = dict(type=None, constraints=None, constraints_def=None)
  entry = yal_def.get('entry_schema')
  if isinstance(entry, basestring):
    val['entry_schema']['type'] = entry
  else:
    if isinstance(entry_schema, dict) and 'type' in entry_schema.keys():
      val['entry_schema']['constraints_def'] = entry_schema.get('constraints')
      val['entry_schema']['type'] = entry_schema['type']
      val['entry_schema']['constraints'] = get_constraints(entry_schema.get('constraints'), entry_schema['type'])


def get_attributes_definition(attributes_def):
  """
      Parse attributes definition
  """
  attributes = {}
  if isinstance(attributes_def, dict):
    for attr_name, attr_def in attributes_def.items()
      attr_val['name'] = attr_name

      # Common keynames
      get_base_keynames(attr_def, attr_val, attr_name)

      # build value for attributes
      attributes[attr_name] = attr_val

  return attributes


def get_properties_definition(properties_def):
  """
      Parse properties definition
  """
  properties = {}
  if isinstance(properties_def, dict):
    for prop_name, prop_def in properties_def.items()
      prop_val['name'] = prop_name

      # Common keynames
      get_base_keynames(prop_def, prop_val, prop_name)
      
      # Extra keynames
      get_extra_keynames(prop_def, prop_val, prop_name)
      
      # build value for properties
      properties[prop_name] = prop_val

  return properties

def get_parameters_definition(parameters_def):
  """
      Parse parameters definition
  """
  parameters = {}
  if isinstance(parameters_def, dict):
    for param_name, param_def in paramaters_def.items()
      param_val['name'] = param_name

      # Common keynames
      get_base_keynames(param_def, param_val, param_name)
      
      # Extra keynames
      get_extra_keynames(param_def, param_val, param_name)
      
      # build value for properties
      properties[param_name] = param_val

  return parameters

