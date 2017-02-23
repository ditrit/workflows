#!/usr/bin/python

import os
import sys
import copy
import consulate
import json
from utils import consul_lock
from tosca_template import ToscaTemplate

"""
	Example facts used to test the workflow	
"""
node_facts = { 
		'A': 	{ 'type': 'tosca.nodes.Root' },
		'B': 	{ 'type': 'tosca.nodes.Root' },
		'C': 	{ 'type': 'tosca.nodes.Root' },
		'D': 	{ 'type': 'tosca.nodes.Root' },
		'srvA': { 'type': 'tosca.nodes.Root' },
		'srvB': { 'type': 'tosca.nodes.Root' },
		'srvC': { 'type': 'tosca.nodes.Root' },
		'srvD': { 'type': 'tosca.nodes.Root' }}

rel_facts = {
		'rab': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'B' },
		'rac': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'A', 'target': 'C' },
		'rbd': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'B', 'target': 'D' },
		'rdc': { 'type': 'tosca.relationships.ConnectsTo', 'source': 'D', 'target': 'C' },
		'ha':   { 'type': 'tosca.relationships.HostedOn', 'source': 'A', 'target': 'srvA' },
		'hb':   { 'type': 'tosca.relationships.HostedOn', 'source': 'B', 'target': 'srvB' },
		'hc':   { 'type': 'tosca.relationships.HostedOn', 'source': 'C', 'target': 'srvC' },
		'hd':   { 'type': 'tosca.relationships.HostedOn', 'source': 'D', 'target': 'srvD' }}

def prepare_facts(consul, session_id):
	""" 
        	Initializes necessary status information for each fact. 
                Also provides for each node instance the set of outgoing and ingoing relations. 
	"""
	reltypes = json.loads(consul.kv['rel_types'])
	
	with consul_lock(consul, session_id, 'locks/allfacts'):
	#if True:
		nodefact_names = consul.kv.find('node_facts').values()
		
		for fname in nodefact_names:
			consul.kv["{}/state".format(fname)] = 'none'
			consul.kv["{}/step".format(fname)]  = 0
			for reltype in reltypes:
				consul.kv["{}/out/{}".format(fname, reltype)] = reltype
				consul.kv["{}/in/{}".format(fname, reltype)] = reltype
		
		relfact_names = consul.kv.find('rel_facts').values()
		for fname in relfact_names:
			tfact = consul.kv["{}/type".format(fname)]
			consul.kv["{}/source_weaving".format(fname)] = 0
			consul.kv["{}/target_weaving".format(fname)] = 0
			
			srcname = consul.kv["{}/source".format(fname)]
			tgtname = consul.kv["{}/target".format(fname)]
			
			consul.kv["{}/out/{}/source/{}".format(srcname,tfact,fname)] = fname
			consul.kv["{}/in/{}/target/{}".format(tgtname,tfact,fname)] = fname


def upload(toscayaml):
	consul = consulate.Consul()
	session_id = consul.session.create()

	node_types = toscayaml.get('node_types')
	rel_types  = toscayaml.get('relationship_types')

	with consul_lock(consul, session_id, 'locks/typesdef'):
	#if True:
		
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
		
	with consul_lock(consul, session_id, 'locks/allfacts'):
	#if True:
		
		if  node_facts:
			for nodefact in node_facts:
				consul.kv['node_facts' + "/" + nodefact ] = nodefact
				consul.kv[nodefact + '/type'] = node_facts[nodefact]['type']
			
			
		if  rel_facts:
			for relfact in rel_facts:
				consul.kv['rel_facts' + "/" + relfact ] = relfact
				consul.kv[relfact + '/type'] = rel_facts[relfact]['type']
				consul.kv[relfact + '/source'] = rel_facts[relfact]['source']
				consul.kv[relfact + '/target'] = rel_facts[relfact]['target']

	prepare_facts(consul, session_id)
	
	session_ended = consul.session.destroy(session_id)
	if session_ended == False:
		print "Session non terminee"


def main(args=None):
	"""
		Upload a TOSCA template given in arguments (imports is ok).
		Workflow definition is uploaded from a TOSCA template.
		Facts are not currently loaded from the template.
	"""

	filename = sys.argv[1] if len(sys.argv) > 1 else None
	
	if filename is not None:
		tosca = ToscaTemplate(filename)
		if tosca is not None:
			toscayaml = tosca.yamldef

	upload(toscayaml)
			
if __name__ == '__main__':
    main()
             

