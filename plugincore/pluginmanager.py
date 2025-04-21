import sys
import types
import inspect
import importlib.util
import os
import glob
from typing import Dict, List, Union
from plugincore import baseplugin
from urllib.parse import parse_qs

def parse_parameter_string(s):
    return {key: value[0] for key, value in parse_qs(s).items()}

class PluginManager:
    def __init__(self, plugin_dir: str, **kwargs):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, baseplugin.BasePlugin] = {}
        self.modules: Dict[str, types.ModuleType] = {}
        self.config = kwargs.get('config')
        self.kwargs = dict(kwargs)

    def _load_module(self, filepath: str) -> types.ModuleType:
        mod_name = os.path.basename(filepath).replace(".py", "")
        spec = importlib.util.spec_from_file_location(mod_name, filepath)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {filepath}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _get_plugin_classes(self, mod: types.ModuleType) -> List[baseplugin.BasePlugin]:
        classes = []
        for name, cls in inspect.getmembers(mod, inspect.isclass):
            if cls.__module__ == mod.__name__ and issubclass(cls, baseplugin.BasePlugin) and cls is not baseplugin.BasePlugin:
                classes.append(cls)
        return classes

    def load_plugins(self):
        plugin_files = glob.glob(os.path.join(self.plugin_dir, '*.py'))
        print(f"Loading plugins from {self.plugin_dir}: {plugin_files}")
        for path in plugin_files:
            self.load_plugin(path)

    def load_plugin(self, path: str):
        plugin_module = os.path.splitext(os.path.basename(path))[0]  # strip .py
        mod = self._load_module(path)
        self.modules[plugin_module] = mod

        for cls in self._get_plugin_classes(mod):
            adict = {}
            try:
                adict = parse_parameter_string(self.config.plugin_parms[plugin_module])
            except (AttributeError, KeyError):
                pass
            kwargs = self.kwargs.copy()
            kwargs.update(adict)
            kwargs['config'] = self.config
            instance = cls(**kwargs)
            print(f"Loaded plugin {cls.__name__}: {instance}")
            self.plugins[instance._get_plugin_id()] = instance

    def remove_plugin(self, plugin_id: str):
        plugin = self.plugins.pop(plugin_id, None)
        if not plugin:
            print(f"No plugin with ID {plugin_id}")
            return

        # Try to remove the module
        module_name = plugin.__class__.__module__
        module_file = os.path.basename(module_name + ".py")
        print(f"Removing plugin {plugin_id} from module {module_name}")

        self.modules.pop(module_file, None)
        sys.modules.pop(module_name, None)

    def reload_plugin(self, plugin_id: str):
        if plugin_id not in self.plugins:
            print(f"No such plugin to reload: {plugin_id}")
            return
        plugin = self.plugins[plugin_id]
        module_name = plugin.__class__.__module__
        module_file = os.path.basename(module_name + ".py")
        full_path = os.path.join(self.plugin_dir, module_file)

        self.remove_plugin(plugin_id)
        self.load_plugin(full_path)

    def get_plugin(self, plugin_id: str):
        return self.plugins.get(plugin_id)

    def all_plugins(self):
        return self.plugins

