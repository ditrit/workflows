
from tosca.basetypes   import *
from tosca.constraints import *
from tosca.interfaces import *

def get_capability_definitions(requirements_def):
  """
      Parse capability definitions
  """
  capabilites = {}
  if isinstance(capabilities_def, dict):

    for capa_name, capa_def in capabilities_def.items()

      # init keywords values 
      capa_type = None
      description = ""
      properties = []
      attributes = []
      valid_source_types = []
      occ_min = occ_max = 1

      # get capability type if short notation
      if isinstance(capa_def, basestring):
        capa_type = capa_def

      # if extended grammar is used
      if isinstance(capa_def, dict)

        # get capability type
        capa_type = capa_def.get('type')
        if not isinstance(capa_type, basestring):
          capa_type = None

        # get capability description
        descr = capa_def.get("description")
        if isinstacne(descr, basestring):
          description = descr

        # get properties and attributes
        val['properties']   = get_property_definitions(capa_def.get('properties'))
        val['attributes']   = get_attribute_definitions(capa_def.get('attributes'))

        # get valid_source_types
        sources = capa_def.get('valid_source_types')
        if isinstance(sources, list) and all(map(lambda x: isinstance(x, basestring), sources)):
          valid_source_types = sources

        # get occurrences
        occ_list = requ_def.get('occurrences')
        if isinstance(occ_list, list): 
          occ_range = Range.from_list(occ_list)
          if isinstance(occ_range, Range):
            occ_min = occ_range.minval
            occ_max = occ_range.maxval
        else:
          print "Syntax Error in occurences definition '{}' for requirement '{}".format(occ_list, requ_name)

      capa_val = {'name': capa_name, 'type': capa_type, 'description' = description, 
                  'properties': properties, 'attributes': attributes, 'valid_sources_types': valid_source_types,
                  'occurrence_min' = occ_min, 'occurrence_max': occ_max }

      if 'capa_type' is None:
        print "ERROR : type is mandatory in capability definition ( {} \n= {} )".format(capa_name, capa_val)

      # build value for requirement
      capabilities[capa_name] = capa_val

  return capabilities

