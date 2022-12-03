from .setup import *


class ModelFPMovieItem(ModelBase):
    P = P
    __tablename__ = 'fp_movie_item'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = P.package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    
    status = db.Column(db.String)

    is_hangul_title = db.Column(db.Boolean)
    source_name = db.Column(db.String)
    source_parent = db.Column(db.String)
    source_path = db.Column(db.String)
    main_video_filepath = db.Column(db.String)
    main_video_filename = db.Column(db.String)
    file_subtitle_count = db.Column(db.String)
    include_kor_file_subttile = db.Column(db.String)
    result_folder = db.Column(db.String)
    is_hard_subtitle = db.Column(db.String)

    meta = db.Column(db.JSON)
    title = db.Column(db.String)
    title_en = db.Column(db.String)
    year = db.Column(db.String)
    poster = db.Column(db.String)
    genre = db.Column(db.String)
    country = db.Column(db.String)
    is_vod = db.Column(db.Boolean)

    ffprobe = db.Column(db.JSON)
    resolution = db.Column(db.String)
    video_codec = db.Column(db.String)
    audio_codec = db.Column(db.String)
    audio_codec_list = db.Column(db.String)
    audio_count = db.Column(db.Integer)
    include_kor_audio = db.Column(db.Boolean)
    video_size = db.Column(db.Integer)
    subtitle_count = db.Column(db.Integer)
    subtitle_list = db.Column(db.String)
    include_kor_subtitle = db.Column(db.Boolean)

   

    def __init__(self, parent, name):
        self.created_time = datetime.now()
        self.log = ''
        self.audio_count = 0
        self.subtitle_count = 0
        self.include_kor_audio = False
        self.include_kor_subtitle = False
        self.file_subtitle_count = 0
        self.file_subtitle_include_kor = False
        self.is_hard_subtitle = False

        self.source_parent = parent
        self.source_name = name
        
        self.source_path = os.path.join(parent, name)
        if os.path.isdir(self.source_path):
            self.is_file = False
            self.is_folder = True
        elif os.path.isfile(self.source_path):
            self.is_file = True
            self.is_folder = False


    @classmethod
    def make_query(cls, req, order='desc', search='', option1='all', option2='all'):
        with F.app.app_context():
            query1 = cls.make_query_search(F.db.session.query(cls), search, cls.title)
            
            query = query1 
            if option1 != 'all':
                query = query.filter(cls.status == option1)
            #if option2 != 'all':
            #    query = query.filter(cls.status == option2)
            
            if order == 'desc':
                query = query.order_by(desc(cls.id))
            else:
                query = query.order_by(cls.id)
            return query
