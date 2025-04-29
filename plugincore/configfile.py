import configparser
import os
import keyword
import builtins
import re
from collections import UserDict

def value_bool(value: any) -> bool:
    if type(value) is str:
        return value in ['true','enabled','on','1','enable']
    if value:
        return True
    return False

class Interpolator(configparser.ExtendedInterpolation):
    """
    This Interpolator class allows for variable interpolation in a few ways. Normally 
    the values from the ini file are, programaticcallt, config[section][variable] or
    config.section.variable and these are strings but sometimes we need better conversions
    so this class converts:
        int:42 to an int with the value of 42
        float:3.14 to a float with the value of 3.14
        bool: converts values of 'true','enabled','on','1','enable to True otherwise False
        list:item1 item2 item3 ended with & or end of line. Each item is checked for type
        conversion shown above. 
        In addition ${ENV:var} will substitute ${ENV:var} with var from the user envionment.
        ${section:var} will be replaced by the value of section.var in the file. 
    """
    _env_var_pattern = re.compile(r'\$\{ENV:([^}]+)\}')
    _typed_value_pattern = re.compile(r'^(bool|int|float|list):(.*)', re.DOTALL)

    def __init__(self):
        super().__init__()
        self._type_constructors = {
            'bool': value_bool,
            'int': int,
            'float': float,
            'list': self._convert_list,  # Add 'list' constructor here
        }

    def before_get(self, parser, section, option, value, defaults):
        # Handle ${ENV:VAR}
        value = self._env_var_pattern.sub(
            lambda m: os.environ.get(m.group(1), ''), value
        )

        # Check for typed prefix
        m = self._typed_value_pattern.match(value)
        if m:
            prefix, raw = m.group(1), m.group(2).lstrip()
            converter = self._type_constructors.get(prefix)
            if converter:
                # Use the type constructor to convert the value
                raw = converter(raw)
                return raw
            else:
                return self._convert_list(raw)  # Handle as list if no matching type

        return super().before_get(parser, section, option, value, defaults)

    def _convert_list(self, raw):
        # Process 'list:' prefix if it exists
        if raw.startswith('list:'):
            raw = raw[5:].lstrip()  # Remove 'list:' prefix

        items = []
        for token in raw.split():
            # For each token, check for its type and apply conversion if necessary
            m = self._typed_value_pattern.match(token)
            if m:
                prefix, item = m.group(1), m.group(2)
                converter = self._type_constructors.get(prefix)
                if converter:
                    items.append(converter(item))  # Convert using the correct constructor
                else:
                    items.append(item)  # If no type prefix, add as-is
            else:
                items.append(token)  # If no match, add token as-is

        return items
    
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

        See the Interpolator class above for information about how value strings are parsed.
        """
    def __init__(self, **kwargs):
        self._foo = "foo"
        super().__init__({})
        section_name = kwargs.get('section_name')
        env_prefix = kwargs.get('env_prefix')
        filename = kwargs.get('file')
        items = kwargs.get('items')
        env_override = kwargs.get('env_override', False)

        if not items and filename:
            self.top_config = self;
            config = config = configparser.ConfigParser(interpolation=Interpolator())
            config.read(filename)
            for section in config.sections():
                if self._keyok(section,'main'):
                    section_items = dict(config.items(section))
                    conf = Config(top_config=self.top_config, items=section_items, env_override=env_override,env_prefix=env_prefix, section_name=section)
                    setattr(self, section,conf)
                    self.data[section] = conf
        elif items:
            self.top_config = kwargs.get('top_config',None)
            for k, v in items.items():
                if not section_name:
                    sect = '-main-'
                else:
                    sect = section_name
                    if not len(k):
                        raise AttributeError(f"A key passed in {sect} was blank, this shouldn't happen")
                    if not k[0].isalpha():
                        raise AttributeError(f"Error in {sect}->{k}: configuration secions or keys must start with alpha characters")
                if self._keyok(k,sect):
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

    def _keyok(self,k,sect):
        _forbidden_keys = {
            'python keyword': keyword.kwlist,
            'python builtin': dir(builtins),
            'class keyword': dir(self)+['self']
        }
        for ktype, klist in _forbidden_keys.items():
            if k in klist:
                raise AttributeError(f"Error in {sect}->{k}:, {k} is a {ktype} and may not be used")
        return True

    def __setitem__(self, key, item):
        item = self._replace_env_vars(item)
        print('setattr',self,key,item)
        setattr(self,key,item)
        return super().__setitem__(key, item)

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