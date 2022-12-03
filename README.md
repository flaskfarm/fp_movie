### 영화 파일처리

파일명, 폴더명 기반으로 메타데이터를 검색하여 적절하게 파일을 이동한다.  
메타 확인용 플러그인과 비디오 파일 분석을 위한 플러그인 필요.

  - 사용 플러그인 
    - 메타데이터 
    - SUPPORT SITE
    - FFMPEG : ffprobe 설정 확인
    - 자막 툴
  
<br><br>  



### 기본 설정

Web UI는 타겟 타입A, 타입B에 대한 설정만 있다.  
필요한 경우 세부 설정은 yaml파일로 한다.

⦁ TYPE A : 즉시 시청 가능 영상
  - 파일명 체크시 VOD 분류
  - 파일명 체크시 HARD SUBTILE 분류
  - 메타 국가 한국
  - 비디오파일에 한국어 자막 포함
  - 한국어 자막 파일이 존재

⦁ TYPE B : TYPE A가 아닌 경우 (자막 필요한 외국 영화)


<br><br>

### 고급 설정

#### 1. 타겟 설정

  영화 파일 정리 구조는 개인 취향이기 때문에 모든 경우에 대해서 처리 루틴을 제공할 수 없다.  
  그래서 본인이 원하는 구조로 정리를 위해서는 조건 처리를 할 수 있는 코드를 본인이 직접 작성해야 한다.

  `db_item` 에 대한 세부 정보는 파일처리 결과 화면의 JSON 버튼으로 구조를 확인 할 수 있다.

##### 1.1 샘플
  ```yaml
  타겟 설정:
    - 이름: "타겟조건 국내영화"
      타겟루트: "M:\\라이브러리\\국내"
      타겟포맷: "{TITLE} ({YEAR}) [{COUNTRY}-{GENRE}-{RESOLUTION}-{VIDEO_CODEC}-{AUDIO_CODEC}.{AUDIO_COUNT}{INCLUDE_KOR_AUDIO}-{SUBTITLE_COUNT}{INCLUDE_KOR_SUBTITLE}.{FILE_SUBTITLE_COUNT}{INCLUDE_KOR_FILE_SUBTITLE}]"
      코드: |
        def check(db_item):
          if db_item.country in ['한국']:
            return True

    - 이름: "타겟조건 19금"
      타겟루트: "M:\\라이브러리\\청소년관람불가"
      타겟포맷: "{TITLE} ({YEAR})"
      코드: |
        def check(db_item):
          if db_item.meta.get('mpaa') in ['청소년관람불가', '청소년 관람불가']: 
            return True
  ```
  `타겟 설정` 에 선언.  
  코드는 `check` 함수로 조건에 맞는 경우 `True` 리턴하고, `True`시 사용할 `타겟루트`, `타겟포맷` 값을 사용한다.

##### 2.2 조건 사용 우선순위
  ```
  타겟 조건 체크 우선순위:
    - "타겟조건 UHD 외국영화 한국어자막 내장"
    - "타겟조건 외국영화 한국어자막 내장"
    - "타겟조건 외국영화 한국어 음성(더빙)"
    - "타겟조건 국내영화"
  ```

  사용은 `타겟 설정`에서 사용한 `이름` 값 목록을 `타겟 조건 체크 우선순위`에 순서대로 넣으며 순차적으로 조건을 체크하여 True인 경우의 타겟 설정을 따르게 된다.

  예를 들어 
  ```
  - 타겟조건 미국영화
  - 타겟조건 UHD영화
  ```

  이런 조건이 선언되어 있고 영화가 둘다 매칭되더라도 먼저 매칭된 `미국영화`의 설정 값을 사용한다.

  모든 조건이 False인 경우 기본 설정인 TYPE A, TYPE B 값이 적용된다.

<br><br>

#### 2. 폴더명 포맷

##### 2.1 내부 선언된 형식
  1. 메타관련
    - `TITLE` : 제목
    - `TITLE_EN` : 영문제목
    - `TITLE_FIRST_CHAR` : 제목 첫 글자의 범위 (가, 나, 다...)
    - `YEAR` : 제작년도
    - `GENRE` : 장르. 여러 장르인 경우 첫번째 값.
    - `COUNTRY` : 국가
  2. 비디오파일 관련
    - `RESOLUTION` : 해상도 예)1920x1080 
    - `VIDEO_CODEC` : 비디오 코덱
    - `AUDIO_CODEC` : 오디오 코덱(첫번째)
    - `AUDIO_COUNT` : 오디오 스트림 수
    - `INCLUDE_KOR_AUDIO` : 한국어 오딩이 있는 겅우 `K` 없으면 빈값
    - `SUBTITLE_COUNT` : 내장 자막 수
  3. 기타
    - `INCLUDE_KOR_SUBTITLE` : 한국어 자막이 있는 경우 `K` 없으면 빈값
    - `FILE_SUBTITLE_COUNT` : 폴더 내 자막파일 수
    - `INCLUDE_KOR_FILE_SUBTITLE` : 한걱우 자막 파일이 있는 `K` 없으면 빈값
    - `ORIGINAL` : 원본 폴더명
    - / : 폴더 구분자


##### 2.2 yaml를 통해 형식 추가

  `folder_format` 함수를 구현하며 인자로 받은 `data`에 추가 형식을 설정한 후 리턴한다.


  ```
  폴더명 형식: |
    def folder_format(data, db_item):
      width = int(db_item.resolution.split('x')[0])
      if width == 1920: ret = 'FHD'
      elif width > 1920: ret = 'FHD'
      elif width < 1920 and width >= 1280: ret = 'HD'
      else: ret = 'SD'
      data['MY_RESOLUTION'] = ret

      if db_item.country in ['미국', '영국']: ret = '서양'
      elif db_item.country in ['일본', '중국']: ret = '동양'
      elif db_item.country == '한국': ret = '한국'
      else ret = '기타'
      data['COUNTRY_GROUP'] = ret
      return data
  ```
  
  예제처럼 설정 후 `MY_RESOLUTION`, `COUNTRY_GROUP` 을 사용하여 타겟포맷을 설정  
  - 타겟포맷 : `"{COUNTRY_GROUP}/{TITLE_FIRST_CHAR}/{TITLE} [{TITLE_EN}] ({YEAR}) [{COUNTRY}-{GENRE}-{MY_RESOLUTION}]"`
  - 결과 : `서양\0Z\8미리 [8MM] (1999) [미국-범죄-FHD]`


<br><br>

##### 3. 타겟포맷 REPLACE 규칙

포맷에 "[{TITLE_EN}]" 형식이 있는 경우 영문 제목이 없는 영화는 `[]`으로만 나온다.  
이런 경우를 대비하여 `타겟포맷 REPLACE 규칙`에서 "[]|" 정도를 설정하면 "[]" 값이 없어진다.

```
타겟포맷 REPLACE 규칙:
  - ".1-|-"
  - ".1K-|K-"
  - "-0.0]|]"
  - " [] | "

```
구분자는 | 으로 A|B 설정시 `target = target.replace(A, B)`코드 실행



