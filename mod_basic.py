from support import SupportYaml
from tool import ToolUtil

from .model import ModelFPMovieItem
from .setup import *
from .task import Task


class ModuleBasic(PluginModuleBase):

    def __init__(self, P):
        super(ModuleBasic, self).__init__(P, name='basic', first_menu='setting', scheduler_desc='영화 파일처리 - 기본')
       
        self.db_default = {
            f'{self.name}_db_version' : '1',
            f'{self.name}_interval' : '30',
            f'{self.name}_auto_start' : 'False',
            f'{self.name}_db_delete_day' : '30',
            f'{self.name}_db_auto_delete' : 'False',
            f'{P.package_name}_item_last_list_option' : '', 

            f'{self.name}_path_source' : '',
            f'{self.name}_meta_order' : 'daum, naver, tmdb',
            f'{self.name}_target_root_a' : '',
            f'{self.name}_target_format_a' : '{TITLE_FIRST_CHAR}/{TITLE} [{TITLE_EN}] ({YEAR}) [{COUNTRY}-{GENRE}-{RESOLUTION}-{VIDEO_CODEC}-{AUDIO_CODEC}.{AUDIO_COUNT}{INCLUDE_KOR_AUDIO}-{SUBTITLE_COUNT}{INCLUDE_KOR_SUBTITLE}.{FILE_SUBTITLE_COUNT}{INCLUDE_KOR_FILE_SUBTITLE}]',
            f'{self.name}_target_root_b' : '',
            f'{self.name}_target_format_b' : '{TITLE_FIRST_CHAR}/{TITLE} [{TITLE_EN}] ({YEAR}) [{COUNTRY}-{GENRE}-{RESOLUTION}-{VIDEO_CODEC}-{AUDIO_CODEC}.{AUDIO_COUNT}{INCLUDE_KOR_AUDIO}-{SUBTITLE_COUNT}{INCLUDE_KOR_SUBTITLE}.{FILE_SUBTITLE_COUNT}{INCLUDE_KOR_FILE_SUBTITLE}]',

            f'{self.name}_remove_file_extension' : 'exe, txt, jpg, nfo, url, torrent, aria2__temp',
            f'{self.name}_remove_folder_except_name' : 'subs, trailer, deleted, behindthescenes, interview, interview, scene, featurette, short, other',


            f'{self.name}_is_vod_check' : '.KOR. HDRip.',
            f'{self.name}_is_hardsub_check' : '.KOR.',
            f'{self.name}_make_info_json' : 'True',

            f'{self.name}_path_config' : "{PATH_DATA}" + os.sep + "db" + os.sep + f"{P.package_name}_{self.name}.yaml",
            f'{self.name}_use_notify' : 'False',

        }
        self.web_list_model = ModelFPMovieItem


    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        if sub == 'setting':
            arg['is_include'] = F.scheduler.is_include(self.get_scheduler_name())
            arg['is_running'] = F.scheduler.is_running(self.get_scheduler_name())
            arg['basic_path_config'] = ToolUtil.make_path(P.ModelSetting.get(f'{self.name}_path_config'))
        return render_template(f'{P.package_name}_{self.name}_{sub}.html', arg=arg)
        

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {'ret':'success'}
        return jsonify(ret)


    def plugin_load(self):
        if os.path.exists(ToolUtil.make_path(P.ModelSetting.get(f'{self.name}_path_config'))) == False:
            shutil.copyfile(os.path.join(os.path.dirname(__file__), 'files', f'config_{self.name}.yaml'), ToolUtil.make_path(P.ModelSetting.get(f'{self.name}_path_config')))


    def scheduler_function(self):
        ret = self.start_celery(Task.start, None, *())
    

    def task_interface(self):
        def func():
            time.sleep(1)
            self.task_interface2()
        th = threading.Thread(target=func, args=())
        th.setDaemon(True)
        th.start()
        return th


    def task_interface2(self):
        ret = self.start_celery(Task.start, None, *())
