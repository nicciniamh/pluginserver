import inspect
import importlib.util
import os
import glob
from types import ModuleType
from typing import Union, Dict, List, Tuple
from plugincore import baseplugin
from urllib.parse import parse_qs

def parse_parameter_string(s):
    return {key: value[0] for key, value in parse_qs(s).items()}

def get_classes_and_methods(mod: Union[str, ModuleType]) -> Tuple[ModuleType, Dict[str, List[str]]]:
    if isinstance(mod, str):
        spec = importlib.util.spec_from_file_location("plugin_" + os.path.basename(mod).replace(".py", ""), mod)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {mod}")
        mod_instance = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod_instance)
        mod = mod_instance

    result = {}
    for name, cls in inspect.getmembers(mod, inspect.isclass):
        if cls.__module__ == mod.__name__:
            methods = [meth_name for meth_name, meth in inspect.getmembers(cls, inspect.isfunction)
                       if meth.__module__ == mod.__name__]
            result[name] = methods
    return mod, result

def get_plugins(path, **kwargs):
    plugins = {}
    cfg = kwargs.get('config')
    kwargs = dict(kwargs)
    plugin_files = glob.glob(os.path.join(path, '*.py'))
    print(f"Loading plugins from {path}: {plugin_files}")
    for p in plugin_files:
        plugin_module = os.path.basename(p)
        print(f"inspecting {p}")
        module, classmap = get_classes_and_methods(p)
        for cls_name in classmap:
            cls = getattr(module, cls_name)
            if not issubclass(cls, baseplugin.BasePlugin) or cls is baseplugin.BasePlugin:
                continue

            adict = {}
            if cfg and 'plugin_parms' in cfg.keys():
                if plugin_module in cfg.plugin_parms.keys():
                    adict = parse_parameter_string(cfg.plugin_parms[plugin_module])
            kwargs.update(adict)
            print(f"Loading plugin {cls}: parameters {adict} ", end="")
            obj = cls(**kwargs)
            print(f"Object: {obj}")

            plugins[obj._get_plugin_id()] = obj
    return plugins
