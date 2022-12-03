import imp

from support import SupportFile, SupportString, SupportYaml
from support.expand.ffprobe import SupportFfprobe
from tool import ToolNotify

from .model import ModelFPMovieItem
from .setup import *


class Task(object):
    current_subtitle_data = None
    config = None

    def process_meta(db_item):
        name =  re.sub('\[.*?\]', '', db_item.source_name).strip()
        name = re.sub("\s{2,}", ' ', name)

        regex_list = [
            r'^(?P<keyword>.*?).(?P<year>\d{4})',
            r'^(?P<keyword>.*?)(?P<year>\d{4})',
            r'^(?P<keyword>.*?)\s+\((?P<year>\d{4})\)',
        ]
        for regex in regex_list:
            match = re.search(regex, name)
            if match == None:
                continue

            keyword = match.group('keyword').replace('.', ' ').strip()
            year = int(match.group('year'))

            P.logger.info(f"SEARCH [{keyword}|{year}]")

            if year < 1900 and year > 2030:
                #Task.move_by_status(db_item, "FAIL_IS_NOT_YEAR")
                continue

            meta_module = F.PluginManager.get_plugin_instance('metadata').logic.get_module('movie')
            
            search_data = meta_module.search(keyword, year, site_list=P.ModelSetting.get_list('basic_meta_order', ','))
            
            if len(search_data) >= 1 and search_data[0]['score'] >= 90:
                #P.logger.info(d(search_data[0]))
                db_item.meta = meta_module.info(search_data[0]['code'])

            if db_item.meta == None:
                #Task.move_by_status(db_item, "FAIL_NO_META")
                continue
            db_item.title = db_item.meta['title']
            db_item.title_en = db_item.meta['originaltitle']
            db_item.year = db_item.meta['year']
            db_item.poster = db_item.meta['main_poster']
            db_item.genre = db_item.meta['genre'][0] if len(db_item.meta['genre']) > 0 else '기타'
            db_item.country = db_item.meta['country'][0] if len(db_item.meta['country']) > 0 else '정보없음'
            
            lang = SupportString.language_info(keyword)
            P.logger.debug(f"[keyword] {lang}")
            if lang[0] > 80:
                db_item.is_hangul_title = True

            return
        else:
            Task.move_by_status(db_item, "FAIL_MATCH_META")
            return
            

    def process_find_main_videofile(db_item):
        max_size = 0
        for _file in os.listdir(db_item.source_path):
            filepath = os.path.join(db_item.source_path, _file)
            if os.path.isfile(filepath):
                tmp = os.path.splitext(_file)
                if tmp[1] in ['.mp4', '.mkv']:
                    size = SupportFile.size(filepath)
                    if size > max_size:
                        db_item.main_video_filepath = filepath
                        db_item.main_video_filename = _file
                        max_size = size
        if db_item.main_video_filename != None:
            for _ in P.ModelSetting.get_list('basic_is_hardsub_check', ' '):
                if _ in db_item.main_video_filename:
                    db_item.is_hard_subtitle = True
                    break
            for _ in P.ModelSetting.get_list('basic_is_vod_check', ' '):
                if _ in db_item.main_video_filename:
                    db_item.is_vod = True
                    break
            
            tmp = os.path.splitext(db_item.main_video_filename)
            for ext in ['.smi', '.srt', '.ko.srt', '.ko.smi']:
                _ = os.path.join(db_item.source_parent, '[SUBTITLE]', tmp[0] + ext)
                if os.path.exists(_):
                    shutil.move(_, db_item.source_path)




    def process_movie_folder(db_item):
        PP = F.PluginManager.get_plugin_instance('subtitle_tool')
        ret = PP.SupportSmi2srt.start(db_item.source_path, remake=False, no_remove_smi=False, no_append_ko=False, no_change_ko_srt=False, fail_move_path=None)

        
        ko_sub_file_list = []
        for _file in os.listdir(db_item.source_path):
            remove = False
            filepath = os.path.join(db_item.source_path, _file)
            split = os.path.splitext(_file)
            if os.path.isfile(filepath):
                if split[1].strip('.').lower() in P.ModelSetting.get_list('basic_remove_file_extension', ','):
                    remove = True
                if remove:
                    os.remove(filepath)
                    continue
                if split[1] in ['.smi', '.srt']:
                    db_item.file_subtitle_count += 1
                    if '.ko.' in _file or '.kor.' in _file and _file.startswith(os.path.splitext(db_item.main_video_filename)[0]):
                        db_item.include_kor_file_subttile = True
            else:
                rule = P.ModelSetting.get_list('basic_remove_folder_except_name', ',')
                remove = False
                if len(rule) == 0:
                    remove = True
                else:
                    if rule[0] == 'ALL':
                        remove = True
                    else:
                        if _file in rule:
                            remove = False
                        else:
                            remove = True

                if remove:
                    shutil.rmtree(filepath)

                if _file.lower() in ['subs']:
                    for _ in os.listdir(filepath):
                        if os.path.splitext(_)[1] in ['.smi', '.srt']:
                            if 'korea' in _.lower():
                                db_item.include_kor_file_subttile = True
                                try:
                                    tmp = os.path.splitext(db_item.main_video_filename)
                                    last = os.path.join(db_item.source_path, f"{tmp[0]}.ko.srt")
                                    if os.path.exists(last) == False:
                                        db_item.file_subtitle_count += 1
                                    shutil.copy(os.path.join(filepath, _), last)
                                except:
                                    pass
                            db_item.file_subtitle_count += 1



    def process_probe(db_item):
        db_item.ffprobe = SupportFfprobe.ffprobe(db_item.main_video_filepath)
        if 'format' not in db_item.ffprobe:
            return False
        db_item.video_size = int(db_item.ffprobe['format']['size'])
        vc = 0
        audio_codec_list = []
        subtitle_list = []
        for track in db_item.ffprobe['streams']:
            if track['codec_type'] == 'video':
                vc += 1
                if db_item.video_codec is None:
                    db_item.video_codec = track['codec_name'].upper()
                    db_item.resolution = f"{track['coded_width']}x{track['coded_height']}"
            elif track['codec_type'] == 'audio':
                db_item.audio_count += 1
                if 'tags' in track and 'language' in track['tags']:
                    #P.logger.info(track['tags']['language'])
                    if track['tags']['language'] in ['kor', 'ko']:
                        db_item.include_kor_audio = True
                
                tmp = track['codec_name'].upper()
                if db_item.audio_codec is None:
                    db_item.audio_codec = tmp
                if tmp not in audio_codec_list:
                    audio_codec_list.append(tmp)

            elif track['codec_type'] == 'subtitle':
                db_item.subtitle_count += 1
                if 'tags' in track and 'language' in track['tags']:
                    P.logger.info(track['tags']['language'])
                    if track['tags']['language'] in ['kor', 'ko']:
                        db_item.include_kor_subtitle = True
                    if track['tags']['language'] not in subtitle_list:
                        subtitle_list.append(track['tags']['language'])
            elif track['codec_type'] in ['data', 'attachment']:
                P.logger.debug("코덱 타입이 데이타")
            else:
                P.logger.debug("코덱 타입이 없음")
        db_item.audio_codec_list = ', '.join(audio_codec_list)
        db_item.subtitle_list = ', '.join(subtitle_list)
        #P.logger.debug(f"VC : {vc}")
        return True


    
    def prepare(source):
        subtitle_folder = os.path.join(source, '[SUBTITLE]')
        os.makedirs(subtitle_folder, exist_ok=True)
        error_folder = os.path.join(source, '[ERROR]')
        os.makedirs(error_folder, exist_ok=True)
        child = os.listdir(source)
        for idx, name in enumerate(child):
            try:
                p = os.path.join(source, name)
                tmp = os.path.splitext(name)
                _ = os.path.join(source, tmp[0])
                P.logger.debug(f"PREPARE {idx+1} / {len(child)}")
                if os.path.isfile(p):
                    if tmp[-1] in ['.smi', '.srt']:
                        if os.path.exists(_):
                            shutil.move(p, _)
                        else:
                            shutil.move(p, subtitle_folder)
                    elif tmp[-1] in ['.mkv', '.mp4']:
                        os.makedirs(_, exist_ok=True)
                        shutil.move(p, _)
                    else:
                        wrong = os.path.join(error_folder, 'WRONG_FILE')
                        os.makedirs(wrong, exist_ok=True)
                        shutil.move(p, wrong)
            except Exception as e: 
                P.logger.error(f"Exception:{str(e)}")
                P.logger.error(traceback.format_exc())
        Task.current_subtitle_list = os.listdir(subtitle_folder)

    

    @F.celery.task
    def start():
        Task.config = SupportYaml.read_yaml(os.path.join(F.config['path_data'], 'db', f"{P.package_name}_basic.yaml"))


        source = P.ModelSetting.get('basic_path_source')
        Task.prepare(source)
        child = os.listdir(source)
        for idx, name in enumerate(child):
            P.logger.debug(f"MAIN {idx+1} / {len(child)}")
            try:
                db_item = None
                if name in ['[ERROR]', '[SUBTITLE]']:
                    continue
                P.logger.warning(name)
                db_item = ModelFPMovieItem(source, name)
                
                # 메타
                Task.process_meta(db_item)
                if db_item.meta == None:
                    continue
                
                Task.process_find_main_videofile(db_item)
                if db_item.main_video_filepath == None:
                    Task.move_by_status(db_item, "FAIL_NOT_FIND_VIDEOFILE")
                    continue

                # 폴더구조 처리
                Task.process_movie_folder(db_item)
                # ffprobe
                if Task.process_probe(db_item) == False:
                    Task.move_by_status(db_item, "FAIL_VIDEOFILE_ERROR")
                    continue

                Task.make_target(db_item)
                
                parent = os.path.dirname(db_item.result_folder)
                Task.util_get_duplicate_check(db_item)
                os.makedirs(parent, exist_ok=True)
                shutil.move(db_item.source_path, db_item.result_folder)
                db_item.status = "MOVE"
                #P.logger.warning(d(db_item.as_dict()))
                if P.ModelSetting.get_bool("basic_use_notify"):
                    tmp = db_item.result_folder.replace('\\', '\\\\')
                    msg = f"영화 파일처리\n소스: {db_item.source_name}\n최종폴더: {tmp}\n비디오파일: {db_item.main_video_filename}\n{db_item.log}"
                    ToolNotify.send_message(msg, message_id="fp_movie_basic", image_url=db_item.poster)

                if P.ModelSetting.get_bool("basic_make_info_json"):
                    SupportFile.write_json(os.path.join(db_item.result_folder, 'info.json'), db_item.meta)

                
            except Exception as e: 
                P.logger.error(f"Exception:{str(e)}")
                P.logger.error(traceback.format_exc())
            finally:
                if db_item == None:
                    continue
                db_item.save()
                if db_item.status != 'MOVE':
                    continue
                if Task.config.get('PLEX_MATE_SCAN') != None:
                    for plex_info in Task.config.get('PLEX_MATE_SCAN'):
                        url = f"{plex_info['URL']}/plex_mate/api/scan/do_scan"
                        P.logger.info(f"PLEX_MATE : {url}")
                        plex_target = db_item.result_folder
                        for rule in plex_info.get('경로변경', []):
                            plex_target = plex_target.replace(rule['소스'], rule['타겟'])
                        
                        if plex_target[0] == '/':
                            plex_target = plex_target.replace('\\', '/')
                        else:
                            plex_target = plex_target.replace('/', '\\')
                        data = {
                            'callback_id': f"{P.package_name}_basic_{db_item.id}",
                            'target': plex_target,
                            'apikey': F.SystemModelSetting.get('apikey'),
                            'mode': 'ADD',
                        }
                        res = requests.post(url, data=data)
                        #P.logger.info(res)
                        data = res.json()
                        P.logger.info(f"PLEX SCAN 요청 : {url} {data}")



    def make_target(db_item):
        target_root = None
        target_format = None
        order_list = Task.config.get('타겟 조건 체크 우선순위')
        if order_list != None:
            for condition_name in order_list:
                condition_list = Task.config.get('타겟 설정')
                condiction_data = None
                for _ in condition_list:
                    if _['이름'] == condition_name:
                        condiction_data = _
                        break
                try:
                    mod = imp.new_module('my_code')
                    exec(condiction_data['코드'], mod.__dict__)
                    if mod.check(db_item):
                        db_item.log += f"타겟 조건: {condiction_data['이름']}"
                        target_root = condiction_data['타겟루트']
                        target_format = condiction_data['타겟포맷']
                except Exception as e: 
                    P.logger.error(f'Exception:{str(e)}')
                    P.logger.error(traceback.format_exc())

                if target_root != None:
                    break
        
        if target_root == None:
            #type_a = False
            if db_item.include_kor_subtitle or db_item.is_vod or db_item.file_subtitle_include_kor or db_item.country in ['한국'] or db_item.is_hard_subtitle or db_item.include_kor_file_subttile:
                db_item.log += f"타겟 조건: TYPE A"
                target_root = P.ModelSetting.get('basic_target_root_a')
                target_format = P.ModelSetting.get('basic_target_format_a')
            else:
                db_item.log += f"타겟 조건: TYPE B"
                target_root = P.ModelSetting.get('basic_target_root_b')
                target_format = P.ModelSetting.get('basic_target_format_b')
        

        default_folder_folder = Task.get_folder_folder(db_item)
        try:
            mod = imp.new_module('my_folder_format')
            exec(Task.config['폴더명 형식'], mod.__dict__)
            folder_format = mod.folder_format(default_folder_folder, db_item)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            folder_format = default_folder_folder


        target = target_format.format(**folder_format)

        rules = Task.config.get("타겟포맷 REPLACE 규칙")
        if rules != None and type(rules) == type([]) and len(rules) > 0:
            for rule in rules:
                try:
                    tmp = rule.split('|')
                    target = target.replace(tmp[0], tmp[1])
                except:
                    pass
        
        target = target.split('/')
        db_item.result_folder = os.path.join(target_root, *target)


    def get_folder_folder(db_item):
        data = {}
        data['TITLE'] = SupportFile.text_for_filename(db_item.title)
        data['TITLE_EN'] = SupportFile.text_for_filename(db_item.title_en) if db_item.title_en != None else ''
        data['TITLE_FIRST_CHAR'] = SupportString.get_cate_char_by_first(db_item.title)
        data['YEAR'] = db_item.year
        data['GENRE'] = db_item.genre.replace('/', '')
        data['COUNTRY'] = db_item.country
        data['RESOLUTION'] = db_item.resolution
        data['VIDEO_CODEC'] = db_item.video_codec
        data['AUDIO_CODEC'] = db_item.audio_codec
        data['AUDIO_COUNT'] = db_item.audio_count
        data['INCLUDE_KOR_AUDIO'] = "K" if db_item.include_kor_audio else ""
        data['SUBTITLE_COUNT'] = db_item.subtitle_count
        data['INCLUDE_KOR_SUBTITLE'] = "K" if db_item.include_kor_subtitle else ""
        data['FILE_SUBTITLE_COUNT'] = db_item.file_subtitle_count
        data['INCLUDE_KOR_FILE_SUBTITLE'] = "K" if db_item.include_kor_file_subttile else ""
        data['ORIGINAL'] = db_item.source_name
        return data
        

    def util_get_duplicate_check(db_item):
        basename = os.path.basename(db_item.result_folder)
        parent = os.path.dirname(db_item.result_folder)
        count = 0
        while True:
            if os.path.exists(db_item.result_folder):
                count += 1
                db_item.result_folder = os.path.join(parent, basename + f' [{count}]')
            else:
                return

    def move_by_status(db_item, status):
        db_item.status = status
        P.logger.error(f"STATUS: {status}")
        target = os.path.join(db_item.source_parent, '[ERROR]', status)
        db_item.result_folder = os.path.join(target, db_item.source_name)
        os.makedirs(target, exist_ok=True)
        shutil.move(db_item.source_path, target)
