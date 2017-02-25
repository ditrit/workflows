#!/usr/bin/python

import os
import sys
import copy
import consulate
import json
from utils import consul_lock
from tosca_template import ToscaTemplate



def prepare_toscatypes(consul, session_id, toscayaml):
	""" 
        	Put parsed TOSCA types defnition into Consul kvstore
	"""
	node_types = toscayaml.get('node_types')
	rel_types  = toscayaml.get('relationship_types')

	with consul_lock(consul, session_id, 'locks/typesdef'):
		node_types = toscayaml.get('node_types')
		if node_types:
			nodetype_names = [ nodetype for nodetype in node_types ]
			for nodetype in nodetype_names:
				consul.kv[nodetype] = node_types[ nodetype ]
			consul.kv['node_types'] = nodetype_names
			
		rel_types  = toscayaml.get('relationship_types')
		if rel_types:
			reltype_names = [ reltype for reltype in rel_types ]
			for reltype in reltype_names:
				consul.kv[reltype] = rel_types[ reltype ]
			consul.kv['rel_types'] = reltype_names
	

def prepare_facts(consul, session_id, node_facts, rel_facts):
	""" 
        	Initializes necessary status information for each fact. 
                Also provides for each node instance the set of outgoing and ingoing relations. 
	"""
	reltypes = { typename: [] for typename in json.loads(consul.kv['rel_types']) }
	for name, fact in node_facts.items():
			fact['state'] = 'none'
			fact['step']  = 0
			fact['out']   = copy.deepcopy(reltypes)
			fact['in']    = copy.deepcopy(reltypes)
	for name, fact in rel_facts.items():
			fact['done']           = []
			fact['source_weaving'] = 0
			fact['target_weaving'] = 0
			node_facts[fact['source']]['out'][fact['type']].append(name)
			node_facts[fact['target']]['in'][fact['type']].append(name)

	with consul_lock(consul, session_id, 'locks/facts'):
		consul.kv["node_facts"] = node_facts.keys()
		for name, fact in node_facts.items():
			consul.kv[name] = fact
		consul.kv["rel_facts"] = rel_facts.keys()
		for name, fact in rel_facts.items():
			consul.kv[name] = fact


def upload(toscayaml):

	# defined here because we can not currently parse
	node_facts = { 
		'A': 	{ 'type': 'tosca.nodes.Root' },
		'B': 	{ 'type': 'tosca.nodes.Root' },
		'C': 	{ 'type': 'tosca.nodes.Root' },
		'D': 	{ 'type': 'tosca.nodes.Root' },
		'srvA': { 'type': 'tosca.nodes.Root' },
		'srvB': { 'type': 'tosca.nodes.Root' },
		'srvC': { 'type': 'tosca.nodes.Root' },
		'srvD': { 'type': 'tosca.nodes.Root' }}

	# defined here because we can not currently parse it
	rel_facts = {
		'rab': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'B' },
		'rac': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'C' },
		'rbd': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'B', 'target': 'D' },
		'rdc': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'D', 'target': 'C' },
		'ha':   { 'type': 'tosca.relationships.HostedOn', 'source': 'A', 'target': 'srvA' },
		'hb':   { 'type': 'tosca.relationships.HostedOn', 'source': 'B', 'target': 'srvB' },
		'hc':   { 'type': 'tosca.relationships.HostedOn', 'source': 'C', 'target': 'srvC' },
		'hd':   { 'type': 'tosca.relationships.HostedOn', 'source': 'D', 'target': 'srvD' }}

	
	consul = consulate.Consul()
	session_id = consul.session.create()


	# Insert type definitions into kvstore
	prepare_toscatypes(consul, session_id, toscayaml)
	
	# Insert facts into kvstore
	prepare_facts(consul, session_id, node_facts, rel_facts)
	
	session_ended = consul.session.destroy(session_id)
	if session_ended == False:
		print "Session non terminee"


def main(args=None):
	"""
		Upload a TOSCA template given in arguments (imports is ok).
		Workflow definition is uploaded from a TOSCA template.
		Facts are not currently loaded from the template.
	"""

	print "TOSCA parsing"
	filename = sys.argv[1] if len(sys.argv) > 1 else None
	
	if filename is not None:
		tosca = ToscaTemplate(filename)
		if tosca is not None:
			toscayaml = tosca.yamldef

	print "Push data into Consul"
	upload(toscayaml)
			
if __name__ == '__main__':
    main()
             

