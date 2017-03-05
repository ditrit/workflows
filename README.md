# workflows

This is a very first implementation for TOSCA 1.1 explicit workflows.

The purpose is to implement TOSCA declarative workflows defined at node type and relationship type level as described in the OASIS normative document 
[TOSCA Simple Profile in YAML Version 1.1](http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.1/TOSCA-Simple-Profile-YAML-v1.1.pdf).

Workflow definition is parsed into a simple rule based RETE like engine. 
Orchestration is launched simply inserting facts (nodes and relationships instances) into the RETE network.
Both facts and RETE rules are stored into Consul. 

## The exemple 
- Workflows implemented are standard `install and uninstall TOSCA workflow as defined in § "7.4.2 Weaving improvements" of the normative document.
- Facts used as exemple describe connections between 4 nodes : [`A-->B B-->D D-->C and A -->C], each node being hosted onto a 'srv' node (A is hosted on srvA, B is hosted on srvB, C is hosted on srvC and D is hosted on D). 

## Running the example

1. Prerequisite : local Consul agent with workflow_watch.conf installed.
2. Parse and upload exemple : <pre>python data_to_consul.py normative.yaml</pre>
3. Execute install workflow using Consul kv : <pre>consul kv put exec-workflow "{'name': 'install'}"</pre>
4. Watch execution with <pre>tail -f /opt/execs</pre>


# Caution

This project is not production ready at all and has not been tested.
The API may change at each commit.
