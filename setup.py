setting = {
    'filepath' : __file__,
    'use_db': True,
    'use_default_setting': True,
    'home_module': None,
    'menu': {
        'uri': __package__,
        'name': '영화 파일처리',
        'list': [
            {
                'uri': 'list',
                'name': '파일처리 결과',
            },
            {
                'uri': 'basic',
                'name': '기본 처리',
                'list': [
                    {'uri': 'setting', 'name': '설정'},
                ]
            },
            {
                'uri': 'manual',
                'name': '매뉴얼',
                'list': [
                    {'uri':'README.md', 'name':'README.md'},
                    {'uri':'files/config_basic.yaml', 'name':'fp_movie_basic.yaml'}
                ]
            },
            {
                'uri': 'log',
                'name': '로그',
            },
        ]
    },
    'setting_menu': None,
    'default_route': 'normal',
}


from plugin import *

P = create_plugin_instance(setting)

try:
    from .mod_basic import ModuleBasic
    from .mod_list import ModuleList
    P.set_module_list([ModuleList, ModuleBasic])
except Exception as e:
    P.logger.error(f'Exception:{str(e)}')
    P.logger.error(traceback.format_exc())

logger = P.logger
