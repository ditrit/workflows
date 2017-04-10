# workflows

This is a very first implementation for TOSCA 1.1 explicit workflows.

The purpose is to implement TOSCA declarative workflows defined at node type and relationship type level as described in the OASIS normative document 
[TOSCA Simple Profile in YAML Version 1.1](http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.1/TOSCA-Simple-Profile-YAML-v1.1.pdf).

Workflow definition is parsed into a simple rule based RETE like engine.
Engine uses a set of workers which insert facts into RETE rules and execute operations.
Workers are sateless and coordination is provided using LINDA coordination language primitives.
Consul is used as storage backend (used for facts and RETE rules) and as the Tuple-Space used by workers.

## Resiliency and high availibility
- Facts are ditributed between workers in such a way two workers can consume each fact at all time.
- If a worker die or fail before releasing a fact, the second worker consumes this fact less than a second later.
- Facts distribution is triggered 3 seconds after each worker creation or die.

## The exemple 
- Workflows implemented are standard `install and uninstall TOSCA workflow as defined in § "7.4.2 Weaving improvements" of the normative document.
- Facts used as exemple describe connections between 4 nodes (`A-->B B-->D D-->C and A -->C ), each one node being hosted onto an other node (A is hosted on srvA, B is hosted on srvB, C is hosted on srvC and D is hosted on D). 

## Running the example

1. Prerequisite :
   - An up and running consul cluster (tested with 3 consul servers)
   - A set of servers for workflow workers (tested with 3 servers). 
   - A server for manager (can be one of the workers)
2. Installation :
   - Install a consul agent and join to the cluster for each worker and the manager.
   - For each workflow worker :
      - copy 'workers/initworker.json' into the consul config directory. 
      - Copy 'workers/.py' into '/usr/local/bin'
   - Copy 'manager/*' on the manager.
3. Execute :
   - Parse and upload a ditrit component library (actually just TOSCA root normative types) : <pre>python upload.py library normative.yaml</pre>
   - Parse and upload an application model : <pre>python upload.py model test_model.yaml model_name</pre>
   - Instanciate a deployment from model  : <pre>pyhton run.py model_name instance_name</pre>
   - [to be updated] Launch the workflow from the manager : <pre>python run.py install model_name"</pre>
   - Watch execution from each workflow worker <pre>tail -f /opt/execs</pre>
4. Shutdown or create workers or consul server members during execution and verify it's still working.


# Caution

This project is not production ready at all and has not been tested.
The API may change at each commit.
