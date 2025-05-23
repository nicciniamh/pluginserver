import sys
import types
import inspect
import importlib.util
import os
import glob
from typing import Dict, List, Union
from plugincore import baseplugin
from urllib.parse import parse_qs
import json

def parse_parameter_string(s):
    return {key: value[0] for key, value in parse_qs(s).items()}

class PluginManager:
    def __init__(self, plugin_dir: str, **kwargs):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, baseplugin.BasePlugin] = {}
        self.modules: Dict[str, types.ModuleType] = {}
        self.config = kwargs.get('config')
        self.task_callback = kwargs.get('task_callback')
        self.log = kwargs.get('log')
        self.prog_args = kwargs.get('args')
        if not self.prog_args:
            raise ValueError('PluginManager: no args object passed')
        self.kwargs = dict(kwargs)

    
    def reset_config(self,config):
        self.config = config

    async def _load_module(self, filepath: str) -> types.ModuleType:
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

    async def load_plugins(self):
        plugin_files = glob.glob(os.path.join(self.plugin_dir, '*.py'))
        self.log(f"Loading plugins from {self.plugin_dir}")
        for path in plugin_files:
            await self.load_plugin(path)

    async def load_plugin(self, path: str):
        plugin_module = os.path.splitext(os.path.basename(path))[0]  # strip .py
        mod = await self._load_module(path)
        self.modules[plugin_module] = mod

        for cls in self._get_plugin_classes(mod):
            adict = {'task_callback': self.task_callback}
            try:
                adict = parse_parameter_string(self.config.plugin_parms[plugin_module])
            except (AttributeError, KeyError):
                pass
            adict['prog_args'] = self.prog_args
            kwargs = self.kwargs.copy()
            kwargs.update(adict)
            kwargs['config'] = self.config
            if 'json' in adict:
                jfilename= os.path.join(self.config.paths.plugins, adict['json'])
                if os.path.exists(jfilename):
                    try:
                        with open(jfilename) as  f:
                            kwargs.update(json.load(f))
                    except Exception as e:
                        self.log.warning(f"Plugin for {cls.__name__} could not load JSON settings from {jfilename}: {e}")
            try:
                instance = cls(**kwargs)
                initialize = getattr(instance,'initialize',None)
                if initialize and callable(initialize):
                    await instance.initialize(**kwargs)
                self.log(f"Loaded plugin {cls.__name__}")
                self.plugins[instance._get_plugin_id()] = instance
            except Exception as e:
                self.log.exception(f"Exception loading plugin from {path}: {e}")
                
    async def remove_plugin(self, plugin_id: str):
        plugin = self.plugins.pop(plugin_id, None)
        if not plugin:
            self.log(f"No plugin with ID {plugin_id}")
            return

        # Try to remove the module
        try:
            plugin.terminate_plugin()
        except Exception as e:
            self.log.exception(f"Exception {type(e)} Unloading plugin - terminate_plugin threw {e}")
        module_name = plugin.__class__.__module__
        module_file = os.path.basename(module_name + ".py")
        self.log(f"Removing plugin {plugin_id} from module {module_name}")

        self.modules.pop(module_file, None)
        sys.modules.pop(module_name, None)

    async def reload_plugin(self, plugin_id: str):
        if plugin_id not in self.plugins:
            self.log(f"No such plugin to reload: {plugin_id}")
            return
        plugin = self.plugins[plugin_id]
        module_name = plugin.__class__.__module__
        module_file = os.path.basename(module_name + ".py")
        full_path = os.path.join(self.plugin_dir, module_file)

        await self.remove_plugin(plugin_id)
        await self.load_plugin(full_path)

    async def get_plugin(self, plugin_id: str):
        return self.plugins.get(plugin_id)

    async def all_plugins(self):
        return self.plugins

