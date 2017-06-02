
class Version(object):

  def __init__(self, valdef):
    self.major_version = 0
    self.minor_version = 0
    self.fix_version   = 0
    self.qualifier     = ''
    self.build_version = 0
    ok = True
    if isinstance(valdef, basestring):
      valdef_args = valdef.split('.')
      vlen = len(valdef_args)
      if vlen in [ 2, 3, 4 ]:
        try:
          self.major_version = int(valdef_args[0])
          self.minor_version = int(valdef_args[1])
          if vlen > 2:
            self.fix_version   = int(valdef_args[2])
            if vlen == 4:
              self.qualifier   = str(valdef_args[3])
              qualifier_args = qualifier.split('-')
              if len(qualifier_args) == 2
                self.qualifier     = str(qualifier_args[0])
                self.build_version = int(qualifier_args[1])
              else:
                if len(qualifier_args) > 2:
                  ok = False
        except:
          ok = False
    if ok == False:
      print "Error : '{}' is not a valid version".format(valdef)

  def __str__(self):
    detail = ""
    if self.qualifier != '':
      detail = ".{}-{}".format(self.qualifier,self.build_version)
    return "{}.{}{}".format(self.major_version, self.minor_version, detail)

  def __eq__(self, other):
    return self.major_version == other.major_version and
           self.minor_version == other.minor_version and
           self.fix_version == other.fix_version and
           self.qualifier == other.qualifier and
           self.build_version == other.build_version 

  def __lt__(self, other):
    return self.major_version < other.major_version  or
       ( self.major_version == other.major_version and self.minor_version < other.minor_version ) or \
       ( self.major_version == other.major_version and self.minor_version == other.minor_version and self.fix_version < other.fix_version ) or \
       ( self.major_version == other.major_version and self.minor_version == other.minor_version and self.fix_version == other.fix_version and self.qualifier != '' and other.qualifier == "") or \
       ( self.major_version == other.major_version and self.minor_version == other.minor_version and self.fix_version == other.fix_version and self.qualifier < other.qualifier == "") or \
       ( self.major_version == other.major_version and self.minor_version == other.minor_version and self.fix_version == other.fix_version and self.qualifier == other.qualifier and self.build_version < other.build_version) 

  def __le__(self, other):
    return self < other or self == other

  def __ne__(self, other):
    return not self == other

  def __gt__(self, other):
    return other < self

  def __ge__(self, other):
    return other < self or self == other

class Range(object)

  unbounded = 'UNBOUNDED'

  def __init__( minval, maxval ):
    if isinstance(minval, int) and ((isinstance(maxval, int) and maxval >= minval) or str(maxval) == unbounded):
      self.minval = minval
      self.maxval = maxval
    else:
      print "Error : '[ {}, {} ]' is not a valid range".format(minval, maxval)

  def __eq__(self, other):
    return self.minval == other.minval and self.maxval == other.maxval

  def __contains__(self, val):
    minok = val >= self.minval
    if self.maxval != unbounded:
      maxok = val <= self.maxval
    else:
      maxok = True
    return minok and maxok

  @classmethod
  def from_minmax(cls, minval, maxval):
    if isinstance(minval, int) and ((isinstance(maxval, int) and maxval >= minval) or str(maxval) == unbounded):
      return cls(minval, maxval)
    else:
      return None
     
  @classmethod
  def from_list(cls, args):
     if isinstance(args, list) and len(args) == 2:
       return cls.from_minmax(args[0], args[1])
     else:
       print "Error : '{}' is not a valid range".format(args)
       return None
     

class ScalarUnit(object):

  def __init__(scalar, unit):
    self.scalar = scalar
    self.unit   = unit
    if self.unit in units.keys():
      self.value  = self.scalar * units[self.unit]
    else:
      print "Error: '{}' is not a valid unit".format(unit)

  @classmethod
  def from_string(cls, strval):
    if isinstance(strval, basestring)
      args = strval.split()
      if len(args) == 2 : 
        return cls(args[0], args[1])
      else:
        print "Error: '{}' is not a valid scalar unit value".format(strval)
        return None

  def __str__(self):
    return "{} {}".format(self.scalar, self.unit)

  def __eq__(self, other):
    return self.value == other.value

  def __lt__(self, other):
    return self.value < other.value

  def __le__(self, other):
    return self < other or self == other

  def __ne__(self, other):
    return not self == other

  def __gt__(self, other):
    return other < self

  def __ge__(self, other):
    return other < self or self == other


