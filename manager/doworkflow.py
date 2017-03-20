#!/usr/bin/python

import os
import sys
import base64
import time
from linda import *

"""
  'Doworkflow' just launches the execution of the workflow provided as argument. 
"""

def main(args=None):
	
    workflow_name = sys.argv[1] if len(sys.argv) > 1 else None
    if workflow_name is not None:
	f = linda_rd('node_facts')
	facts = eval(f)

        # every fact of the instance is written to trigger workflow worker
	if len(facts)>0:
          for fact_name in facts:
             linda_out("exec-wd/{}/fact/{}".format(workflow_name, fact_name), time.time())

if __name__ == '__main__':
    main()

