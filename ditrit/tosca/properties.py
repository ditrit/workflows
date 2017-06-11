
from tosca.basetypes   import *
from tosca.constraints import *


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
  default = yaml_def.get('default')
  if default is not None:
   default = get_value(default, val['type'])
  val['default'] = default


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
  constraints = parse_constraints(yaml_def.get('constraints'), val['type'])
  val['constraints'] = constraints
  if val['constraints_def'] is not None and val['default'] is not None and constraints(val['default']) == False:
    print "Error : default value '{}' breaks the constraints '{}'".format(val['default'], val['constraints_def'])

  # Entry schema (for list or map types)
  val['entry_schema'] = dict(type=None, constraints=None, constraints_def=None)
  entry = yaml_def.get('entry_schema')
  if isinstance(entry, basestring):
    val['entry_schema']['type'] = entry
  else:
    if isinstance(entry, dict) and 'type' in entry.keys():
      val['entry_schema']['constraints_def'] = entry.get('constraints')
      val['entry_schema']['type'] = entry['type']
      val['entry_schema']['constraints'] = parse_constraints(entry.get('constraints'), entry['type'])


def get_attribute_definitions(attributes_def):
  """
      Parse attributes definition
  """
  attributes = {}
  if isinstance(attributes_def, dict):
    for attr_name, attr_def in attributes_def.items():
      attr_val = {}
      attr_val['name'] = attr_name

      # Common keynames
      get_base_keynames(attr_def, attr_val, attr_name)

      # build value for attributes
      attributes[attr_name] = attr_val

  return attributes


def get_property_definitions(properties_def):
  """
      Parse properties definition
  """
  properties = {}
  if isinstance(properties_def, dict):
    for prop_name, prop_def in properties_def.items():
      prop_val = {}
      prop_val['name'] = prop_name

      # Common keynames
      get_base_keynames(prop_def, prop_val, prop_name)
      
      # Extra keynames
      get_extra_keynames(prop_def, prop_val, prop_name)
      
      # build value for properties
      properties[prop_name] = prop_val

  return properties

def get_parameter_definitions(parameters_def):
  """
      Parse parameters definition
  """
  parameters = {}
  if isinstance(parameters_def, dict):
    for param_name, param_def in paramaters_def.items():
      param_val = {}
      param_val['name'] = param_name

      # Common keynames
      get_base_keynames(param_def, param_val, param_name)
      
      # Extra keynames
      get_extra_keynames(param_def, param_val, param_name)
      
      # build value for properties
      parameters[param_name] = param_val

  return parameters

