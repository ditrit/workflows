
from tosca.basetypes    import *
from tosca.constraints  import *
from tosca.operations   import *

def get_trigger_definitions(trigger_def):
  """
      Parse trigger definition
  """
  triggers = {}

  if isinstance(trigger_def, dict):

    # a key is the name of an operation if it is not a predefined key for interfaces
    for tr_name, tr_def in trigger_def.items()
      description = ""
      event_type = None
      schedule = None
      target_filter = None 
      constraint =  None
      period = None 
      evaluations = None 
      method = None
      action = None
  
      

      # get description
      val = tr_def.get('description')
      if val is not None:
        if isinstance(description, basestring):
          description = val 
        else:
          print "Syntax error in description"

      # get event type
      val = tr_def.get('event')
      if isinstance(val, basestring):
        event_type = val
      if isinstance(val, dict):
        val = val.get('type')
        if isinstance(val, basestring):
          event_type = val

      # get schedule period
      val = tr_def.get('schedule')
      if isinstance(val, dict):
        # TODO: verify it is a real schedule
        schedule = val

      # get target filter
      target_filter = tr_def.get('target_filter')
 
      # get condition
      val = tr_def.get('condition')
      if isinstance(val, dict):
        if 'constraint' in val.keys():
          constraint = val.get('constraint')
          period = val.get('period')
          evaluations = val.get('evaluations')
          method = val.get('method')
        else:
          constraint = tr_def.get('constraint')

      # get action
      action = get_operation_definitions(tr_def.get('action'))
            
      tr_val = { 'name': tr_name, 'description': description, 
                 'event_type': event_type, 'schedule': schedule, 
                 'target_filter': target_filter, 'constraint': constraint, 
                 'period': period, 'evaluations': evaluations, 'method': method }

      # build value for interface
      triggers[tr_name] = tr_val

  return triggers

