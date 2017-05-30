
import tosca_basetypes

def f_eq(v, _): 
  return lambda x : x == v

def f_gt(v, _): 
  return lambda x : x > v

def f_ge(v, _):
  return lambda x : x >= v

def f_lt(v, _):
  return lambda x : x < v

def f_le(v, _):
  return lambda x : x <= v

def f_ir(v, t):
  if isinstance(t, int) and isinstance(v, list):
    r = Range.from_list(v)
    return lambda x : x in r
  else:
    return lambda _: False

def f_vv(v, _):
  return lambda x : x in v

def f_ln(v, t):
  if isinstance(t, int) and isinstance(v, list):
    return lambda x : len(x) == v 
  else:
    return lambda _: False

def f_mn(v, t):
  if isinstance(t, int) and isinstance(v, list):
    return lambda x : len(x) >= v 
  else:
    return lambda _: False

def f_mx(v, t):
  if isinstance(t, int) and isinstance(v, list):
    return lambda x : len(x) <= v 
  else:
    return lambda _: False

def f_re(v, t):
  if isinstance(t, basestring) and isinstance(v, basestring):
    return lambda x : re.search(v, x) is not None 
  else:
    return lambda _: False

def parse_constraint(expr, typename):
  constraint_map = {
    'equal':            f_eq,
    'greater_than':     f_gt,
    'greater_or_equal': f_ge,
    'less_than':        f_lt,
    'less_or_equal':    f_le,
    'in_range':         f_ir,
    'valid_values':     f_vv,
    'length':           f_ln,
    'min_length':       f_mn,
    'max_length':       f_mx,
    'pattern':          f_re,
  if isinstance(expr, dict) and len(expr) == 1:
    key = expr.keys()[0]
    if key in contraint_map.keys():
      return constraint_map[key](expr[key])  
  print "Error: {} is not a valid expression for a constraint".format(expr)
  return lambda _ : False
    
def parse_constraints(list_expr, typename):
  if list_expr is None:
    list_expr = []
  if isinstance(list_expr, list):
    f_list = [ parse_constraint(expr, typename) for expr in list_expr ]
    return lambda x : all(map(lambda f : f(x), f_list)) 
  else:
    print "'{}' is not a list".format(list_expr)
    return lambda _ : False
   
