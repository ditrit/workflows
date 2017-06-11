
from tosca.basetypes   import *
from tosca.constraints import *
from tosca.interfaces import *

def get_requirement_definitions(requirements_def):
  """
      Parse requirements definition
  """
  requirements = {}
  if isinstance(requirements_def, dict):

    for requ_name, requ_def in requirements_def.items():

      # init keywords values 
      capability_type = None
      node_type = None
      relationship_type = None
      occ_min = occ_max = 1
      interface_defs = []

      # get capability type if short notation
      if isinstance(requ_def, basestring):
        capability_type = requ_def

      # if extended grammar is used
      if isinstance(requ_def, dict):

        # get capability type
        capability_type = requ_def.get('capability')
        if not isinstance(capability_type, basestring):
          capability_type = None

        # get node type
        node_type = requ_def.get('node')
        if not isinstance(node, basestring):
          node = None
          print "Error: node type name should be a string"

        # get occurrences
        occ_list = requ_def.get('occurrences')
        if occ_list is None:
          occ_list = [ 1, 1 ]
        if isinstance(occ_list, list): 
          occ_range = Range.from_list(occ_list)
          if isinstance(occ_range, Range):
            occ_min = occ_range.minval
            occ_max = occ_range.maxval
        else:
          print "Syntax Error in occurences definition '{}' for requirement '{}".format(occ_list, requ_name)

        # get relationship type
        relationship = requ_def('relationship')
        if isinstance(relationship, basestring):
          relationship_type = relationship
        if isinstance(relationship, dict):
          relationship_type = relationship.get('type')
          if not isinstance(relationship_type, basestring):
            print "Syntax Error : '{}' should be the name of a valide relationship type".format(relationship_type)
            relationship_type = None
        
        # get interfaces type definition  
        interface_defs = get_interface_definitions(requ_def.get('interfaces'))
          
      requ_val = {'name': requ_name, 'capability_type': capability_type, 'node_type': node_type, 'relationship_type': node_type, 
                  'occurrence_min': occ_min, 'occurrence_max': occ_max, 'interfaces': interface_defs }

      if 'capability_type' is None:
        print "ERROR : capability type is mandatory in requirement definition ( requirement : {} \n= {} )".format(requ_name, requ_val)

      # build value for requirement
      requirements[requ_name] = requ_val


      ### TODO: add 'node_filter' on properties / capabilities on potential target nodes

  return requirements

