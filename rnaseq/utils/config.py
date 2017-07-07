import yaml
import os

config_path = os.path.dirname(os.path.realpath(__file__))

# read rnaseq analysis paths
module_path = os.path.join(config_path, 'config_defaults.yaml')
module_path_dict = dict()
with open(module_path) as f:
    configs = yaml.load(f)
    for c, v in configs.items():
        globals()[c] = v
