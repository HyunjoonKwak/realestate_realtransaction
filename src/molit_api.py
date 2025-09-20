#!/usr/bin/env python3
"""
국토교통부 부동산 실거래가 API 연동 모듈
"""

import requests
import xml.etree.ElementTree as ET
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import os
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed

class MolitRealEstateAPI:
    """국토교통부 부동산 실거래가 API 클래스"""

    def __init__(self, service_key: str = None):
        """
        Args:
            service_key: 국토교통부 공공데이터포털에서 발급받은 서비스키
                        https://www.data.go.kr/ 에서 신청 가능
        """
        if not service_key:
            raise ValueError("MOLIT API 서비스키가 필요합니다. .env 파일에 MOLIT_API_KEY를 설정해주세요.")
        
        self.service_key = service_key
        self.base_url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
        self.rent_base_url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
        self.rent_url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"

        # 환경 변수에서 설정 로드
        self.request_delay = float(os.getenv('API_REQUEST_DELAY', '0.05'))
        self.timeout = int(os.getenv('API_TIMEOUT', '15'))
        self.max_retries = int(os.getenv('API_MAX_RETRIES', '3'))

        # 로깅 설정 - 전역 설정을 덮어쓰지 않도록 수정
        self.logger = logging.getLogger(__name__)

        # 로거가 이미 설정되어 있지 않은 경우에만 핸들러 추가
        if not self.logger.handlers:
            log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
            self.logger.setLevel(getattr(logging, log_level, logging.INFO))

            # 콘솔 핸들러 추가
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, log_level, logging.INFO))
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # 중복 출력 방지
            self.logger.propagate = False

        # 시-군-구 계층적 지역 데이터 구조
        self.region_hierarchy = {
            '강원특별자치도': {
                '강릉시': '51150',
                '고성군': '51820',
                '동해시': '51170',
                '삼척시': '51230',
                '속초시': '51210',
                '양구군': '51800',
                '양양군': '51830',
                '영월군': '51750',
                '원주시': '51130',
                '인제군': '51810',
                '정선군': '51770',
                '철원군': '51780',
                '춘천시': '51110',
                '태백시': '51190',
                '평창군': '51760',
                '홍천군': '51720',
                '화천군': '51790',
                '횡성군': '51730',
            },
            '경기도': {
                '가평군': '41820',
                '고양시': {
                    '_main': '41280',
                    '덕양구': '41281',
                    '일산동구': '41285',
                    '일산서구': '41287',
                },
                '과천시': '41290',
                '광명시': '41210',
                '광주시': '41610',
                '구리시': '41310',
                '군포시': '41410',
                '김포시': '41570',
                '남양주시': '41360',
                '동두천시': '41250',
                '부천시': '41190',
                '성남시': {
                    '_main': '41130',
                    '분당구': '41135',
                    '수정구': '41131',
                    '중원구': '41133',
                },
                '수원시': {
                    '_main': '41110',
                    '권선구': '41113',
                    '영통구': '41117',
                    '장안구': '41111',
                    '팔달구': '41115',
                },
                '시흥시': '41390',
                '안산시': {
                    '_main': '41270',
                    '단원구': '41273',
                    '상록구': '41271',
                },
                '안성시': '41550',
                '안양시': {
                    '_main': '41170',
                    '동안구': '41173',
                    '만안구': '41171',
                },
                '양주시': '41630',
                '양평군': '41830',
                '여주시': '41670',
                '연천군': '41800',
                '오산시': '41370',
                '용인시': {
                    '_main': '41460',
                    '기흥구': '41463',
                    '수지구': '41465',
                    '처인구': '41461',
                },
                '의왕시': '41430',
                '의정부시': '41150',
                '이천시': '41500',
                '파주시': '41480',
                '평택시': '41220',
                '포천시': '41650',
                '하남시': '41450',
                '화성시': '41590',
            },
            '경상남도': {
                '거제시': '48310',
                '거창군': '48880',
                '고성군': '48820',
                '김해시': '48250',
                '남해군': '48840',
                '밀양시': '48270',
                '사천시': '48240',
                '산청군': '48860',
                '양산시': '48330',
                '의령군': '48720',
                '진주시': '48170',
                '창녕군': '48740',
                '창원시': {
                    '_main': '48120',
                    '마산합포구': '48125',
                    '마산회원구': '48127',
                    '성산구': '48123',
                    '의창구': '48121',
                    '진해구': '48129',
                },
                '통영시': '48220',
                '하동군': '48850',
                '함안군': '48730',
                '함양군': '48870',
                '합천군': '48890',
            },
            '경상북도': {
                '경산시': '47290',
                '경주시': '47130',
                '고령군': '47830',
                '구미시': '47190',
                '김천시': '47150',
                '문경시': '47280',
                '봉화군': '47920',
                '상주시': '47250',
                '성주군': '47840',
                '안동시': '47170',
                '영덕군': '47770',
                '영양군': '47760',
                '영주시': '47210',
                '영천시': '47230',
                '예천군': '47900',
                '울릉군': '47940',
                '울진군': '47930',
                '의성군': '47730',
                '청도군': '47820',
                '청송군': '47750',
                '칠곡군': '47850',
                '포항시': {
                    '_main': '47110',
                    '남구': '47111',
                    '북구': '47113',
                },
            },
            '광주광역시': {
                '광산구': '29200',
                '남구': '29155',
                '동구': '29110',
                '북구': '29170',
                '서구': '29140',
            },
            '대구광역시': {
                '군위군': '27720',
                '남구': '27200',
                '달서구': '27290',
                '달성군': '27710',
                '동구': '27140',
                '북구': '27230',
                '서구': '27170',
                '수성구': '27260',
                '중구': '27110',
            },
            '대전광역시': {
                '대덕구': '30230',
                '동구': '30110',
                '서구': '30170',
                '유성구': '30200',
                '중구': '30140',
            },
            '부산광역시': {
                '강서구': '26440',
                '금정구': '26410',
                '기장군': '26710',
                '남구': '26290',
                '동구': '26170',
                '동래구': '26260',
                '부산진구': '26230',
                '북구': '26320',
                '사상구': '26530',
                '사하구': '26380',
                '서구': '26140',
                '수영구': '26500',
                '연제구': '26470',
                '영도구': '26200',
                '중구': '26110',
                '해운대구': '26350',
            },
            '서울특별시': {
                '강남구': '11680',
                '강동구': '11740',
                '강북구': '11305',
                '강서구': '11500',
                '관악구': '11620',
                '광진구': '11215',
                '구로구': '11530',
                '금천구': '11545',
                '노원구': '11350',
                '도봉구': '11320',
                '동대문구': '11230',
                '동작구': '11590',
                '마포구': '11440',
                '서대문구': '11410',
                '서초구': '11650',
                '성동구': '11200',
                '성북구': '11290',
                '송파구': '11710',
                '양천구': '11470',
                '영등포구': '11560',
                '용산구': '11170',
                '은평구': '11380',
                '종로구': '11110',
                '중구': '11140',
                '중랑구': '11260',
            },
            '세종특별자치시': {
                '세종시': '36110'
            },
            '울산광역시': {
                '남구': '31140',
                '동구': '31170',
                '북구': '31200',
                '울주군': '31710',
                '중구': '31110',
            },
            '인천광역시': {
                '강화군': '28710',
                '계양구': '28245',
                '남동구': '28200',
                '동구': '28140',
                '미추홀구': '28177',
                '부평구': '28237',
                '서구': '28260',
                '연수구': '28185',
                '옹진군': '28720',
                '중구': '28110',
            },
            '전라남도': {
                '강진군': '46810',
                '고흥군': '46770',
                '곡성군': '46720',
                '광양시': '46230',
                '구례군': '46730',
                '나주시': '46170',
                '담양군': '46710',
                '목포시': '46110',
                '무안군': '46840',
                '보성군': '46780',
                '순천시': '46150',
                '신안군': '46910',
                '여수시': '46130',
                '영광군': '46870',
                '영암군': '46830',
                '완도군': '46890',
                '장성군': '46880',
                '장흥군': '46800',
                '진도군': '46900',
                '함평군': '46860',
                '해남군': '46820',
                '화순군': '46790',
            },
            '전북특별자치도': {
                '고창군': '52790',
                '군산시': '52130',
                '김제시': '52210',
                '남원시': '52190',
                '무주군': '52730',
                '부안군': '52800',
                '순창군': '52770',
                '완주군': '52710',
                '익산시': '52140',
                '임실군': '52750',
                '장수군': '52740',
                '전주시': {
                    '_main': '52110',
                    '덕진구': '52113',
                    '완산구': '52111',
                },
                '정읍시': '52180',
                '진안군': '52720',
            },
            '제주특별자치도': {
                '서귀포시': '50130',
                '제주시': '50110',
            },
            '충청남도': {
                '계룡시': '44250',
                '공주시': '44150',
                '금산군': '44710',
                '논산시': '44230',
                '당진시': '44270',
                '보령시': '44180',
                '부여군': '44760',
                '서산시': '44210',
                '서천군': '44770',
                '아산시': '44200',
                '예산군': '44810',
                '천안시': {
                    '_main': '44130',
                    '동남구': '44131',
                    '서북구': '44133',
                },
                '청양군': '44790',
                '태안군': '44825',
                '홍성군': '44800',
            },
            '충청북도': {
                '괴산군': '43760',
                '단양군': '43800',
                '보은군': '43720',
                '영동군': '43740',
                '옥천군': '43730',
                '음성군': '43770',
                '제천시': '43150',
                '증평군': '43745',
                '진천군': '43750',
                '청주시': {
                    '_main': '43110',
                    '상당구': '43111',
                    '서원구': '43112',
                    '청원구': '43114',
                    '흥덕구': '43113',
                },
                '충주시': '43130',
            },
        }

        # 기존 호환성을 위한 단순 매핑도 유지
        self.region_codes = {}
        for city, districts in self.region_hierarchy.items():
            for district, code_or_dict in districts.items():
                if isinstance(code_or_dict, str):
                    # 단순 코드
                    self.region_codes[code_or_dict] = f"{city} {district}"
                elif isinstance(code_or_dict, dict):
                    # 중첩된 구조
                    for sub_district, sub_code in code_or_dict.items():
                        if sub_district == '_main':
                            self.region_codes[sub_code] = f"{city} {district}"
                        else:
                            self.region_codes[sub_code] = f"{city} {district} {sub_district}"

        # HTTP 세션 초기화 (재사용을 위해)
        self._init_http_session()

    def _init_http_session(self):
        """HTTP 세션 초기화"""
        self.session = requests.Session()

        # 기본 헤더 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/xml, text/xml, */*',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive'
        })

        # SSL 검증 활성화
        self.session.verify = True

        # SSL/TLS 설정을 위한 추가 구성
        try:
            import ssl
            import urllib3
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            from urllib3.util.ssl_ import create_urllib3_context

            # 정부 API와 호환되는 SSL 컨텍스트 생성
            context = create_urllib3_context()
            context.set_ciphers('DEFAULT@SECLEVEL=1')  # 보안 레벨을 낮춰서 호환성 향상
            context.minimum_version = ssl.TLSVersion.TLSv1_2  # TLS 1.2 이상 사용

            retry_strategy = Retry(
                total=self.max_retries,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"],
                backoff_factor=1
            )

            # SSL 컨텍스트를 사용하는 HTTPAdapter 생성
            class SSLAdapter(HTTPAdapter):
                def init_poolmanager(self, *args, **kwargs):
                    kwargs['ssl_context'] = context
                    return super().init_poolmanager(*args, **kwargs)

            adapter = SSLAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)

            self.logger.debug("HTTP 세션 초기화 완료")
        except Exception as e:
            self.logger.warning(f"HTTP 어댑터 설정 실패: {e}")

    def get_region_name(self, region_code: str) -> str:
        """지역코드로 지역명 조회"""
        return self.region_codes.get(region_code, f"지역코드 {region_code}")

    def get_apt_trade_data(self, lawd_cd: str, deal_ymd: str, page_no: int = 1, num_of_rows: int = 1000) -> Dict:
        """
        아파트 실거래가 데이터 조회

        Args:
            lawd_cd: 지역코드 (예: 11110)
            deal_ymd: 거래년월 (예: 202506)
            page_no: 페이지 번호 (기본값: 1)
            num_of_rows: 한 페이지 결과 수 (기본값: 100)

        Returns:
            실거래 데이터 딕셔너리
        """
        try:
            # Rate Limiting 적용
            self._rate_limit()
            
            # API URL 구성
            url = f"{self.base_url}?serviceKey={self.service_key}&LAWD_CD={lawd_cd}&DEAL_YMD={deal_ymd}&pageNo={page_no}&numOfRows={num_of_rows}"

            self.logger.info(f"🏢 국토교통부 API 호출: 지역={lawd_cd}({self.get_region_name(lawd_cd)}), 기간={deal_ymd}")
            self.logger.info(f"📊 요청 파라미터: 페이지={page_no}, 조회건수={num_of_rows}")
            self.logger.debug(f"🔗 전체 URL: {url}")

            # 재사용 가능한 세션 사용
            # SSL 검증으로 먼저 시도
            try:
                response = self.session.get(url, timeout=self.timeout)
            except requests.exceptions.SSLError as ssl_error:
                self.logger.warning(f"SSL 인증서 오류 발생, 인증서 검증 비활성화로 재시도: {ssl_error}")
                # SSL 오류 시에만 검증 비활성화
                import urllib3
                original_verify = self.session.verify
                self.session.verify = False
                try:
                    with urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning):
                        response = self.session.get(url, timeout=self.timeout)
                finally:
                    # 원래 설정 복원
                    self.session.verify = original_verify
            except requests.exceptions.ConnectionError as conn_error:
                self.logger.error(f"연결 오류: {conn_error}")
                raise

            # 응답 상태 확인
            self.logger.info(f"HTTP 상태코드: {response.status_code}")
            
            if response.status_code == 200:
                return self._parse_xml_response(response.text, lawd_cd, deal_ymd)
            else:
                self.logger.error(f"HTTP 오류: {response.status_code}")
                return {
                    'success': False,
                    'error': f'HTTP 오류: {response.status_code}',
                    'data': [],
                    'total_count': 0
                }

        except Exception as e:
            self.logger.error(f"API 호출 실패: {e}")
            self.logger.info("데모 데이터로 대체합니다.")
            return self._get_demo_transaction_data(lawd_cd, deal_ymd)

    def _parse_xml_response(self, xml_content: str, lawd_cd: str, deal_ymd: str) -> Dict:
        """XML 응답 파싱"""
        try:
            root = ET.fromstring(xml_content)
            
            # 결과 코드 확인
            result_code = root.find('.//resultCode')
            result_msg = root.find('.//resultMsg')
            
            # resultCode가 없거나 '000'이 아닌 경우에만 오류 처리
            if result_code is not None and result_code.text and result_code.text != '000':
                error_msg = result_msg.text if result_msg is not None else '알 수 없는 오류'
                self.logger.error(f"API 오류: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'data': [],
                    'total_count': 0
                }
            
            # resultMsg가 'OK'인 경우는 정상 응답으로 처리
            if result_msg is not None and result_msg.text == 'OK':
                self.logger.info("API 정상 응답: OK")

            # 데이터 파싱
            items = root.findall('.//item')
            transactions = []
            
            for item in items:
                # 거래일 생성 및 유효성 검사 - 예외 처리 추가
                try:
                    deal_year = int(self._get_xml_text(item, 'dealYear', '0'))
                    deal_month = int(self._get_xml_text(item, 'dealMonth', '0'))
                    deal_day = int(self._get_xml_text(item, 'dealDay', '0'))

                    # 유효한 날짜 범위 검사
                    if not (1900 <= deal_year <= 2100):
                        self.logger.warning(f"유효하지 않은 연도: {deal_year}")
                        continue
                    if not (1 <= deal_month <= 12):
                        self.logger.warning(f"유효하지 않은 월: {deal_month}")
                        continue
                    if not (1 <= deal_day <= 31):
                        self.logger.warning(f"유효하지 않은 일: {deal_day}")
                        continue

                    deal_date = f"{deal_year}-{deal_month:0>2}-{deal_day:0>2}"
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"날짜 파싱 오류: {e}, 해당 거래 건너뜀")
                    continue
                
                # 미래 거래일 필터링
                from datetime import datetime
                try:
                    deal_datetime = datetime.strptime(deal_date, '%Y-%m-%d')
                    if deal_datetime > datetime.now():
                        self.logger.warning(f"미래 거래일 필터링: {deal_date}")
                        continue
                except:
                    self.logger.warning(f"잘못된 거래일 형식: {deal_date}")
                    continue
                
                # 숫자 필드들에 안전한 파싱 적용
                try:
                    build_year = int(self._get_xml_text(item, 'buildYear', '0'))
                    exclusive_area = float(self._get_xml_text(item, 'excluUseAr', '0'))
                    floor = int(self._get_xml_text(item, 'floor', '0'))
                    deal_amount = self._parse_amount(self._get_xml_text(item, 'dealAmount'))

                    # 데이터 유효성 검사
                    if build_year < 1900 or build_year > 2100:
                        self.logger.warning(f"유효하지 않은 건축년도: {build_year}")
                        build_year = 0
                    if exclusive_area < 0 or exclusive_area > 1000:  # 1000㎡ 이상은 비정상적
                        self.logger.warning(f"유효하지 않은 전용면적: {exclusive_area}")
                        exclusive_area = 0
                    if floor < 0 or floor > 200:  # 200층 이상은 비정상적
                        self.logger.warning(f"유효하지 않은 층수: {floor}")
                        floor = 0

                except (ValueError, TypeError) as e:
                    self.logger.warning(f"숫자 필드 파싱 오류: {e}, 기본값 사용")
                    build_year = 0
                    exclusive_area = 0
                    floor = 0
                    deal_amount = 0

                transaction = {
                    'apt_dong': self._get_xml_text(item, 'aptDong'),
                    'apt_name': self._get_xml_text(item, 'aptNm'),
                    'apt_seq': self._get_xml_text(item, 'aptSeq'),
                    'bonbun': self._get_xml_text(item, 'bonbun'),
                    'bubun': self._get_xml_text(item, 'bubun'),
                    'build_year': build_year,
                    'buyer_gbn': self._get_xml_text(item, 'buyerGbn'),
                    'cdeal_type': self._get_xml_text(item, 'cdealType'),
                    'deal_amount': deal_amount,
                    'deal_day': deal_day,
                    'deal_month': deal_month,
                    'deal_year': deal_year,
                    'dealing_gbn': self._get_xml_text(item, 'dealingGbn'),
                    'estate_agent_sgg_nm': self._get_xml_text(item, 'estateAgentSggNm'),
                    'exclusive_area': exclusive_area,
                    'floor': floor,
                    'jibun': self._get_xml_text(item, 'jibun'),
                    'road_name': self._get_xml_text(item, 'roadNm'),
                    'road_name_bonbun': self._get_xml_text(item, 'roadNmBonbun'),
                    'road_name_bubun': self._get_xml_text(item, 'roadNmBubun'),
                    'sgg_cd': self._get_xml_text(item, 'sggCd'),
                    'sler_gbn': self._get_xml_text(item, 'slerGbn'),
                    'umd_cd': self._get_xml_text(item, 'umdCd'),
                    'umd_nm': self._get_xml_text(item, 'umdNm'),
                    'region_code': lawd_cd,
                    'region_name': self.get_region_name(lawd_cd),
                    'deal_date': deal_date,
                    'price_per_area': 0,  # 계산해서 추가
                    # 추가 필드들 - 빈 값이어도 파싱
                    'rgs_date': self._get_xml_text(item, 'rgsDate'),  # 등기일자
                    'cancel_deal_type': self._get_xml_text(item, 'cancelDealType'),  # 해제여부
                    'cancel_deal_day': self._get_xml_text(item, 'cancelDealDay'),  # 해제사유발생일
                    'req_gbn': self._get_xml_text(item, 'reqGbn'),  # 거래유형
                    'house_type': self._get_xml_text(item, 'houseType'),  # 주택유형
                }
                
                # 평당 가격 계산
                if transaction['exclusive_area'] > 0:
                    transaction['price_per_area'] = (transaction['deal_amount'] * 10000) / transaction['exclusive_area']
                
                transactions.append(transaction)

            # 총 개수 확인
            total_count = root.find('.//totalCount')
            total_count_value = int(total_count.text) if total_count is not None else len(transactions)

            if len(transactions) == 0:
                self.logger.info(f"해당 기간({deal_ymd})에 거래 데이터가 없습니다.")
                return {
                    'success': True,
                    'data': [],
                    'total_count': 0,
                    'region_code': lawd_cd,
                    'region_name': self.get_region_name(lawd_cd),
                    'deal_ymd': deal_ymd,
                    'message': '해당 기간에 거래 데이터가 없습니다.'
                }
            else:
                self.logger.info(f"✅ {len(transactions)}건의 실거래 데이터 수집완료 (API 총 {total_count_value}건)")

                # totalCount와 파싱된 데이터 개수 차이 로깅
                if total_count_value > len(transactions):
                    self.logger.warning(f"⚠️ totalCount({total_count_value})와 파싱된 데이터({len(transactions)})에 차이가 있습니다.")
                    self.logger.warning("일부 데이터가 파싱 중 스킵되었을 수 있습니다.")

                if transactions:
                    # 거래 데이터 요약 정보 표시
                    apt_names = list(set([tx.get('apt_name', '') for tx in transactions if tx.get('apt_name')]))
                    self.logger.info(f"📍 포함된 아파트 단지: {len(apt_names)}개 ({', '.join(apt_names[:3])}{'...' if len(apt_names) > 3 else ''})")

                    # 가격 범위 정보
                    prices = [tx.get('deal_amount', 0) for tx in transactions if tx.get('deal_amount')]
                    if prices:
                        min_price = min(prices) / 10000  # 만원 단위
                        max_price = max(prices) / 10000
                        avg_price = sum(prices) / len(prices) / 10000
                        self.logger.info(f"💰 거래가격 범위: {min_price:,.0f}만원 ~ {max_price:,.0f}만원 (평균: {avg_price:,.0f}만원)")

                return {
                    'success': True,
                    'data': transactions,
                    'total_count': total_count_value,
                    'parsed_count': len(transactions),  # 실제 파싱된 개수 추가
                    'region_code': lawd_cd,
                    'region_name': self.get_region_name(lawd_cd),
                    'deal_ymd': deal_ymd
                }

        except ET.ParseError as e:
            self.logger.error(f"XML 파싱 오류: {e}")
            return {
                'success': False,
                'error': f'XML 파싱 오류: {e}',
                'data': [],
                'total_count': 0
            }

    def get_all_apt_trade_data(self, lawd_cd: str, deal_ymd: str, num_of_rows: int = 1000) -> Dict:
        """
        아파트 매매 전체 데이터 조회 (모든 페이지)

        Args:
            lawd_cd: 지역코드
            deal_ymd: 거래년월
            num_of_rows: 페이지당 조회 건수 (최대 1000)

        Returns:
            전체 매매 데이터 딕셔너리
        """
        all_transactions = []
        page_no = 1
        total_count_from_api = 0

        while True:
            # 페이지별 데이터 조회
            result = self.get_apt_trade_data(lawd_cd, deal_ymd, page_no, num_of_rows)

            if not result.get('success'):
                self.logger.error(f"매매 데이터 조회 실패 (페이지 {page_no}): {result.get('error')}")
                break

            transactions = result.get('data', [])
            if not transactions:
                # 더 이상 데이터가 없으면 종료
                break

            all_transactions.extend(transactions)

            # 첫 페이지에서 전체 건수 확인
            if page_no == 1:
                total_count_from_api = result.get('total_count', 0)
                self.logger.info(f"📊 매매 데이터 전체 건수: {total_count_from_api}건, 페이지당 {num_of_rows}건씩 수집")

            # 수집된 데이터가 전체 건수와 같거나 페이지당 데이터가 num_of_rows보다 적으면 종료
            if len(all_transactions) >= total_count_from_api or len(transactions) < num_of_rows:
                break

            page_no += 1
            self.logger.info(f"📄 매매 데이터 페이지 {page_no} 수집 중... (현재까지 {len(all_transactions)}건)")

        self.logger.info(f"✅ 매매 데이터 전체 수집 완료: {len(all_transactions)}건 (API 총 {total_count_from_api}건)")

        return {
            'success': True,
            'data': all_transactions,
            'total_count': len(all_transactions),
            'api_total_count': total_count_from_api,
            'pages_fetched': page_no
        }

    def get_all_apt_rent_data(self, lawd_cd: str, deal_ymd: str, num_of_rows: int = 1000) -> Dict:
        """
        아파트 전월세 전체 데이터 조회 (모든 페이지)

        Args:
            lawd_cd: 지역코드
            deal_ymd: 거래년월
            num_of_rows: 페이지당 조회 건수 (최대 1000)

        Returns:
            전체 전월세 데이터 딕셔너리
        """
        all_transactions = []
        page_no = 1
        total_count_from_api = 0

        while True:
            # 페이지별 데이터 조회
            result = self.get_apt_rent_data(lawd_cd, deal_ymd, page_no, num_of_rows)

            if not result.get('success'):
                self.logger.error(f"전월세 데이터 조회 실패 (페이지 {page_no}): {result.get('error')}")
                break

            transactions = result.get('data', [])
            if not transactions:
                # 더 이상 데이터가 없으면 종료
                break

            all_transactions.extend(transactions)

            # 첫 페이지에서 전체 건수 확인
            if page_no == 1:
                total_count_from_api = result.get('total_count', 0)
                self.logger.info(f"📊 전월세 데이터 전체 건수: {total_count_from_api}건, 페이지당 {num_of_rows}건씩 수집")

            # 수집된 데이터가 전체 건수와 같거나 페이지당 데이터가 num_of_rows보다 적으면 종료
            if len(all_transactions) >= total_count_from_api or len(transactions) < num_of_rows:
                break

            page_no += 1
            self.logger.info(f"📄 전월세 데이터 페이지 {page_no} 수집 중... (현재까지 {len(all_transactions)}건)")

        self.logger.info(f"✅ 전월세 데이터 전체 수집 완료: {len(all_transactions)}건 (API 총 {total_count_from_api}건)")

        return {
            'success': True,
            'data': all_transactions,
            'total_count': len(all_transactions),
            'api_total_count': total_count_from_api,
            'pages_fetched': page_no
        }

    def get_multiple_months_data(self, lawd_cd: str, months: int = 6, start_date: str = None, end_date: str = None, progress_callback=None) -> List[Dict]:
        """여러 개월 실거래 데이터 조회"""
        all_transactions = []
        
        if start_date and end_date:
            # 날짜 범위로 조회
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            current = start.replace(day=1)  # 월의 첫째 날로 설정
            while current <= end:
                deal_ymd = current.strftime("%Y%m")
                result = self.get_combined_apt_data(lawd_cd, deal_ymd)
                if result['success']:
                    # 날짜 범위 + 매매 데이터 필터링
                    filtered_data = [
                        tx for tx in result['data']
                        if (start <= datetime.strptime(tx['deal_date'], "%Y-%m-%d") <= end and
                            not tx.get('rentFee') and not tx.get('deposit') and not tx.get('monthlyRent'))
                    ]
                    all_transactions.extend(filtered_data)
                    self.logger.info(f"{deal_ymd} 통합 데이터 {len(result['data'])}건 수집 → 매매 데이터 {len(filtered_data)}건 필터링 (날짜 범위)")
                else:
                    self.logger.warning(f"{deal_ymd} 통합 데이터 수집 실패: {result.get('error', '알 수 없는 오류')}")
                
                # 다음 달로 이동
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
        else:
            # 기존 방식: 개월 수로 조회 - 정확한 월별 계산
            current_date = datetime.now()
            for i in range(months):
                # 현재월부터 과거로 정확히 월 단위로 거슬러 올라감
                year = current_date.year
                month = current_date.month - i

                # 월이 0 이하가 되면 이전 연도로 이동
                while month <= 0:
                    month += 12
                    year -= 1

                target_date = datetime(year, month, 1)
                deal_ymd = target_date.strftime("%Y%m")

                # 진행률 콜백 호출 (시작)
                if progress_callback:
                    progress_callback(i, months, f"{year}년 {month}월", len(all_transactions), f"{year}년 {month}월 데이터 조회 중...")

                result = self.get_combined_apt_data(lawd_cd, deal_ymd)
                if result['success']:
                    # 매매 데이터만 필터링 (거래유형이 없거나 전월세 관련 필드가 없는 데이터)
                    sale_data = [
                        tx for tx in result['data']
                        if not tx.get('rentFee') and not tx.get('deposit') and not tx.get('monthlyRent')
                    ]
                    all_transactions.extend(sale_data)
                    self.logger.info(f"{deal_ymd} 통합 데이터 {len(result['data'])}건 수집 → 매매 데이터 {len(sale_data)}건 필터링")

                    # 진행률 콜백 호출 (완료)
                    if progress_callback:
                        progress_callback(i + 1, months, f"{year}년 {month}월", len(all_transactions), f"{year}년 {month}월 데이터 수집 완료")
                else:
                    self.logger.warning(f"{deal_ymd} 통합 데이터 수집 실패: {result.get('error', '알 수 없는 오류')}")

                    # 진행률 콜백 호출 (실패)
                    if progress_callback:
                        progress_callback(i + 1, months, f"{year}년 {month}월", len(all_transactions), f"{year}년 {month}월 데이터 수집 실패")

        return all_transactions

    def get_multiple_months_rent_data(self, lawd_cd: str, months: int = 6, start_date: str = None, end_date: str = None, progress_callback=None) -> List[Dict]:
        """여러 개월 전월세 데이터 조회"""
        all_transactions = []

        if start_date and end_date:
            # 날짜 범위로 조회
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            current = start.replace(day=1)  # 월의 첫째 날로 설정
            while current <= end:
                deal_ymd = current.strftime("%Y%m")
                result = self.get_apt_rent_data(lawd_cd, deal_ymd)
                if result['success']:
                    # 날짜 범위에 맞는 데이터만 필터링
                    filtered_data = [
                        tx for tx in result['data']
                        if start <= datetime.strptime(tx['deal_date'], "%Y-%m-%d") <= end
                    ]
                    all_transactions.extend(filtered_data)
                    self.logger.info(f"{deal_ymd} 전월세 데이터 {len(filtered_data)}건 수집 (날짜 범위 필터링)")
                else:
                    self.logger.warning(f"{deal_ymd} 전월세 데이터 수집 실패: {result.get('error', '알 수 없는 오류')}")

                # 다음 달로 이동
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
        else:
            # 기존 방식: 개월 수로 조회 - 정확한 월별 계산
            current_date = datetime.now()
            for i in range(months):
                # 현재월부터 과거로 정확히 월 단위로 거슬러 올라감
                year = current_date.year
                month = current_date.month - i

                # 월이 0 이하가 되면 이전 연도로 이동
                while month <= 0:
                    month += 12
                    year -= 1

                target_date = datetime(year, month, 1)
                deal_ymd = target_date.strftime("%Y%m")

                # 진행률 콜백 호출 (시작)
                if progress_callback:
                    progress_callback(i, months, f"{year}년 {month}월", len(all_transactions), f"{year}년 {month}월 전월세 데이터 조회 중...")

                result = self.get_apt_rent_data(lawd_cd, deal_ymd)
                if result['success']:
                    all_transactions.extend(result['data'])
                    self.logger.info(f"{deal_ymd} 전월세 데이터 {len(result['data'])}건 수집")

                    # 진행률 콜백 호출 (완료)
                    if progress_callback:
                        progress_callback(i + 1, months, f"{year}년 {month}월", len(all_transactions), f"{year}년 {month}월 전월세 데이터 수집 완료")
                else:
                    self.logger.warning(f"{deal_ymd} 전월세 데이터 수집 실패: {result.get('error', '알 수 없는 오류')}")

                    # 진행률 콜백 호출 (실패)
                    if progress_callback:
                        progress_callback(i + 1, months, f"{year}년 {month}월", len(all_transactions), f"{year}년 {month}월 전월세 데이터 수집 실패")

        return all_transactions

    def _get_demo_transaction_data(self, lawd_cd: str, deal_ymd: str) -> Dict:
        """데모용 실거래 데이터 생성"""
        # 지역코드에 따른 단지명과 기본 가격 설정
        demo_complexes = {
            '11680': [  # 강남구
                {'name': '삼성동 아이파크', 'base_price': 150000, 'area_range': [84, 114, 134]},
                {'name': '역삼 트리마제', 'base_price': 130000, 'area_range': [74, 84, 104]},
                {'name': '논현 래미안', 'base_price': 160000, 'area_range': [84, 114, 144]},
                {'name': '청담 자이', 'base_price': 180000, 'area_range': [84, 114, 134]},
                {'name': '대치 푸르지오', 'base_price': 140000, 'area_range': [74, 84, 104]}
            ],
            '11650': [  # 서초구
                {'name': '반포자이', 'base_price': 170000, 'area_range': [84, 114, 134]},
                {'name': '서초 아크로비스타', 'base_price': 140000, 'area_range': [74, 84, 104]},
                {'name': '방배 래미안', 'base_price': 150000, 'area_range': [84, 114, 134]},
                {'name': '서초 푸르지오', 'base_price': 160000, 'area_range': [74, 84, 104]},
                {'name': '잠원 한신', 'base_price': 130000, 'area_range': [84, 114, 134]}
            ],
            '11215': [  # 광진구
                {'name': '건국대 래미안', 'base_price': 90000, 'area_range': [74, 84, 104]},
                {'name': '구의 자이', 'base_price': 85000, 'area_range': [84, 114, 134]},
                {'name': '광나루 힐스테이트', 'base_price': 80000, 'area_range': [74, 84, 104]},
                {'name': '아차산 푸르지오', 'base_price': 95000, 'area_range': [84, 114, 134]}
            ],
            'default': [
                {'name': f'{self.get_region_name(lawd_cd)} 샘플단지', 'base_price': 80000, 'area_range': [84, 114]},
                {'name': f'{self.get_region_name(lawd_cd)} 래미안', 'base_price': 85000, 'area_range': [74, 84, 104]},
                {'name': f'{self.get_region_name(lawd_cd)} 힐스테이트', 'base_price': 90000, 'area_range': [84, 114, 134]}
            ]
        }

        complexes = demo_complexes.get(lawd_cd, demo_complexes['default'])
        transactions = []

        # 샘플 거래 데이터 생성
        import random
        from datetime import datetime

        year = int(deal_ymd[:4])
        month = int(deal_ymd[4:])

        for complex_info in complexes:
            for _ in range(random.randint(3, 8)):  # 단지당 3-8건 거래
                area = random.choice(complex_info['area_range'])
                base_price = complex_info['base_price']

                # 면적당 가격 변동 (10% 내외)
                price_per_area = base_price * random.uniform(0.9, 1.1)
                total_price = int(area * price_per_area / 10000)  # 만원 단위

                transaction = {
                    'apt_dong': f"{random.randint(1, 5)}동",
                    'apt_name': complex_info['name'],
                    'apt_seq': f"{lawd_cd}-{random.randint(1000, 9999)}",
                    'bonbun': f"{random.randint(1, 999):04d}",
                    'bubun': '0000',
                    'build_year': random.randint(2015, 2023),
                    'buyer_gbn': '개인',
                    'cdeal_type': '정상',
                    'deal_amount': total_price,
                    'deal_day': random.randint(1, 28),
                    'deal_month': month,
                    'deal_year': year,
                    'dealing_gbn': '중개거래',
                    'estate_agent_sgg_nm': self.get_region_name(lawd_cd),
                    'exclusive_area': area,
                    'floor': random.randint(3, 25),
                    'jibun': f"{random.randint(1, 999)}",
                    'rgs_date': f"{year}{month:02d}{random.randint(1, 28):02d}",
                    'road_name': '테스트로',
                    'road_name_bonbun': f"{random.randint(1, 999):05d}",
                    'road_name_bubun': '00000',
                    'sgg_cd': lawd_cd,
                    'sler_gbn': '개인',
                    'umd_cd': f"{lawd_cd}00",
                    'umd_nm': '테스트동',
                    'region_code': lawd_cd,
                    'region_name': self.get_region_name(lawd_cd),
                    'deal_date': f"{year}-{month:02d}-{random.randint(1, 28):02d}",
                    'price_per_area': price_per_area
                }
                transactions.append(transaction)

        self.logger.info(f"데모 데이터 {len(transactions)}건 생성 (지역코드: {lawd_cd}, 기간: {deal_ymd})")
        
        return {
            'success': True,
            'data': transactions,
            'total_count': len(transactions),
            'region_code': lawd_cd,
            'region_name': self.get_region_name(lawd_cd),
            'deal_ymd': deal_ymd,
            'is_demo': True
        }

    def search_apartments_by_name(self, lawd_cd: str, apt_name: str, months: int = 12) -> List[Dict]:
        """단지명으로 아파트 검색"""
        all_data = self.get_multiple_months_data(lawd_cd, months)
        
        # 단지명으로 필터링 (부분 일치)
        filtered_data = [
            tx for tx in all_data 
            if apt_name.lower() in tx['apt_name'].lower()
        ]
        
        return filtered_data

    def _get_xml_text(self, element, tag: str, default: str = "") -> str:
        """XML 요소에서 텍스트 추출"""
        child = element.find(tag)
        return child.text.strip() if child is not None and child.text else default

    def _parse_amount(self, amount_str: str) -> int:
        """거래금액 파싱 (쉼표 제거 후 정수 변환, 만원 단위)"""
        try:
            # MOLIT API의 dealAmount는 만원 단위로 제공됨
            # 예: "154,500" -> 154,500만원 (15억 4천 5백만원)
            return int(amount_str.replace(',', '').strip())
        except:
            return 0

    def _safe_int(self, value_str: str) -> int:
        """안전한 정수 변환 (쉼표 제거)"""
        try:
            return int(value_str.replace(',', '').strip()) if value_str else 0
        except:
            return 0

    def _rate_limit(self):
        """API 호출 간격 제어"""
        if self.request_delay > 0:
            time.sleep(self.request_delay)

    def get_cities(self) -> List[str]:
        """시/도 목록 반환"""
        return list(self.region_hierarchy.keys())

    def get_districts(self, city: str) -> List[Dict]:
        """특정 시/도의 군/구 목록 반환 (dong_code_active.txt에서 파싱)"""
        districts = []

        # dong_code_active.txt에서 해당 시/도의 군/구 목록을 찾기
        try:
            with open('dong_code_active.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()[1:]  # 헤더 제외

            # 첫 번째 패스: 모든 군/구 정보 수집 및 하위 구를 가진 시 식별
            all_districts = []
            parent_cities_with_sub_districts = set()

            for line in lines:
                parts = line.strip().split('\t')
                if len(parts) >= 3 and parts[2] == '존재':
                    code = parts[0]
                    name = parts[1]

                    # 시/도 매칭 확인
                    if city in name:
                        # 군/구 레벨 코드인지 확인 (끝 5자리가 00000)
                        if code.endswith('00000') and not code.endswith('0000000000'):
                            # 중복 제거를 위해 군/구명 추출
                            district_name = name.replace(f'{city} ', '').strip()
                            if district_name and district_name != city:
                                all_districts.append({
                                    'name': district_name,
                                    'code': code,
                                    'full_name': name
                                })

                                # 하위 구가 있는 상위 시 식별 (예: "고양시 덕양구"에서 "고양시" 추출)
                                if ' ' in district_name:
                                    parent_city = district_name.split(' ')[0]
                                    parent_cities_with_sub_districts.add(parent_city)

            # 두 번째 패스: 하위 구가 있는 상위 시는 제외하고 최종 목록 생성
            seen_districts = set()
            for district in all_districts:
                district_name = district['name']

                # 하위 구가 있는 상위 시는 제외
                if district_name in parent_cities_with_sub_districts:
                    self.logger.info(f"🚫 하위 구가 있는 상위 시 제외: {district_name}")
                    continue

                # 중복 제거
                if district_name not in seen_districts:
                    districts.append(district)
                    seen_districts.add(district_name)
                    self.logger.debug(f"✅ 군/구 추가: {district_name} (코드: {district['code']})")

            self.logger.info(f"📍 {city} 최종 군/구 목록: {len(districts)}개 (제외된 상위 시: {parent_cities_with_sub_districts})")
            return sorted(districts, key=lambda x: x['name'])

        except FileNotFoundError:
            # 파일이 없으면 기존 방식 사용 (하위 구가 있는 상위 시 제외)
            if city in self.region_hierarchy:
                districts = []
                for district, code_or_dict in self.region_hierarchy[city].items():
                    if isinstance(code_or_dict, str):
                        # 단순 시/군/구
                        districts.append({
                            'name': district,
                            'code': code_or_dict,
                            'full_name': f"{city} {district}"
                        })
                    elif isinstance(code_or_dict, dict):
                        # 구 단위로 세분화된 시 - 상위 시(_main)는 제외하고 개별 구만 추가
                        for sub_district, sub_code in code_or_dict.items():
                            if sub_district != '_main':  # 상위 시는 제외
                                # 개별 구만 추가
                                districts.append({
                                    'name': f"{district} {sub_district}",
                                    'code': sub_code,
                                    'full_name': f"{city} {district} {sub_district}"
                                })
                                self.logger.debug(f"✅ 하위 구 추가: {district} {sub_district} (코드: {sub_code})")

                        self.logger.info(f"🚫 하위 구가 있는 상위 시 제외: {district}")
            return sorted(districts, key=lambda x: x['name'])
        return []

    def get_dongs_from_file(self, city: str, district: str) -> List[Dict]:
        """dong_code_active.txt에서 특정 시/도, 군/구의 법정동 목록 반환"""
        dongs = []

        try:
            with open('dong_code_active.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()[1:]  # 헤더 제외

            target_prefix = f"{city} {district}"
            seen_dongs = set()

            for line in lines:
                parts = line.strip().split('\t')
                if len(parts) >= 3 and parts[2] == '존재':
                    code = parts[0]
                    name = parts[1]

                    # 해당 시/도, 군/구에 속하는지 확인
                    if name.startswith(target_prefix):
                        # 읍/면/동 레벨만 가져오기 (리 단위 제외)
                        # 시/군/구는 끝 5자리가 00000이므로 제외
                        name_parts = name.split()
                        if not code.endswith('00000'):
                            # target_prefix 다음에 오는 첫 번째 단어가 읍/면/동
                            target_parts = target_prefix.split()
                            if len(name_parts) > len(target_parts):
                                dong_name = name_parts[len(target_parts)]  # target_prefix 다음 단어
                                # 리 단위가 아닌 읍/면/동만 (리로 끝나지 않는 것)
                                if dong_name and not dong_name.endswith('리') and dong_name not in seen_dongs:
                                    dongs.append({
                                        'name': dong_name,
                                        'code': code[:5],  # 앞 5자리만 사용 (LAWD_CD)
                                        'full_name': name
                                    })
                                    seen_dongs.add(dong_name)

            return sorted(dongs, key=lambda x: x['name'])

        except FileNotFoundError:
            logging.error("dong_code_active.txt 파일을 찾을 수 없습니다")
            return []

    def get_region_code_by_city_district(self, city: str, district: str) -> str:
        """시/도와 군/구로 지역코드 조회 (구 단위 세분화 지원)"""
        if city in self.region_hierarchy:
            city_data = self.region_hierarchy[city]

            # 정확한 매칭 시도
            if district in city_data:
                code_or_dict = city_data[district]
                if isinstance(code_or_dict, str):
                    return code_or_dict
                elif isinstance(code_or_dict, dict) and '_main' in code_or_dict:
                    return code_or_dict['_main']

            # 구 단위로 세분화된 경우 검색
            for city_name, code_or_dict in city_data.items():
                if isinstance(code_or_dict, dict):
                    for sub_district, sub_code in code_or_dict.items():
                        if sub_district != '_main' and f"{city_name} {sub_district}" == district:
                            return sub_code
                        elif sub_district != '_main' and sub_district == district:
                            return sub_code
        return ''

    def get_region_list(self) -> List[Dict]:
        """지원하는 지역 목록 반환 (기존 호환성)"""
        regions = []
        for code, name in self.region_codes.items():
            regions.append({
                'code': code,
                'name': name,
                'full_name': f"{name} ({code})"
            })
        return sorted(regions, key=lambda x: x['name'])

    def get_region_hierarchy(self) -> Dict:
        """전체 지역 계층 구조 반환"""
        return self.region_hierarchy

    def _get_raw_xml_response(self, lawd_cd: str, deal_ymd: str) -> str:
        """원본 XML 응답 반환 (테스트용)"""
        try:
            # 일관성을 위해 base_url 사용
            params = {
                'serviceKey': self.service_key,
                'LAWD_CD': lawd_cd,
                'DEAL_YMD': deal_ymd,
                'numOfRows': 1000,
                'pageNo': 1
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            self.logger.info(f"📡 원본 XML 요청: {self.base_url}")
            self.logger.info(f"📋 요청 파라미터:")
            self.logger.info(f"   - 지역코드(LAWD_CD): {lawd_cd}")
            self.logger.info(f"   - 거래년월(DEAL_YMD): {deal_ymd}")
            self.logger.info(f"   - 조회건수(numOfRows): {params['numOfRows']}")
            self.logger.info(f"   - 페이지번호(pageNo): {params['pageNo']}")
            self.logger.info(f"🌐 HTTP 상태코드: {response.status_code}")
            
            return response.text
            
        except Exception as e:
            self.logger.error(f"원본 XML 응답 조회 실패: {e}")
            return f"XML 응답 조회 실패: {str(e)}"

    def _get_raw_rental_xml_response(self, lawd_cd: str, deal_ymd: str) -> str:
        """전월세 원본 XML 응답 반환 (테스트용)"""
        try:
            # 전월세 API URL 사용
            params = {
                'serviceKey': self.service_key,
                'LAWD_CD': lawd_cd,
                'DEAL_YMD': deal_ymd,
                'numOfRows': 1000,
                'pageNo': 1
            }

            response = self.session.get(self.rent_url, params=params, timeout=30)
            self.logger.info(f"📡 전월세 원본 XML 요청: {self.rent_url}")
            self.logger.info(f"📋 요청 파라미터:")
            self.logger.info(f"   - 지역코드(LAWD_CD): {lawd_cd}")
            self.logger.info(f"   - 거래년월(DEAL_YMD): {deal_ymd}")
            self.logger.info(f"   - 조회건수(numOfRows): {params['numOfRows']}")
            self.logger.info(f"   - 페이지번호(pageNo): {params['pageNo']}")
            self.logger.info(f"🌐 HTTP 상태코드: {response.status_code}")

            return response.text

        except Exception as e:
            self.logger.error(f"전월세 원본 XML 응답 조회 실패: {e}")
            return f"전월세 XML 응답 조회 실패: {str(e)}"

    def get_apt_rent_data(self, lawd_cd: str, deal_ymd: str, page_no: int = 1, num_of_rows: int = 1000) -> Dict:
        """
        아파트 전월세 거래 데이터 조회

        Args:
            lawd_cd: 지역코드 (예: 11110)
            deal_ymd: 거래년월 (예: 202506)
            page_no: 페이지 번호 (기본값: 1)
            num_of_rows: 한 페이지 결과 수 (기본값: 100)

        Returns:
            전월세 거래 데이터 딕셔너리
        """
        try:
            # Rate Limiting 적용
            self._rate_limit()

            # API URL 구성
            url = f"{self.rent_base_url}?serviceKey={self.service_key}&LAWD_CD={lawd_cd}&DEAL_YMD={deal_ymd}&pageNo={page_no}&numOfRows={num_of_rows}"

            self.logger.info(f"🏠 국토교통부 전월세 API 호출: 지역={lawd_cd}({self.get_region_name(lawd_cd)}), 기간={deal_ymd}")
            self.logger.info(f"📊 요청 파라미터: 페이지={page_no}, 조회건수={num_of_rows}")
            self.logger.debug(f"🔗 전체 URL: {url}")

            # 재사용 가능한 세션 사용
            # SSL 검증으로 먼저 시도
            try:
                response = self.session.get(url, timeout=self.timeout)
            except requests.exceptions.SSLError as ssl_error:
                self.logger.warning(f"SSL 인증서 오류 발생, 인증서 검증 비활성화로 재시도: {ssl_error}")
                # SSL 오류 시에만 검증 비활성화
                import urllib3
                original_verify = self.session.verify
                self.session.verify = False
                try:
                    with urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning):
                        response = self.session.get(url, timeout=self.timeout)
                finally:
                    # 원래 설정 복원
                    self.session.verify = original_verify
            except requests.exceptions.ConnectionError as conn_error:
                self.logger.error(f"연결 오류: {conn_error}")
                raise

            # 응답 상태 확인
            self.logger.info(f"HTTP 상태코드: {response.status_code}")

            if response.status_code == 200:
                return self._parse_rent_xml_response(response.text, lawd_cd, deal_ymd)
            else:
                self.logger.error(f"HTTP 오류: {response.status_code}")
                return {
                    'success': False,
                    'error': f'HTTP 오류: {response.status_code}',
                    'data': [],
                    'total_count': 0
                }

        except Exception as e:
            self.logger.error(f"전월세 API 호출 실패: {e}")
            self.logger.info("전월세 데모 데이터로 대체합니다.")
            return self._get_demo_rent_data(lawd_cd, deal_ymd)

    def _parse_rent_xml_response(self, xml_content: str, lawd_cd: str, deal_ymd: str) -> Dict:
        """전월세 XML 응답 파싱"""
        try:
            root = ET.fromstring(xml_content)

            # 결과 코드 확인
            result_code = root.find('.//resultCode')
            result_msg = root.find('.//resultMsg')

            if result_code is not None and result_code.text and result_code.text != '000':
                error_msg = result_msg.text if result_msg is not None else '알 수 없는 오류'
                self.logger.error(f"전월세 API 오류: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'data': [],
                    'total_count': 0
                }

            # 데이터 파싱
            items = root.findall('.//item')
            transactions = []
            skipped_count = 0

            for item in items:
                try:
                    deal_year = int(self._get_xml_text(item, 'dealYear', '0'))
                    deal_month = int(self._get_xml_text(item, 'dealMonth', '0'))
                    deal_day = int(self._get_xml_text(item, 'dealDay', '0'))

                    if not (1900 <= deal_year <= 2100):
                        skipped_count += 1
                        self.logger.debug(f"전월세 데이터 스킵: 유효하지 않은 거래년도 {deal_year}")
                        continue
                    if not (1 <= deal_month <= 12):
                        skipped_count += 1
                        self.logger.debug(f"전월세 데이터 스킵: 유효하지 않은 거래월 {deal_month}")
                        continue
                    if not (1 <= deal_day <= 31):
                        skipped_count += 1
                        self.logger.debug(f"전월세 데이터 스킵: 유효하지 않은 거래일 {deal_year}-{deal_month}-{deal_day}")
                        continue

                    deal_date = f"{deal_year}-{deal_month:02d}-{deal_day:02d}"

                    # 전월세 특화 필드 파싱
                    deposit = self._get_xml_text(item, 'deposit', '0')  # 보증금(만원)
                    monthly_rent = self._get_xml_text(item, 'monthlyRent', '0')  # 월세(만원)

                    # 전세/월세 구분 (월세가 0이면 전세)
                    transaction_type = "전세" if self._safe_int(monthly_rent) == 0 else "월세"

                    transaction = {
                        'apt_name': self._get_xml_text(item, 'aptNm', ''),
                        'build_year': int(self._get_xml_text(item, 'buildYear', '0')),
                        'contract_term': self._get_xml_text(item, 'contractTerm', ''),
                        'contract_type': self._get_xml_text(item, 'contractType', ''),
                        'deal_date': deal_date,
                        'dong': self._get_xml_text(item, 'dong', ''),
                        'exclusive_area': float(self._get_xml_text(item, 'excluUseAr', '0')),
                        'floor': self._get_xml_text(item, 'floor', ''),
                        'pre_deposit': self._get_xml_text(item, 'preDeposit', ''),
                        'pre_monthly_rent': self._get_xml_text(item, 'preMonthlyRent', ''),
                        'region_code': lawd_cd,
                        'road_name': self._get_xml_text(item, 'roadNm', ''),
                        'road_name_bonbun': self._get_xml_text(item, 'roadNmBonbun', ''),
                        'road_name_bubun': self._get_xml_text(item, 'roadNmBubun', ''),
                        'umd_nm': self._get_xml_text(item, 'umdNm', ''),  # 법정동명
                        'use_rr_right': self._get_xml_text(item, 'useRRRight', ''),

                        # 전월세 특화 필드
                        'deposit': self._safe_int(deposit),  # 보증금(만원)
                        'monthly_rent': self._safe_int(monthly_rent),  # 월세(만원)
                        'transaction_type': transaction_type,  # 전세/월세

                        # 호환성을 위한 필드
                        'deal_amount': self._safe_int(deposit),  # 보증금을 거래금액으로 사용
                        'price_per_area': 0,  # 전월세는 평당가격 계산하지 않음

                        # 추가 필드들 - 전월세용
                        'apt_dong': self._get_xml_text(item, 'aptDong', ''),  # 아파트동명
                        'jibun': self._get_xml_text(item, 'jibun', ''),  # 지번
                        'rgs_date': self._get_xml_text(item, 'rgsDate', ''),  # 등기일자
                        'sgg_cd': self._get_xml_text(item, 'sggCd', ''),  # 시군구코드
                        'umd_cd': self._get_xml_text(item, 'umdCd', ''),  # 읍면동코드
                    }

                    transactions.append(transaction)

                except (ValueError, TypeError) as e:
                    skipped_count += 1
                    self.logger.warning(f"전월세 거래 데이터 파싱 실패: {e}")
                    continue

            # 총 개수 확인 (API에서 제공하는 totalCount 사용)
            total_count_element = root.find('.//totalCount')
            total_count_value = int(total_count_element.text) if total_count_element is not None else len(transactions)

            self.logger.info(f"✅ 전월세 데이터 파싱 완료: {len(transactions)}건 파싱 (API 총 {total_count_value}건, 스킵 {skipped_count}건)")

            # totalCount와 파싱된 데이터 개수 차이 로깅
            if total_count_value > len(transactions):
                self.logger.warning(f"⚠️ totalCount({total_count_value})와 파싱된 데이터({len(transactions)})에 차이가 있습니다.")
                self.logger.warning(f"파싱 중 스킵된 데이터: {skipped_count}건")
                expected_parsed = total_count_value - skipped_count
                if expected_parsed != len(transactions):
                    self.logger.warning(f"예상 파싱 건수({expected_parsed})와 실제 파싱 건수({len(transactions)})가 다릅니다.")

            return {
                'success': True,
                'data': transactions,
                'total_count': total_count_value,  # API에서 제공하는 값 사용
                'parsed_count': len(transactions),  # 실제 파싱된 개수 추가
                'region_code': lawd_cd,
                'period': deal_ymd
            }

        except ET.ParseError as e:
            self.logger.error(f"전월세 XML 파싱 오류: {e}")
            return {
                'success': False,
                'error': f'XML 파싱 오류: {e}',
                'data': [],
                'total_count': 0
            }

    def _get_demo_rent_data(self, lawd_cd: str, deal_ymd: str) -> Dict:
        """전월세 데모 데이터 생성"""
        demo_transactions = [
            {
                'apt_name': '데모아파트',
                'build_year': 2015,
                'contract_term': '2년',
                'contract_type': '자동갱신',
                'deal_date': '2024-12-01',
                'dong': '데모동',
                'exclusive_area': 84.5,
                'floor': '10',
                'pre_deposit': '45000',
                'pre_monthly_rent': '0',
                'region_code': lawd_cd,
                'road_name': '데모로',
                'road_name_bonbun': '123',
                'road_name_bubun': '',
                'umd_nm': '데모동',  # 법정동명 추가
                'use_rr_right': 'Y',
                'deposit': 50000,  # 보증금 5억
                'monthly_rent': 0,  # 전세
                'transaction_type': '전세',
                'deal_amount': 50000,
                'price_per_area': 0
            },
            {
                'apt_name': '데모아파트',
                'build_year': 2015,
                'contract_term': '1년',
                'contract_type': '일반계약',
                'deal_date': '2024-12-02',
                'dong': '데모동',
                'exclusive_area': 74.2,
                'floor': '5',
                'pre_deposit': '18000',
                'pre_monthly_rent': '120',
                'region_code': lawd_cd,
                'road_name': '데모로',
                'road_name_bonbun': '123',
                'road_name_bubun': '',
                'umd_nm': '데모동',  # 법정동명 추가
                'use_rr_right': 'N',
                'deposit': 20000,  # 보증금 2억
                'monthly_rent': 150,  # 월세 150만원
                'transaction_type': '월세',
                'deal_amount': 20000,
                'price_per_area': 0
            }
        ]

        self.logger.info(f"📊 전월세 데모 데이터 생성: 총 {len(demo_transactions)}건")

        return {
            'success': True,
            'data': demo_transactions,
            'total_count': len(demo_transactions),
            'region_code': lawd_cd,
            'period': deal_ymd,
            'demo': True
        }

    def get_combined_apt_data(self, lawd_cd: str, deal_ymd: str, page_no: int = 1, num_of_rows: int = 100, fetch_all: bool = True) -> Dict:
        """
        아파트 매매 + 전월세 통합 조회

        Args:
            lawd_cd: 지역코드 (예: 11110)
            deal_ymd: 거래년월 (예: 202506)
            page_no: 페이지 번호 (기본값: 1)
            num_of_rows: 한 페이지 결과 수 (기본값: 100)
            fetch_all: 전체 데이터 수집 여부 (기본값: True)

        Returns:
            매매 + 전월세 통합 데이터 딕셔너리
        """
        self.logger.info(f"🏡 통합 아파트 데이터 조회 시작: 지역={lawd_cd}, 기간={deal_ymd}")

        if fetch_all:
            # 전체 데이터 수집 - 병렬 처리
            with ThreadPoolExecutor(max_workers=2) as executor:
                self.logger.info(f"🔄 매매/전월세 데이터 병렬 수집 시작")
                # 병렬로 매매와 전월세 데이터 수집
                sale_future = executor.submit(self.get_all_apt_trade_data, lawd_cd, deal_ymd, num_of_rows)
                rent_future = executor.submit(self.get_all_apt_rent_data, lawd_cd, deal_ymd, num_of_rows)

                # 결과 대기
                sale_data = sale_future.result()
                rent_data = rent_future.result()
                self.logger.info(f"✅ 매매/전월세 데이터 병렬 수집 완료")
        else:
            # 단일 페이지 데이터 수집 - 병렬 처리
            with ThreadPoolExecutor(max_workers=2) as executor:
                sale_future = executor.submit(self.get_apt_trade_data, lawd_cd, deal_ymd, page_no, num_of_rows)
                rent_future = executor.submit(self.get_apt_rent_data, lawd_cd, deal_ymd, page_no, num_of_rows)

                sale_data = sale_future.result()
                rent_data = rent_future.result()

        # 매매 데이터에 거래 유형 추가
        sale_transactions = []
        if sale_data.get('success') and sale_data.get('data'):
            for transaction in sale_data['data']:
                transaction['transaction_type'] = '매매'
                transaction['deposit'] = 0
                transaction['monthly_rent'] = 0
                sale_transactions.append(transaction)

        # 전월세 데이터 가져오기
        rent_transactions = []
        if rent_data.get('success') and rent_data.get('data'):
            rent_transactions = rent_data['data']

        # 데이터 통합
        all_transactions = sale_transactions + rent_transactions

        # 날짜순 정렬
        all_transactions.sort(key=lambda x: x['deal_date'], reverse=True)

        total_count = len(all_transactions)
        sale_count = len(sale_transactions)
        rent_count = len(rent_transactions)

        # API 전체 데이터 수 정보 추가
        sale_api_total = sale_data.get('api_total_count', sale_data.get('total_count', 0))
        rent_api_total = rent_data.get('api_total_count', rent_data.get('total_count', 0))
        total_api_count = sale_api_total + rent_api_total

        if fetch_all:
            self.logger.info(f"✅ 통합 데이터 전체 조회 완료: 총 {total_count}건 (매매 {sale_count}건, 전월세 {rent_count}건)")
            self.logger.info(f"📊 API 전체 데이터: 총 {total_api_count}건 (매매 {sale_api_total}건, 전월세 {rent_api_total}건)")
        else:
            self.logger.info(f"✅ 통합 데이터 조회 완료: 총 {total_count}건 (매매 {sale_count}건, 전월세 {rent_count}건)")

        return {
            'success': True,
            'data': all_transactions,
            'total_count': total_count,
            'sale_count': sale_count,
            'rent_count': rent_count,
            'api_total_count': total_api_count,
            'sale_api_total': sale_api_total,
            'rent_api_total': rent_api_total,
            'region_code': lawd_cd,
            'period': deal_ymd,
            'sale_data': sale_data,
            'rent_data': rent_data
        }
