
from tosca.basetypes   import *
from tosca.properties import *

def get_repository_definitions(repositories_def):
  """
      Parse artifacts definition
  """
  repositories = {}

  if isinstance(repositories_def, dict):

    for repo_name, repo_def in repositories_def.items()
        description   = ""
        url = None
        credential = None
        
        # get description
        val = repo_def.get('description')
        if val is not None:
          if isinstance(description, basestring):
            description = val 

        # get the url of the repository
        url = repo_def.get('url')

        # get credential to be used
        ## TODO: get credential elements 
        credential = repo_def.get('credential'))

        repo_val = { 'name': repo_name, 'description': description,  'url': url, 'credential': credential }

        # build value for interface
        repositories[repo_name] = repo_val

  return repositories

