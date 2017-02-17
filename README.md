# workflows

This is a very first implementation for TOSCA 1.1 explicit workflows.

The purpose is to implement TOSCA declarative workflows defined at node type and relationship type level as described in the OASIS normative document 
[TOSCA Simple Profile in YAML Version 1.1](http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.1/TOSCA-Simple-Profile-YAML-v1.1.pdf).

Workflow definition is parsed into a simple rule based RETE like engine. 
Orchestration is launched simply inserting facts (nodes and relationships instances) into the RETE network.

## The exemple 
- Workflow in input is the standard `install` TOSCA workflow as defined in § "7.4.2 Weaving improvements" of the normative document.
- Facts in input describe connections between 4 nodes : [`A-->B B-->D D-->C and A -->C](facts_ex1.svg) 

## Running the example

`python workflows_rete_04.py`

<pre>
A.state = creating
A : tosca.interfaces.node.lifecycle.Standard.create
A.state = created
A.state = configuring
C.state = creating
C : tosca.interfaces.node.lifecycle.Standard.create
C.state = created
C.state = configuring
C : rac.tosca.interfaces.relationships.Configure.pre_configure_target
B.state = creating
B : tosca.interfaces.node.lifecycle.Standard.create
B.state = created
B.state = configuring
B : rab.tosca.interfaces.relationships.Configure.pre_configure_target
D.state = creating
D : tosca.interfaces.node.lifecycle.Standard.create
D.state = created
D.state = configuring
D : rbd.tosca.interfaces.relationships.Configure.pre_configure_target
C : rdc.tosca.interfaces.relationships.Configure.pre_configure_target
C : tosca.interfaces.node.lifecycle.Standard.configure
C : rdc.tosca.interfaces.relationships.Configure.post_configure_target
C : rac.tosca.interfaces.relationships.Configure.post_configure_target
C.state = configured
C.state = starting
C : tosca.interfaces.node.lifecycle.Standard.start
C.state = started
D : rdc.tosca.interfaces.relationships.Configure.pre_configure_source
D : tosca.interfaces.node.lifecycle.Standard.configure
D : rbd.tosca.interfaces.relationships.Configure.post_configure_target
C : rdc.tosca.interfaces.relationships.Configure.add_source
D : rdc.tosca.interfaces.relationships.Configure.post_configure_source
D.state = configured
D : rdc.None
D.state = starting
D : tosca.interfaces.node.lifecycle.Standard.start
D.state = started
B : rbd.tosca.interfaces.relationships.Configure.pre_configure_source
B : tosca.interfaces.node.lifecycle.Standard.configure
B : rab.tosca.interfaces.relationships.Configure.post_configure_target
D : rbd.tosca.interfaces.relationships.Configure.add_source
B : rbd.tosca.interfaces.relationships.Configure.post_configure_source
B.state = configured
B : rbd.None
B.state = starting
B : tosca.interfaces.node.lifecycle.Standard.start
B.state = started
A : rab.tosca.interfaces.relationships.Configure.pre_configure_source
B : rab.tosca.interfaces.relationships.Configure.add_source
B : rbd.tosca.interfaces.relationships.Configure.add_target
B.state = ended
D : rdc.tosca.interfaces.relationships.Configure.add_target
D.state = ended
A : rac.tosca.interfaces.relationships.Configure.pre_configure_source
A : tosca.interfaces.node.lifecycle.Standard.configure
A : rab.tosca.interfaces.relationships.Configure.post_configure_source
C : rac.tosca.interfaces.relationships.Configure.add_source
C.state = ended
A : rac.tosca.interfaces.relationships.Configure.post_configure_source
A.state = configured
A : rab.None
A : rac.None
A.state = starting
A : tosca.interfaces.node.lifecycle.Standard.start
A.state = started
A : rab.tosca.interfaces.relationships.Configure.add_target
A : rac.tosca.interfaces.relationships.Configure.add_target
A.state = ended
</pre>

# Caution

This project is not production ready at all and has not been tested.
The API may change at each commit.
