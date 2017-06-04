

def get_types(types_def, type_name):
  """
     Get the list of types the node derives from
  """
  if type_name.split('.')[-1] == 'Root':
    return [ type_name ]
  else:
    type_def = types_def[type_name]
    parent_type = type_def.get('derived_from')
    if isinstance(parent_type, basestring):
      return get_types(parent_type).append(type_name)
    else:
      print "Syntax error"
      return []

