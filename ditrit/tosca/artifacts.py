
from tosca.basetypes   import *
from tosca.properties import *

def get_operation_definitions(artifacts_def):
  """
      Parse artifacts definition
  """
  artifacts = {}

  if isinstance(artifacts_def, dict):

    for art_name, art_def in artifacts_def.items()
        description   = ""
        artifact_type = None
        aritfact_file = None
        repository    = None
        deploy_type   = None
        
        # get description
        val = art_def.get('description')
        if val is not None:
          if isinstance(description, basestring):
            description = val 

        # get type of the artifact
        artifact_type = art_def.get('type')
        ## TODO: verify it is an artifact type
        print "ERROR: deifnition of an artifact must define the type of the artifact"

        # get the URI string of the file
        artifact_file = art_def.get('file'))

        # get the repository to use
        ## TODO: get verify it as known repository
        repository = art_def.get('repository'))

        deploy_path = art_def.get('deploy_path')

        art_val = { 'name': art_name, 'description': description,  'type': artifact_type;
                   'file': artifac_file, 'repository': repository, 'dezploy_path': deploy_path }

        # build value for interface
        artifacts[art_name] = art_val

  return artifacts

