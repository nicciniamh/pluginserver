
class BasePlugin:
    def __init__(self, **kwargs):
        ourclass = self.__class__.__name__
        self._plugin_id = kwargs.get('route_path',ourclass.lower())
        #print(f"{self.__class__.__name__}: init - route: '/{self._plugin_id}, args: {kwargs}")
        self.args = dict(kwargs)

    def _get_plugin_id(self):
        return self._plugin_id
