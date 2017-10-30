"""Helper code to handle various configurations
"""
import json

SIMCONFIG_ATTRS = ('pathways',
                   'protocols',
                   'n_pairs',
                   'rndm_seed',
                   'n_repetitions',
                   'multiprocessing',
                   'output_dir',
                   'blue_config')

PROTOCOL_ATTRS = ('holding_I', 'holding_V',
                  't_stim', 't_stop',
                  'g_factor', 'record_dt',
                  'post_ttx', 'clamp_V')


class JsonConfig(object):
    """Dummy class to hold JSON configuration
    """
    def __str__(self):
        return str(self.__dict__)


def check_attributes(config_map, attrs):
    """Check whether there is a 100% match between the keys of a map \
            and a set of attributes.
    Raises AttributeError on failure
    """
    keys = config_map.keys()
    for k in keys:
        if k not in attrs:
            raise AttributeError(k)
    if len(keys) != len(attrs):
        raise AttributeError


def load_json(json_):
    """Load a json object from a file handle or a JSON string.
    """
    loader = json.loads if isinstance(json_, str) else json.load
    return loader(json_)


def config_from_json(json_obj):
    """Build a JsonConfig python object from a json instance
    """
    obj = JsonConfig()

    for key, val in json_obj.iteritems():
        setattr(obj, key, val)

    return obj


class Json2Config(object):
    """Functor to check json object against reference attributes.
    """
    def __init__(self, ref_attrs):
        self._ref_attrs = ref_attrs

    def __call__(self, json_input):
        json_obj = load_json(json_input)
        check_attributes(json_obj, self._ref_attrs)
        return config_from_json(json_obj)

json2protocol = Json2Config(PROTOCOL_ATTRS)

json2simconfig = Json2Config(SIMCONFIG_ATTRS)
