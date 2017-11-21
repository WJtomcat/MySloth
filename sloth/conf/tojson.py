import json
from sloth.conf import default_config

def main():
    set = {}
    for setting in dir(default_config):
        if setting == setting.upper():
            set[setting] = getattr(default_config, setting)
    f = open('tojson.json', 'w')
    json.dump(set, f, indent=4, separators=(',', ': '), sort_keys=True)
    f.write("\n")

if __name__=='__main__':
    main()