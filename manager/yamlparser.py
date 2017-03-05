
import codecs
from six.moves import urllib
import yaml

def load_yaml(path, a_file=True):
    f = None
    try:
      if isinstance(path, basestring):
        f = codecs.open(path, encoding='utf-8', errors='strict') if a_file \
            else urllib.request.urlopen(path)
    except Exception as e:
        raise
    return yaml.load(f.read())


def simple_parse(tmpl_str):
    try:
        tpl = yaml.load(tmpl_str)
    except yaml.YAMLError as yea:
        raise
    else:
        if tpl is None:
            tpl = {}
    return tpl