class ScalarUnit_size(ScalarUnit):

  units = { 'B': 1, 'kB': 1000, 'KiB': 1024, 'MB': 1000000, 'MiB': 1048576, 'GB': 1000000000, 'GiB': 1073741824, 'TB': 1000000000000, 'TiB': 1099511627776 } 


class ScalarUnit_time(ScalarUnit):

  units = { 'ns': 1, 'us': 1000, 'ms': 1000000, 's': 1000000000, 'm': 60000000000, 'h': 3600000000000, 'd': 86400000000000 } 


class ScalarUnit_frequency(ScalarUnit):

  units = { 'Hz': 1, 'kHz': 1000, 'MHz': 1000000, 'GHz': 1000000000 } 

def get_string(valdef):
  value = None
  try:
    value = str(valdef)
  except:
    print "'{}' is not a string".format(valdef)
  return value

def get_integer(valdef):
  value = None
  try:
    value = int(valdef)
  except:
    print "'{}' is not an integer".format(valdef)
  return value

def get_float(valdef):
  value = None
  try:
    value = float(valdef)
  except:
    print "'{}' is not a float".format(valdef)
  return value

def get_boolean(valdef):
  value = None
  if valdef in [ False, 'false', 'False' ]
    return False
  if valdef in [ True, 'true', 'True' ]
    return True
  try:
    value = eval(valdef)
  except:
    print "'{}' is not a boolean".format(valdef)
  return value

def get_null(valdef):
  if valdef not in [ None, 'null' ]
    print "'{}' is not null value".format(valdef)
  return None

def get_timestamp(valdef):
  if isinstance(valdef, datetime.datetime)
    return valdef
  else:
    print "'{}' is not a timestamp".format(valdef)
    return None

def get_version(valdef):
  return Version(valdef)

def get_range(valdef):
  if isinstance(valdef, Range):
    return valdef  
  if isinstance(valdef, list):
    return Range.from_list(valdef)

def get_size(valdef):
  if isinstance(valdef, ScalarUnit_size):
    return valdef  
  if isinstance(valdef, basestring):
    return ScalarUnit_size.from_list(valdef)
  print "Error: '{}' is not a size scalar unit".format(valdef)
  return None

def get_time(valdef):
  if isinstance(valdef, ScalarUnit_time):
    return valdef  
  if isinstance(valdef, basestring):
    return ScalarUnit_time.from_list(valdef)
  print "Error: '{}' is not a time scalar unit".format(valdef)
  return None

def get_frequency(valdef):
  if isinstance(valdef, ScalarUnit_frequency):
    return valdef  
  if isinstance(valdef, basestring):
    return ScalarUnit_frequency.from_list(valdef)
  print "Error: '{}' is not a frequency scalar unit".format(valdef)
  return None

def get_list(valdef):
  if isinstance(valdef, list):
    return valdef
  else:
    print "Error: '{}' is not a list".format(valdef)
    return None

def get_map(valdef):
  if isinstance(valdef, dict):
    return valdef
  else:
    print "Error: '{}' is not a map".format(valdef)
    return None


def get_value(valdef, typename):
  get_value_map = {
    'string':    get_string,
    'integer':   get_integer,
    'float':     get_float,
    'boolean':   get_boolean,
    'null':      get_null,
    'timestamp': get_timestamp,
    'version':   get_version,
    'range':     get_range,
    'size':      get_size,
    'time':      get_time,
    'frequency': get_frequency,
    'list':      get_list,
    'map':       get_map
  }
  if typename in get_value_map.keys()
    return get_value_map[typename](valdef)
  else:
    return None




   
