#!/usr/bin/python

import sys
import os
import consulate
from contextlib import contextmanager


@contextmanager
def consul_lock(consul, session_id, lock_key = None):
	try: 
		lock = consul.kv.acquire_lock(lock_key, session_id)
		if lock:
			try:
				yield			
			except:
				print "Erreur dans la partie lockee"
	except:
		print "Error inside protected section (using Consul lock mechanism)"
		
	finally:
		unlock = consul.kv.release_lock(lock_key, session_id)


