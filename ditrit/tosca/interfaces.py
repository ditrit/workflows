
from tosca.basetypes  import *
from tosca.properties import *
from tosca.operations import *

def get_interface_definitions(interfaces_def, for_template=False):
  """
      Parse interfaces definition
  """
  interfaces = {}
  if isinstance(interfaces_def, dict):

    for if_name, if_def in interfaces_def.items()

      interface_type = None
      inputs = []
      operations = []

      ## TODO : manage namespace to have complete interface name (eg : tosca.interfaces.nodes.lifecycle.Standard)

      # in the case of a Template, get the required interface_type_name
      ## TODO: get the interface type at the type definition level when interface is defined for a type
      interface_type = if_def.get('type')
      if for_template == True and not isinstance(interface_type, basestring):
        print "Error: the name of the interface type is mandatory for interface defined in a template"

      # get property_definitions in case of a type 
      if for_templates == False:
        inputs = get_property_definitions(if_def.get('inputs'))
      else
        ## TODO: get properties 'assignments' in case of a template
	inputs = [] # get_properties_assignments(if_def.get('inputs'))

      # get definition of operations 
      operations = get_operation_definitions(if_def) 
          
      if_val = { 'name': if_name, 'interface_type': interface_type, 'inputs': inputs, 'operations': operations }

      # build value for interface
      interfaces[if_name] = if_val

  return interfaces

