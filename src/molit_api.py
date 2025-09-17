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

        # 환경 변수에서 설정 로드
        self.request_delay = float(os.getenv('API_REQUEST_DELAY', '0.1'))
        self.timeout = int(os.getenv('API_TIMEOUT', '15'))
        self.max_retries = int(os.getenv('API_MAX_RETRIES', '3'))

        # 로깅 설정
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 시-군-구 계층적 지역 데이터 구조
        self.region_hierarchy = {
            '서울특별시': {
                '종로구': '11110',
                '중구': '11140', 
                '용산구': '11170',
                '성동구': '11200',
                '광진구': '11215',
                '동대문구': '11230',
                '중랑구': '11260',
                '성북구': '11290',
                '강북구': '11305',
                '도봉구': '11320',
                '노원구': '11350',
                '은평구': '11380',
                '서대문구': '11410',
                '마포구': '11440',
                '양천구': '11470',
                '강서구': '11500',
                '구로구': '11530',
                '금천구': '11545',
                '영등포구': '11560',
                '동작구': '11590',
                '관악구': '11620',
                '서초구': '11650',
                '강남구': '11680',
                '송파구': '11710',
                '강동구': '11740'
            },
            '경기도': {
                '수원시': '41110',
                '성남시': '41130',
                '의정부시': '41150',
                '안양시': '41170',
                '부천시': '41190',
                '광명시': '41210',
                '평택시': '41220',
                '과천시': '41290',
                '오산시': '41370',
                '시흥시': '41390',
                '군포시': '41410',
                '고양시': '41280',
                '의왕시': '41430',
                '하남시': '41450',
                '용인시': '41460',
                '파주시': '41480',
                '이천시': '41500',
                '안성시': '41550',
                '김포시': '41570',
                '화성시': '41590',
                '광주시': '41610',
                '여주시': '41670',
                '양평군': '41830',
                '가평군': '41820',
                '연천군': '41800'
            },
            '인천광역시': {
                '중구': '28110',
                '동구': '28140',
                '미추홀구': '28177',
                '연수구': '28185',
                '남동구': '28200',
                '부평구': '28237',
                '계양구': '28245',
                '서구': '28260',
                '강화군': '28710',
                '옹진군': '28720'
            },
            '부산광역시': {
                '중구': '26110',
                '서구': '26140',
                '동구': '26170',
                '영도구': '26200',
                '부산진구': '26230',
                '동래구': '26260',
                '남구': '26290',
                '북구': '26320',
                '해운대구': '26350',
                '사하구': '26380',
                '금정구': '26410',
                '강서구': '26440',
                '연제구': '26470',
                '수영구': '26500',
                '사상구': '26530',
                '기장군': '26710'
            },
            '대구광역시': {
                '중구': '27110',
                '동구': '27140',
                '서구': '27170',
                '남구': '27200',
                '북구': '27230',
                '수성구': '27260',
                '달서구': '27290',
                '달성군': '27710'
            },
            '광주광역시': {
                '동구': '29110',
                '서구': '29140',
                '남구': '29170',
                '북구': '29200',
                '광산구': '29230'
            },
            '대전광역시': {
                '동구': '30110',
                '중구': '30140',
                '서구': '30170',
                '유성구': '30200',
                '대덕구': '30230'
            },
            '울산광역시': {
                '중구': '31110',
                '남구': '31140',
                '동구': '31170',
                '북구': '31200',
                '울주군': '31710'
            },
            '세종특별자치시': {
                '세종시': '36110'
            },
            '강원특별자치도': {
                '춘천시': '51110',
                '원주시': '51130',
                '강릉시': '51150',
                '동해시': '51170',
                '태백시': '51190',
                '속초시': '51210',
                '삼척시': '51230',
                '홍천군': '51720',
                '횡성군': '51730',
                '영월군': '51750',
                '평창군': '51760',
                '정선군': '51770',
                '철원군': '51780',
                '화천군': '51790',
                '양구군': '51800',
                '인제군': '51810',
                '고성군': '51820',
                '양양군': '51830'
            },
            '충청북도': {
                '청주시': '43110',
                '충주시': '43130',
                '제천시': '43150',
                '보은군': '43720',
                '옥천군': '43730',
                '영동군': '43740',
                '증평군': '43745',
                '진천군': '43750',
                '괴산군': '43760',
                '음성군': '43770',
                '단양군': '43800'
            },
            '충청남도': {
                '천안시': '44130',
                '공주시': '44150',
                '보령시': '44180',
                '아산시': '44200',
                '서산시': '44210',
                '논산시': '44230',
                '계룡시': '44250',
                '당진시': '44270',
                '금산군': '44710',
                '부여군': '44760',
                '서천군': '44770',
                '청양군': '44790',
                '홍성군': '44800',
                '예산군': '44810',
                '태안군': '44825'
            },
            '전라북도': {
                '전주시': '45110',
                '군산시': '45130',
                '익산시': '45140',
                '정읍시': '45180',
                '남원시': '45190',
                '김제시': '45210',
                '완주군': '45710',
                '진안군': '45720',
                '무주군': '45730',
                '장수군': '45740',
                '임실군': '45750',
                '순창군': '45770',
                '고창군': '45790',
                '부안군': '45800'
            },
            '전라남도': {
                '목포시': '46110',
                '여수시': '46130',
                '순천시': '46150',
                '나주시': '46170',
                '광양시': '46230',
                '담양군': '46710',
                '곡성군': '46720',
                '구례군': '46730',
                '고흥군': '46770',
                '보성군': '46780',
                '화순군': '46790',
                '장흥군': '46800',
                '강진군': '46810',
                '해남군': '46820',
                '영암군': '46830',
                '무안군': '46840',
                '함평군': '46860',
                '영광군': '46870',
                '장성군': '46880',
                '완도군': '46890',
                '진도군': '46900',
                '신안군': '46910'
            },
            '경상북도': {
                '포항시': '47110',
                '경주시': '47130',
                '김천시': '47150',
                '안동시': '47170',
                '구미시': '47190',
                '영주시': '47210',
                '영천시': '47230',
                '상주시': '47250',
                '문경시': '47280',
                '경산시': '47290',
                '군위군': '47720',
                '의성군': '47730',
                '청송군': '47750',
                '영양군': '47760',
                '영덕군': '47770',
                '청도군': '47820',
                '고령군': '47830',
                '성주군': '47840',
                '칠곡군': '47850',
                '예천군': '47900',
                '봉화군': '47920',
                '울진군': '47930',
                '울릉군': '47940'
            },
            '경상남도': {
                '창원시': '48120',
                '진주시': '48170',
                '통영시': '48220',
                '사천시': '48240',
                '김해시': '48250',
                '밀양시': '48270',
                '거제시': '48310',
                '양산시': '48330',
                '의령군': '48720',
                '함안군': '48730',
                '창녕군': '48740',
                '고성군': '48820',
                '남해군': '48840',
                '하동군': '48850',
                '산청군': '48860',
                '함양군': '48870',
                '거창군': '48880',
                '합천군': '48890'
            },
            '제주특별자치도': {
                '제주시': '50110',
                '서귀포시': '50130'
            }
        }

        # 기존 호환성을 위한 단순 매핑도 유지
        self.region_codes = {}
        for city, districts in self.region_hierarchy.items():
            for district, code in districts.items():
                self.region_codes[code] = f"{city} {district}"

    def get_region_name(self, region_code: str) -> str:
        """지역코드로 지역명 조회"""
        return self.region_codes.get(region_code, f"지역코드 {region_code}")

    def get_apt_trade_data(self, lawd_cd: str, deal_ymd: str, page_no: int = 1, num_of_rows: int = 100) -> Dict:
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

            self.logger.info(f"국토교통부 API 호출: 지역={lawd_cd}({self.get_region_name(lawd_cd)}), 기간={deal_ymd}")
            self.logger.debug(f"URL: {url}")

            # HTTP 헤더 설정
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/xml, text/xml, */*',
                'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                'Connection': 'keep-alive'
            }

            # SSL 설정 개선 (공공 API 호출용)
            session = requests.Session()
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # SSL 검증 비활성화 (공공 API 호출용)
            session.verify = False
            
            # SSL 컨텍스트 설정 (macOS 호환성)
            try:
                from requests.adapters import HTTPAdapter
                from urllib3.util.ssl_ import create_urllib3_context
                import ssl

                class CustomSSLAdapter(HTTPAdapter):
                    def init_poolmanager(self, *args, **kwargs):
                        context = create_urllib3_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        # macOS 호환성을 위한 SSL 설정
                        context.set_ciphers('DEFAULT:@SECLEVEL=0')
                        kwargs['ssl_context'] = context
                        return super().init_poolmanager(*args, **kwargs)

                session.mount('https://', CustomSSLAdapter())
                self.logger.debug("SSL 어댑터 설정 완료")
            except Exception as e:
                self.logger.warning(f"SSL 어댑터 설정 실패: {e}")
                # 기본 설정으로 fallback

            response = session.get(url, headers=headers, timeout=self.timeout)

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
                # 거래일 생성 및 유효성 검사
                deal_year = int(self._get_xml_text(item, 'dealYear', '0'))
                deal_month = int(self._get_xml_text(item, 'dealMonth', '0'))
                deal_day = int(self._get_xml_text(item, 'dealDay', '0'))
                deal_date = f"{deal_year}-{deal_month:0>2}-{deal_day:0>2}"
                
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
                
                transaction = {
                    'apt_dong': self._get_xml_text(item, 'aptDong'),
                    'apt_name': self._get_xml_text(item, 'aptNm'),
                    'apt_seq': self._get_xml_text(item, 'aptSeq'),
                    'bonbun': self._get_xml_text(item, 'bonbun'),
                    'bubun': self._get_xml_text(item, 'bubun'),
                    'build_year': int(self._get_xml_text(item, 'buildYear', '0')),
                    'buyer_gbn': self._get_xml_text(item, 'buyerGbn'),
                    'deal_amount': self._parse_amount(self._get_xml_text(item, 'dealAmount')),
                    'deal_day': deal_day,
                    'deal_month': deal_month,
                    'deal_year': deal_year,
                    'dealing_gbn': self._get_xml_text(item, 'dealingGbn'),
                    'estate_agent_sgg_nm': self._get_xml_text(item, 'estateAgentSggNm'),
                    'exclusive_area': float(self._get_xml_text(item, 'excluUseAr', '0')),
                    'floor': int(self._get_xml_text(item, 'floor', '0')),
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
                    'price_per_area': 0  # 계산해서 추가
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
                self.logger.info(f"✅ {len(transactions)}건의 실거래 데이터 수집완료 (총 {total_count_value}건)")

                return {
                    'success': True,
                    'data': transactions,
                    'total_count': total_count_value,
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

    def get_multiple_months_data(self, lawd_cd: str, months: int = 6, start_date: str = None, end_date: str = None) -> List[Dict]:
        """여러 개월 실거래 데이터 조회"""
        all_transactions = []
        
        if start_date and end_date:
            # 날짜 범위로 조회
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            current = start.replace(day=1)  # 월의 첫째 날로 설정
            while current <= end:
                deal_ymd = current.strftime("%Y%m")
                result = self.get_apt_trade_data(lawd_cd, deal_ymd)
                if result['success']:
                    # 날짜 범위에 맞는 데이터만 필터링
                    filtered_data = [
                        tx for tx in result['data'] 
                        if start <= datetime.strptime(tx['deal_date'], "%Y-%m-%d") <= end
                    ]
                    all_transactions.extend(filtered_data)
                    self.logger.info(f"{deal_ymd} 데이터 {len(filtered_data)}건 수집 (날짜 범위 필터링)")
                else:
                    self.logger.warning(f"{deal_ymd} 데이터 수집 실패: {result.get('error', '알 수 없는 오류')}")
                
                # 다음 달로 이동
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
        else:
            # 기존 방식: 개월 수로 조회
            current_date = datetime.now()
            for i in range(months):
                # 현재월부터 과거로 거슬러 올라감
                target_date = current_date - timedelta(days=30 * i)
                deal_ymd = target_date.strftime("%Y%m")

                result = self.get_apt_trade_data(lawd_cd, deal_ymd)
                if result['success']:
                    all_transactions.extend(result['data'])
                    self.logger.info(f"{deal_ymd} 데이터 {len(result['data'])}건 수집")
                else:
                    self.logger.warning(f"{deal_ymd} 데이터 수집 실패: {result.get('error', '알 수 없는 오류')}")

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
                    'deal_amount': total_price,
                    'deal_day': random.randint(1, 28),
                    'deal_month': month,
                    'deal_year': year,
                    'dealing_gbn': '중개거래',
                    'estate_agent_sgg_nm': self.get_region_name(lawd_cd),
                    'exclusive_area': area,
                    'floor': random.randint(3, 25),
                    'jibun': f"{random.randint(1, 999)}",
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

    def _rate_limit(self):
        """API 호출 간격 제어"""
        if self.request_delay > 0:
            time.sleep(self.request_delay)

    def get_cities(self) -> List[str]:
        """시/도 목록 반환"""
        return list(self.region_hierarchy.keys())

    def get_districts(self, city: str) -> List[Dict]:
        """특정 시/도의 군/구 목록 반환"""
        if city in self.region_hierarchy:
            districts = []
            for district, code in self.region_hierarchy[city].items():
                districts.append({
                    'name': district,
                    'code': code,
                    'full_name': f"{city} {district}"
                })
            return sorted(districts, key=lambda x: x['name'])
        return []

    def get_region_code_by_city_district(self, city: str, district: str) -> str:
        """시/도와 군/구로 지역코드 조회"""
        if city in self.region_hierarchy and district in self.region_hierarchy[city]:
            return self.region_hierarchy[city][district]
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
