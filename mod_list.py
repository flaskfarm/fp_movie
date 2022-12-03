from .model import ModelFPMovieItem
from .setup import *


class ModuleList(PluginModuleBase):

    def __init__(self, P):
        super(ModuleList, self).__init__(P, name='list', first_menu='list')
        self.db_default = {
            f'{self.name}_db_version' : '1',
            f'{P.package_name}_item_last_list_option' : '',
        }
        self.web_list_model = ModelFPMovieItem

