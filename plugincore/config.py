import configparser
import os
import keyword
import builtins
from collections import UserDict

class Config(UserDict):
    """ Parse and INI file for sections and keys, creating more Config objects for 
       each section. 
       usage: 
       1 - read config file: 
            Config(file=<pathname>, env_override=True|False)
       2 - build object from dict in items: 
            Config(items=<dict>, env_override=True|False)

        returns a quasi dict-like object where object properties are also keys when referencing 
        as a dict. 

        Environment overrides are done when env_override=True and if there is a value 
        of key (uppercase) in the environment. Key must exist in the ini_file. 

        There are a few restrictions with the section and key names:
            keys must start with alpha characters (A-Z, a-z)
            keys must NOT be python keywords, builtins, or attributes or methods of the Config class
            itself, or the word self as these will cause issues internally.

        The configuration data is accessible with either dot or index notation. This class 
        is based on UserDict so it will pretty much act like a dict.
        """
    def __init__(self, **kwargs):
        super().__init__({})
        section_name = kwargs.get('section_name')
        _forbidden_keys = {
            'python keyword': keyword.kwlist,
            'python builtin': dir(builtins),
            'class keyword': dir(self)+['self']
        }
        def keyok(k):
            if not section_name:
                sect = '-main-'
            else:
                sect = section_name
            if not len(k):
                raise AttributeError(f"A key passed in {sect} was blank, this shouldn't happen")
            if not k[0].isalpha():
                raise AttributeError(f"Error in {sect}->{k}: configuration secions or keys must start with alpha characters")
            for ktype, klist in _forbidden_keys.items():
                if k in klist:
                    raise AttributeError(f"Error in {sect}->{k}:, {k} is a {ktype} and may not be used")
            return True

        env_prefix = kwargs.get('env_prefix')
        filename = kwargs.get('file')
        items = kwargs.get('items')
        env_override = kwargs.get('env_override', False)

        if not items and filename:
            config = configparser.ConfigParser()
            config.read(filename)
            for section in config.sections():
                if keyok(section):
                    section_items = dict(config.items(section))
                    conf = Config(items=section_items, env_override=env_override,env_prefix=env_prefix, section_name=section)
                    setattr(self, section,conf)
                    self.data[section] = conf
        elif items:
            for k, v in items.items():
                if keyok(k):
                    if env_override:
                        env_var = ""
                        if env_prefix:
                            env_var = f"{env_prefix.upper()}_"
                        if section_name:
                            env_var = env_var + f"{section_name.upper()}_"
                        env_var = env_var + k.upper()
                        if env_var in os.environ:
                            v = os.environ[env_var]
                    setattr(self, k, v)
                    self.data[k] = v
        else:
            raise AttributeError('items or file must be specified')

    @property
    def _keys(self):
        return self.data.keys()

    def merge(self, other: "Config", overwrite: bool = True):
        """
        Merge another Config object into this one.

        Args:
            other (Config): Another config to merge from.
            overwrite (bool): Whether to overwrite existing values.
        """
        for key in other._keys:
            if key not in self._keys:
                attr = getattr(other, key)
                setattr(self, key, attr)
                self.data[key] = attr
            elif isinstance(getattr(self, key), Config) and isinstance(getattr(other, key), Config):
                getattr(self, key).merge(getattr(other, key), overwrite=overwrite)
            elif overwrite:
                attr = getattr(other, key)
                setattr(self, key, attr)
                self.data[key] = attr

    def write(self, filename: str):
        """
        Write the configuration back to an INI file.

        Args:
            filename (str): Path to output INI file.
        """
        config = configparser.ConfigParser()

        for key in self._keys:
            value = getattr(self, key)
            if isinstance(value, Config):
                config[key] = {k: str(getattr(value, k)) for k in value._keys}
            else:
                config['DEFAULT'][key] = str(value)

        with open(filename, 'w') as f:
            config.write(f)
