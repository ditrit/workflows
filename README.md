# workflows

This is a very first implementation for TOSCA 1.1 explicit workflows.

The purpose is to implement TOSCA declarative workflows defined at node type and relationship type level as described in the OASIS normative document 
[TOSCA Simple Profile in YAML Version 1.1](http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.1/TOSCA-Simple-Profile-YAML-v1.1.pdf).

Workflow definition is parsed into a simple rule based RETE like engine.
Engine uses a set of workers which insert facts into RETE rules and execute operations.
Workers are sateless and coordination is provided using LINDA coordination language primitives.
Consul is used as storage backend (used for facts and RETE rules) and as the Tuple-Space used by workers.

## Resiliency and high availibility
- No more facts distribution : each worker launch a thread for each fact of the instance whose status is set as ready in the Space. 
- Linda coordination provides distribution of operations whatever the number of workers.
- Consul provides high availibility, resiliency and coherency at Space level. 

## The exemple 
- Workflows implemented are standard `install and uninstall TOSCA workflow as defined in § "7.4.2 Weaving improvements" of the normative document.
- The Model used as exemple describe connections between 4 nodes (`A-->B B-->D D-->C and A -->C ), each one node being hosted onto an other node (A is hosted on srvA, B is hosted on srvB, C is hosted on srvC and D is hosted on D). 
- Default scaling is used on several nodes. 19 real nodes are built when the 'install' workflow is executed for an instance of the model.

## Running the example

1. Prerequisite :
   - An up and running Linux OS with ansible 2.3, lxc and libvirtd installed (tested with Redhat 7 and Ubuntu 16.10)
2. Installation :
   - Clone the repository : <pre>git clone https://github.com/ditrit/workflows.git</pre>.
   - Go into the <pre>install</pre> directory.
   - Adapt the inventory <pre>hosts</pre> file with adequate ip addresses.
   - Install ditrit as root : <pre>ansible-playbook -i hosts ditrit.yaml</pre>
   - Go into one of the manager containers : <pre>lxc-attach -n manager1</pre>
3. Use Ditrit:
   - Parse and upload a ditrit component library (actually just TOSCA root normative types) : <pre>curl -X PUT http://localhost:5000/library -F "file=@normative.yaml"</pre>
   - Parse and upload an application model : <pre>curl -X PUT "http://localhost:5000/model?name=un_model" -F "file=@test_model.yaml"</pre>
   - Instanciate a deployment from model  : <pre>curl -X PUT "http://localhost:5000/instance?model=un_model&name=une_instance"</pre>
   - Launch a workflow : <pre>curl -X PUT "http://localhost:5000/exec?model=un_model&instance=une_instance&workflow=install"</pre>
   - Watch execution on each workflow worker <pre>tail -f /opt/execs</pre>
4. Destroy, stop or start workers or consul server members during execution and verify it's still working.


# Caution

This project is not production ready at all and has not been tested.
The API may change at each commit.
