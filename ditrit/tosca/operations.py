
from tosca.basetypes   import *
from tosca.properties import *

def get_operation_definitions(operations_def, for_template=False):
  """
      Parse interfaces definition
  """
  operations = {}
  if isinstance(operations_def, dict):

    description = ""
    inputs = []
    implementation = ""
    dependencies = []

    for op_name, op_def in operations_def.items()

      # get description
      val = op_def.get('description')
      if val is not None:
        if isinstance(description, basestring):
          description = val 
        else:
          print "Error: the name of the interface type is mandatory for interface defined in a template"

      # get property_definitions in case of a type 
      if for_templates == False:
        inputs = get_property_definitions(op_def.get('inputs'))
      else
        ## TODO: get properties 'assignments' in case of a template
	inputs = [] # get_properties_assignments(op_def.get('inputs'))

      # get implementation
      implementation_def = op_def.get('implementation')) 
      if isinstance(implementation_def, basestring):
        implementation = implementation_def
      else:
        if isinstance(implementation_def, dict):
          implementation = implementation_def.get('primary')
          if not isinstance(implementation, basestring):
            print "Error: primary value for implementation of an operation is mandatory in extended notation"
            implementation = ""
          dependencies_def = implementation_def.get('dependencies')
          if dependencies_def is not None:
            if isinstance(dependencies_def, list) and all(map(lambda x : isinstance(x, basestring), dependencies_def)):
              dependencies = dependencies_def
            else:
              print "Error : dependencies for an operation definition is a list of strings"
          
      op_val = { 'name': op_name, 'description': description, 
                 'inputs': inputs, 'implementation': implementation, 'dependencies': dependencies }

      # build value for interface
      operations[op_name] = op_val

  return operations

