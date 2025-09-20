#!/usr/bin/env python3
"""
국토교통부 실거래가 조회 시스템 웹 애플리케이션
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
import json
import threading
import time

from .molit_api import MolitRealEstateAPI
from .database import ApartmentDatabase

# .env 파일 로드
load_dotenv()

class ApartmentTrackerApp:
    """아파트 실거래가 추적 웹 애플리케이션"""

    def __init__(self):
        self.app = Flask(__name__, template_folder='../templates', static_folder='../static')

        # 진행률 저장소
        self.search_progress = {}
        self.search_lock = threading.Lock()

        # 보안 설정
        self.app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
        
        # 운영 환경에서 추가 보안 설정
        if os.getenv('FLASK_DEBUG', 'True').lower() != 'true':
            self.app.config['SESSION_COOKIE_SECURE'] = True
            self.app.config['SESSION_COOKIE_HTTPONLY'] = True
            self.app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

        # 로깅 설정
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # MOLIT API 초기화
        try:
            molit_api_key = os.getenv('MOLIT_API_KEY')
            if not molit_api_key:
                raise ValueError("MOLIT_API_KEY가 설정되지 않았습니다.")
            self.molit_api = MolitRealEstateAPI(service_key=molit_api_key)
            self.logger.info("MOLIT API 초기화 완료")
        except Exception as e:
            self.logger.error(f"MOLIT API 초기화 실패: {e}")
            self.molit_api = None

        # 데이터베이스 초기화
        try:
            db_path = os.getenv('DATABASE_URL', 'sqlite:///apartment_tracker.db').replace('sqlite:///', '')
            self.db = ApartmentDatabase(db_path)
            self.logger.info("데이터베이스 초기화 완료")
        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 실패: {e}")
            self.db = None

        self.setup_routes()

    def create_progress_callback(self, search_id):
        """진행률 콜백 함수 생성"""
        def callback(completed, total, current_month, total_data, message):
            with self.search_lock:
                self.search_progress[search_id] = {
                    'completed': completed,
                    'total': total,
                    'current_month': current_month,
                    'total_data': total_data,
                    'message': message,
                    'percentage': round((completed / total) * 100) if total > 0 else 0,
                    'timestamp': datetime.now().isoformat()
                }
        return callback

    def get_search_progress(self, search_id):
        """검색 진행률 조회"""
        with self.search_lock:
            return self.search_progress.get(search_id, None)

    def clear_search_progress(self, search_id):
        """검색 진행률 삭제"""
        with self.search_lock:
            if search_id in self.search_progress:
                del self.search_progress[search_id]

    def setup_routes(self):
        """라우트 설정"""
        self.logger.info("라우트 설정 시작")
        
        # 템플릿 함수 등록
        @self.app.template_filter('getPriceChangeClass')
        def get_price_change_class(price_change):
            """가격 변동률에 따른 CSS 클래스 반환"""
            if price_change > 0:
                return "text-success"
            elif price_change < 0:
                return "text-danger"
            else:
                return "text-muted"
        
        @self.app.template_filter('getPriceChangeIcon')
        def get_price_change_icon(price_change):
            """가격 변동률에 따른 아이콘 반환"""
            if price_change > 0:
                return "↗"
            elif price_change < 0:
                return "↘"
            else:
                return "→"

        @self.app.route('/')
        def index():
            """메인 페이지 - 관심단지 대시보드"""
            if not self.db:
                return render_template('error.html', 
                                     error="데이터베이스 연결 실패", 
                                     message="데이터베이스를 초기화할 수 없습니다.")
            
            # 관심단지와 최신 데이터 조회
            favorites = self.db.get_favorite_apartments_with_latest_data()
            return render_template('index.html', favorites=favorites)

        @self.app.route('/search')
        def search_page():
            """아파트 검색 페이지"""
            if not self.molit_api:
                return render_template('error.html', 
                                     error="API 연결 실패", 
                                     message="국토교통부 API 키가 설정되지 않았습니다.")
            
            cities = self.molit_api.get_cities()
            return render_template('search.html', cities=cities)

        @self.app.route('/favorites')
        def favorites_page():
            """관심단지 관리 페이지"""
            if not self.db:
                return render_template('error.html', 
                                     error="데이터베이스 연결 실패", 
                                     message="데이터베이스를 초기화할 수 없습니다.")
            
            favorites = self.db.get_favorite_apartments()
            return render_template('favorites.html', favorites=favorites)

        @self.app.route('/apartment/<apt_name>/<region_code>')
        def apartment_detail(apt_name, region_code):
            """아파트 상세 페이지"""
            if not self.db:
                return render_template('error.html', 
                                     error="데이터베이스 연결 실패", 
                                     message="데이터베이스를 초기화할 수 없습니다.")
            
            # 아파트 정보 조회
            transactions = self.db.get_apartment_transactions_old(apt_name, region_code, months=24)
            price_trend = self.db.get_price_trend(apt_name, region_code, months=12)
            
            # 관심단지 여부 확인
            favorites = self.db.get_favorite_apartments()
            is_favorite = any(fav['apt_name'] == apt_name and fav['region_code'] == region_code 
                            for fav in favorites)
            
            return render_template('apartment_detail.html', 
                                 apt_name=apt_name,
                                 region_code=region_code,
                                 transactions=transactions,
                                 price_trend=price_trend,
                                 is_favorite=is_favorite)

        # API 라우트들
        @self.app.route('/api/cities')
        def api_cities():
            """시/도 목록 API"""
            if not self.molit_api:
                return jsonify({'success': False, 'message': 'API 연결 실패'})
            
            cities = self.molit_api.get_cities()
            return jsonify({'success': True, 'cities': cities})

        @self.app.route('/api/districts/<city>')
        def api_districts(city):
            """특정 시/도의 군/구 목록 API"""
            if not self.molit_api:
                return jsonify({'success': False, 'message': 'API 연결 실패'})
            
            districts = self.molit_api.get_districts(city)
            return jsonify({'success': True, 'districts': districts})

        @self.app.route('/api/dongs/<city>/<district>')
        def api_dongs(city, district):
            """특정 시/도, 군/구의 법정동 목록 API (dong_code_active.txt에서 파싱)"""
            try:
                if not self.molit_api:
                    return jsonify({'success': False, 'message': 'API 연결 실패'})

                # dong_code_active.txt에서 법정동 목록 가져오기
                dongs = self.molit_api.get_dongs_from_file(city, district)
                return jsonify({'success': True, 'dongs': dongs})

            except Exception as e:
                logging.error(f"법정동 목록 조회 오류: {e}")
                return jsonify({'success': False, 'message': f'법정동 목록 조회 실패: {str(e)}'})

        @self.app.route('/api/dongs_legacy/<city>/<district>')
        def api_dongs_legacy(city, district):
            """특정 시/도, 군/구의 법정동 목록 API (기존 API 호출 방식)"""
            try:
                if not self.molit_api:
                    return jsonify({'success': False, 'message': 'API 연결 실패'})

                # 5자리 지역 코드 조회
                region_code = self.molit_api.get_region_code_by_city_district(city, district)
                if not region_code:
                    return jsonify({'success': False, 'message': '해당 지역을 찾을 수 없습니다.'})

                # 캐시에서 동 목록 조회 시도
                cache_data = self.db.get_search_cache(region_code, 36, datetime.now().strftime('%Y-%m-%d'))

                if cache_data and cache_data.get('raw_data'):
                    # 캐시된 데이터에서 동 목록 추출
                    dong_list = list(set([tx.get('umd_nm', '') for tx in cache_data['raw_data'] if tx.get('umd_nm')]))
                    dong_list = [dong for dong in dong_list if dong]  # 빈 문자열 제거
                    dong_list.sort()

                    return jsonify({
                        'success': True,
                        'dongs': dong_list,
                        'region_code': region_code,
                        'region_name': f"{city} {district}",
                        'from_cache': True
                    })

                # 캐시가 없으면 짧은 기간으로 API 호출해서 동 목록만 추출
                try:
                    # 최근 6개월 데이터로 동 목록 추출
                    api_data = self.molit_api.get_multiple_months_data(region_code, months=6)
                    if api_data:
                        dong_list = list(set([tx.get('umd_nm', '') for tx in api_data if tx.get('umd_nm')]))
                        dong_list = [dong for dong in dong_list if dong]  # 빈 문자열 제거
                        dong_list.sort()

                        return jsonify({
                            'success': True,
                            'dongs': dong_list,
                            'region_code': region_code,
                            'region_name': f"{city} {district}",
                            'from_cache': False
                        })
                    else:
                        return jsonify({'success': False, 'message': '해당 지역의 거래 데이터가 없습니다.'})

                except Exception as e:
                    self.logger.error(f"동 목록 API 호출 오류: {e}")
                    return jsonify({'success': False, 'message': f'API 호출 중 오류가 발생했습니다: {str(e)}'})

            except Exception as e:
                self.logger.error(f"동 목록 조회 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/regions')
        def api_regions():
            """지역 목록 API (기존 호환성)"""
            if not self.molit_api:
                return jsonify({'success': False, 'message': 'API 연결 실패'})
            
            regions = self.molit_api.get_region_list()
            return jsonify({'success': True, 'regions': regions})

        @self.app.route('/api/search', methods=['POST'])
        def api_search():
            """아파트 검색 API (캐시 시스템 적용)"""
            try:
                if not self.molit_api:
                    return jsonify({'success': False, 'message': 'API 연결 실패'})
                
                data = request.get_json()
                city = data.get('city', '')
                district = data.get('district', '')
                apt_name = data.get('apt_name', '')
                months = int(data.get('months', 6))
                start_date = data.get('start_date', '')
                end_date = data.get('end_date', '')
                force_refresh = data.get('force_refresh', False)  # 강제 새로고침 옵션
                
                if not city or not district:
                    return jsonify({'success': False, 'message': '시/도와 군/구를 모두 선택해주세요.'})
                
                # 시/도와 군/구로 지역코드 조회
                region_code = self.molit_api.get_region_code_by_city_district(city, district)
                if not region_code:
                    return jsonify({'success': False, 'message': '유효하지 않은 지역입니다.'})
                
                # 검색 날짜 생성 (캐시 키용)
                search_date = datetime.now().strftime('%Y-%m-%d')
                region_name = f"{city} {district}"
                
                # 캐시 확인 (특정 아파트 검색이 아닌 경우에만)
                if not apt_name and not force_refresh and self.db:
                    cache_data = self.db.get_search_cache(region_code, months, search_date)
                    if cache_data:
                        self.logger.info(f"캐시된 데이터 사용: {region_name} ({cache_data['total_count']}건)")
                        return jsonify({
                            'success': True,
                            'data': cache_data['raw_data'],
                            'classified_data': cache_data['classified_data'],
                            'total_count': cache_data['total_count'],
                            'region_name': cache_data['region_name'],
                            'region_code': cache_data['region_code'],
                            'is_demo': False,
                            'from_cache': True,
                            'cache_created': cache_data['created_at']
                        })
                
                # API 호출하여 새 데이터 조회
                self.logger.info(f"새 데이터 조회: {region_name}")
                
                if apt_name:
                    # 특정 아파트 검색
                    if start_date and end_date:
                        all_data = self.molit_api.get_multiple_months_data(region_code, months, start_date, end_date)
                        transactions = [tx for tx in all_data if apt_name.lower() in tx['apt_name'].lower()]
                    else:
                        transactions = self.molit_api.search_apartments_by_name(region_code, apt_name, months)
                else:
                    # 전체 아파트 조회
                    transactions = self.molit_api.get_multiple_months_data(region_code, months, start_date, end_date)
                
                # 데이터베이스에 저장
                if self.db and transactions:
                    saved_count = self.db.save_transaction_data(transactions)
                    self.logger.info(f"{saved_count}건의 거래 데이터 저장")
                
                # 법정동 단위로 분류
                classified_data = self._classify_by_dong(transactions)
                self.logger.info(f"법정동별 분류 완료: {len(classified_data)}개 동")
                
                # 캐시 저장 (특정 아파트 검색이 아닌 경우에만)
                if not apt_name and self.db:
                    cache_saved = self.db.save_search_cache(
                        region_code=region_code,
                        region_name=region_name,
                        months=months,
                        search_date=search_date,
                        total_count=len(transactions),
                        classified_data=classified_data,
                        raw_data=transactions,
                        cache_hours=24  # 24시간 캐시
                    )
                    if cache_saved:
                        self.logger.info(f"검색 결과 캐시 저장 완료: {region_name}")
                
                return jsonify({
                    'success': True,
                    'data': transactions,
                    'classified_data': classified_data,
                    'total_count': len(transactions),
                    'region_name': region_name,
                    'region_code': region_code,
                    'is_demo': transactions[0].get('is_demo', False) if transactions else False,
                    'from_cache': False
                })
                
            except Exception as e:
                self.logger.error(f"검색 API 오류: {e}")
                return jsonify({'success': False, 'message': f'검색 중 오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/favorites/check', methods=['POST'])
        def api_check_favorite():
            """관심단지 중복 확인 API"""
            try:
                if not self.db:
                    return jsonify({'success': False, 'message': '데이터베이스 연결 실패'})
                
                data = request.get_json()
                apt_name = data.get('apt_name')
                region_code = data.get('region_code')
                
                if not apt_name or not region_code:
                    return jsonify({'success': False, 'message': '아파트명과 지역코드가 필요합니다.'})
                
                exists = self.db.check_favorite_exists(apt_name, region_code)
                return jsonify({'success': True, 'exists': exists})
                    
            except Exception as e:
                self.logger.error(f"관심단지 확인 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/favorites', methods=['POST'])
        def api_add_favorite():
            """관심단지 추가 API"""
            try:
                if not self.db:
                    return jsonify({'success': False, 'message': '데이터베이스 연결 실패'})
                
                data = request.get_json()
                success = self.db.add_favorite_apartment(data)
                
                if success:
                    return jsonify({'success': True, 'message': '관심단지가 추가되었습니다.'})
                else:
                    return jsonify({'success': False, 'message': '관심단지 추가에 실패했습니다.'})
                    
            except Exception as e:
                self.logger.error(f"관심단지 추가 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/favorites/<apt_name>/<region_code>', methods=['DELETE'])
        def api_remove_favorite(apt_name, region_code):
            """관심단지 제거 API"""
            try:
                if not self.db:
                    return jsonify({'success': False, 'message': '데이터베이스 연결 실패'})
                
                success = self.db.remove_favorite_apartment(apt_name, region_code)
                
                if success:
                    return jsonify({'success': True, 'message': '관심단지가 제거되었습니다.'})
                else:
                    return jsonify({'success': False, 'message': '관심단지 제거에 실패했습니다.'})
                    
            except Exception as e:
                self.logger.error(f"관심단지 제거 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/apartment/<apt_name>/<region_code>/transactions')
        def api_apartment_transactions(apt_name, region_code):
            """아파트 거래 내역 API"""
            try:
                if not self.db:
                    return jsonify({'success': False, 'message': '데이터베이스 연결 실패'})
                
                months = int(request.args.get('months', 12))
                transactions = self.db.get_apartment_transactions_old(apt_name, region_code, months)
                price_trend = self.db.get_price_trend(apt_name, region_code, months)
                
                return jsonify({
                    'success': True,
                    'transactions': transactions,
                    'price_trend': price_trend
                })
                
            except Exception as e:
                self.logger.error(f"거래 내역 조회 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/refresh/<apt_name>/<region_code>')
        def api_refresh_data(apt_name, region_code):
            """아파트 데이터 새로고침 API"""
            try:
                if not self.molit_api or not self.db:
                    return jsonify({'success': False, 'message': 'API 또는 데이터베이스 연결 실패'})
                
                # 최근 6개월 데이터 조회
                transactions = self.molit_api.search_apartments_by_name(region_code, apt_name, 6)
                
                if transactions:
                    saved_count = self.db.save_transaction_data(transactions)
                    return jsonify({
                        'success': True, 
                        'message': f'{saved_count}건의 새로운 데이터를 저장했습니다.',
                        'new_data_count': saved_count
                    })
                else:
                    return jsonify({'success': False, 'message': '새로운 거래 데이터가 없습니다.'})
                    
            except Exception as e:
                self.logger.error(f"데이터 새로고침 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/search/step1', methods=['POST'])
        def api_search_step1():
            """1단계: 시도/군구 선택 후 법정동 목록 조회"""
            try:
                if not self.molit_api or not self.db:
                    return jsonify({'success': False, 'message': 'API 또는 데이터베이스 연결 실패'})
                
                data = request.get_json()
                city = data.get('city')
                district = data.get('district')
                dong = data.get('dong')
                search_type = data.get('search_type', 'sale')  # 기본값: 매매

                if not city or not district or not dong:
                    return jsonify({'success': False, 'message': '시도, 군구, 법정동을 모두 선택해주세요.'})
                
                # 지역 코드 조회
                region_code = self.molit_api.get_region_code_by_city_district(city, district)
                if not region_code:
                    return jsonify({'success': False, 'message': '해당 지역의 코드를 찾을 수 없습니다.'})
                
                # 데이터베이스에서 먼저 확인 (36개월 캐시) - 검색 타입별로 별도 캐시 키 사용
                search_date = datetime.now().strftime('%Y-%m-%d')
                if search_type == "all":
                    search_type_name = "통합"
                else:
                    search_type_name = "매매" if search_type == "sale" else "전월세"
                cache_key = f"{region_code}_{search_type}"  # 검색 타입별 캐시 키
                cached_data = self.db.get_search_cache(cache_key, 36, search_date)
                if cached_data and cached_data.get('raw_data'):
                    # 캐시된 데이터에서 선택된 법정동으로 필터링
                    raw_data = cached_data['raw_data']

                    # 선택된 동으로 데이터 필터링
                    filtered_data = [tx for tx in raw_data if tx.get('umd_nm') == dong]

                    if not filtered_data:
                        return jsonify({
                            'success': False,
                            'message': f'선택하신 법정동({dong})에서 {search_type_name} 거래 데이터를 찾을 수 없습니다.',
                            'suggestion': '다른 법정동을 선택해주세요.'
                        })

                    # 아파트 목록 추출 (선택된 동만) - 개선된 버전
                    apartment_list = self._extract_apartment_list_improved(filtered_data)

                    return jsonify({
                        'success': True,
                        'region_code': region_code,
                        'dong_name': dong,
                        'apartment_list': apartment_list,
                        'from_cache': True,
                        'total_count': len(filtered_data),
                        'search_type': search_type,
                        'search_type_name': search_type_name
                    })
                
                # 캐시된 데이터가 없으면 API 호출
                self.logger.info(f"{search_type_name} API 호출: {city} {district} (지역코드: {region_code})")
                try:
                    # 검색 타입에 따라 다른 API 호출
                    if search_type == "sale":
                        api_data = self.molit_api.get_multiple_months_data(region_code, months=36)
                    elif search_type == "rent":
                        api_data = self.molit_api.get_multiple_months_rent_data(region_code, months=36)
                    else:  # all - 통합 검색
                        # 매매와 전월세 데이터를 모두 가져와서 합치기
                        sale_data = self.molit_api.get_multiple_months_data(region_code, months=36)
                        rent_data = self.molit_api.get_multiple_months_rent_data(region_code, months=36)
                        api_data = (sale_data or []) + (rent_data or [])

                    self.logger.info(f"{search_type_name} API 호출 결과: {len(api_data) if api_data else 0}건의 데이터")
                except Exception as e:
                    self.logger.error(f"{search_type_name} API 호출 중 오류 발생: {e}")
                    return jsonify({'success': False, 'message': f'{search_type_name} API 호출 중 오류가 발생했습니다: {str(e)}'})

                if not api_data:
                    return jsonify({
                        'success': False,
                        'message': f'해당 지역({city} {district})의 최근 {search_type_name} 거래 데이터가 없습니다.',
                        'suggestion': '다른 지역을 선택하거나, 서울특별시나 인천광역시 등 대도시 지역을 시도해보세요.'
                    })
                
                # 데이터베이스에 저장 (캐시 + 개별 거래기록) - 검색 타입별로 별도 저장
                region_name = f"{city} {district} ({search_type_name})"
                self.db.save_search_cache(
                    region_code=cache_key,  # 검색 타입별 캐시 키 사용
                    region_name=region_name,
                    months=36,
                    search_date=search_date,
                    total_count=len(api_data),
                    classified_data={},  # 법정동별 분류는 나중에 필요시
                    raw_data=api_data,
                    cache_hours=24
                )

                # 개별 거래기록도 transaction_data 테이블에 저장
                for i, transaction in enumerate(api_data):
                    try:
                        # 데이터 타입 확인을 위한 디버깅
                        if i == 0:  # 첫 번째 항목만 로깅
                            self.logger.info(f"첫 번째 transaction 타입: {type(transaction)}")
                            self.logger.info(f"첫 번째 transaction 내용: {str(transaction)[:200]}...")

                        # 문자열인 경우 건너뛰기
                        if isinstance(transaction, str):
                            self.logger.warning(f"문자열 데이터 건너뛰기: {transaction[:50]}...")
                            continue

                        # 딕셔너리인 경우에만 처리
                        if isinstance(transaction, dict):
                            # region_name 추가
                            transaction['region_name'] = region_name
                            self.db.save_transaction_data(transaction)
                        else:
                            self.logger.warning(f"예상치 못한 데이터 타입: {type(transaction)}")
                    except Exception as e:
                        self.logger.error(f"거래 데이터 처리 중 오류: {e} - 타입: {type(transaction)}")
                        continue
                
                # 선택된 동으로 API 데이터 필터링
                filtered_data = [tx for tx in api_data if tx.get('umd_nm') == dong]

                if not filtered_data:
                    return jsonify({
                        'success': False,
                        'message': f'선택하신 법정동({dong})에서 거래 데이터를 찾을 수 없습니다.',
                        'suggestion': '다른 법정동을 선택해주세요.'
                    })

                # 아파트 목록 추출 (선택된 동만) - 개선된 버전
                apartment_list = self._extract_apartment_list_improved(filtered_data)

                return jsonify({
                    'success': True,
                    'region_code': region_code,
                    'dong_name': dong,
                    'apartment_list': apartment_list,
                    'from_cache': False,
                    'total_count': len(filtered_data),
                    'search_type': search_type,
                    'search_type_name': search_type_name
                })
                
            except Exception as e:
                self.logger.error(f"1단계 검색 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/search/step2', methods=['POST'])
        def api_search_step2():
            """2단계: 법정동 선택 후 아파트 목록 조회"""
            try:
                if not self.db:
                    return jsonify({'success': False, 'message': '데이터베이스 연결 실패'})
                
                data = request.get_json()
                region_code = data.get('region_code')
                dong_name = data.get('dong_name')
                
                if not region_code or not dong_name:
                    return jsonify({'success': False, 'message': '지역코드와 법정동을 선택해주세요.'})
                
                # 해당 법정동의 아파트 목록 조회
                apartment_list = self.db.get_apartments_by_dong(region_code, dong_name)
                
                return jsonify({
                    'success': True,
                    'apartment_list': apartment_list,
                    'dong_name': dong_name
                })
                
            except Exception as e:
                self.logger.error(f"2단계 검색 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/search/step3', methods=['POST'])
        def api_search_step3():
            """3단계: 아파트 선택 후 거래기록 조회"""
            try:
                if not self.db:
                    return jsonify({'success': False, 'message': '데이터베이스 연결 실패'})

                data = request.get_json()
                region_code = data.get('region_code')
                apt_name = data.get('apt_name')

                # 디버깅 로그 추가
                self.logger.info(f"🏢 Step3 요청: 지역코드={region_code}, 아파트명={apt_name}")

                if not region_code or not apt_name:
                    return jsonify({'success': False, 'message': '지역코드와 아파트명을 선택해주세요.'})

                # 해당 아파트의 거래기록 조회
                transactions = self.db.get_apartment_transactions(region_code, apt_name)

                self.logger.info(f"📊 거래기록 조회 결과: {len(transactions)}건")

                if len(transactions) == 0:
                    # 디버깅을 위해 데이터베이스에서 직접 확인
                    import sqlite3
                    with sqlite3.connect(self.db.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('SELECT COUNT(*) FROM transaction_data WHERE region_code = ?', (region_code,))
                        region_count = cursor.fetchone()[0]
                        cursor.execute('SELECT COUNT(*) FROM transaction_data WHERE apt_name = ?', (apt_name,))
                        apt_count = cursor.fetchone()[0]
                        self.logger.warning(f"❌ 거래기록 없음 - 지역코드 {region_code}: {region_count}건, 아파트명 '{apt_name}': {apt_count}건")

                return jsonify({
                    'success': True,
                    'transactions': transactions,
                    'apt_name': apt_name
                })

            except Exception as e:
                self.logger.error(f"3단계 검색 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/cache/statistics')
        def api_cache_statistics():
            """캐시 통계 API"""
            try:
                if not self.db:
                    return jsonify({'success': False, 'message': '데이터베이스 연결 실패'})

                stats = self.db.get_cache_statistics()

                return jsonify({
                    'success': True,
                    'statistics': stats
                })

            except Exception as e:
                self.logger.error(f"캐시 통계 조회 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/cache/invalidate', methods=['POST'])
        def api_cache_invalidate():
            """캐시 무효화 API"""
            try:
                if not self.db:
                    return jsonify({'success': False, 'message': '데이터베이스 연결 실패'})

                data = request.get_json()
                region_code = data.get('region_code') if data else None

                affected_rows = self.db.invalidate_search_cache(region_code)

                return jsonify({
                    'success': True,
                    'message': f'{affected_rows}건의 캐시가 무효화되었습니다.',
                    'affected_rows': affected_rows
                })

            except Exception as e:
                self.logger.error(f"캐시 무효화 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/test/direct', methods=['POST'])
        def api_test_direct():
            """직접 API 호출 테스트"""
            try:
                if not self.molit_api:
                    return jsonify({'success': False, 'message': 'MOLIT API 연결 실패'})

                data = request.get_json()
                region_code = data.get('region_code')
                deal_ymd = data.get('deal_ymd')

                # 사용자 요청 데이터 로그
                self.logger.info(f"🧪 API 테스트 요청 수신:")
                self.logger.info(f"📋 사용자 입력 데이터:")
                self.logger.info(f"   - 지역코드: {region_code}")
                self.logger.info(f"   - 거래년월: {deal_ymd}")
                self.logger.info(f"   - 클라이언트 IP: {request.remote_addr}")

                if not region_code or not deal_ymd:
                    self.logger.warning(f"❌ 필수 파라미터 누락 - 지역코드: {region_code}, 거래년월: {deal_ymd}")
                    return jsonify({'success': False, 'message': '지역코드와 거래년월이 필요합니다.'})

                # 직접 API 호출
                self.logger.info(f"🚀 국토교통부 API 직접 호출 시작")
                result = self.molit_api.get_apt_trade_data(region_code, deal_ymd)

                # 원본 XML 응답도 가져오기
                raw_xml = self.molit_api._get_raw_xml_response(region_code, deal_ymd)

                return jsonify({
                    'success': True,
                    'data': result.get('data', []),
                    'raw_xml': raw_xml,
                    'request_url': f"https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev?LAWD_CD={region_code}&DEAL_YMD={deal_ymd}&serviceKey=***",
                    'original_request': {
                        'method': request.method,
                        'url': request.url,
                        'path': request.path,
                        'query_string': request.query_string.decode(),
                        'headers': dict(request.headers),
                        'content_type': request.content_type,
                        'json_data': {
                            'region_code': region_code,
                            'deal_ymd': deal_ymd
                        },
                        'client_ip': request.remote_addr,
                        'user_agent': request.user_agent.string,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'referrer': request.referrer,
                        'scheme': request.scheme,
                        'host': request.host,
                        'is_secure': request.is_secure,
                        'content_length': request.content_length
                    },
                    'request_info': {
                        'region_code': region_code,
                        'deal_ymd': deal_ymd,
                        'client_ip': request.remote_addr,
                        'timestamp': result.get('timestamp', ''),
                        'region_name': self.molit_api.get_region_name(region_code) if self.molit_api else region_code
                    },
                    'summary': {
                        'region_code': region_code,
                        'deal_ymd': deal_ymd,
                        'total_count': len(result.get('data', [])),
                        'http_status': result.get('http_status', 'Unknown'),
                        'api_success': result.get('success', False)
                    }
                })

            except Exception as e:
                self.logger.error(f"직접 API 테스트 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/test/rental', methods=['POST'])
        def api_test_rental():
            """전월세 API 호출 테스트"""
            try:
                if not self.molit_api:
                    return jsonify({'success': False, 'message': 'MOLIT API 연결 실패'})

                data = request.get_json()
                region_code = data.get('region_code')
                deal_ymd = data.get('deal_ymd')

                # 사용자 요청 데이터 로그
                self.logger.info(f"🧪 전월세 API 테스트 요청 수신:")
                self.logger.info(f"📋 사용자 입력 데이터:")
                self.logger.info(f"   - 지역코드: {region_code}")
                self.logger.info(f"   - 거래년월: {deal_ymd}")
                self.logger.info(f"   - 클라이언트 IP: {request.remote_addr}")

                if not region_code or not deal_ymd:
                    self.logger.warning(f"❌ 필수 파라미터 누락 - 지역코드: {region_code}, 거래년월: {deal_ymd}")
                    return jsonify({'success': False, 'message': '지역코드와 거래년월이 필요합니다.'})

                # 전월세 API 호출
                self.logger.info(f"🚀 국토교통부 전월세 API 직접 호출 시작")
                result = self.molit_api.get_apt_rent_data(region_code, deal_ymd)

                # 원본 XML 응답도 가져오기
                raw_xml = self.molit_api._get_raw_rental_xml_response(region_code, deal_ymd)

                return jsonify({
                    'success': True,
                    'data': result.get('data', []),
                    'raw_xml': raw_xml,
                    'request_url': f"https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent?LAWD_CD={region_code}&DEAL_YMD={deal_ymd}&serviceKey=***",
                    'original_request': {
                        'method': request.method,
                        'url': request.url,
                        'path': request.path,
                        'query_string': request.query_string.decode(),
                        'headers': dict(request.headers),
                        'content_type': request.content_type,
                        'json_data': {
                            'region_code': region_code,
                            'deal_ymd': deal_ymd,
                            'api_type': 'rent'
                        },
                        'client_ip': request.remote_addr,
                        'user_agent': request.user_agent.string,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'referrer': request.referrer,
                        'scheme': request.scheme,
                        'host': request.host,
                        'is_secure': request.is_secure,
                        'content_length': request.content_length
                    },
                    'request_info': {
                        'region_code': region_code,
                        'deal_ymd': deal_ymd,
                        'client_ip': request.remote_addr,
                        'timestamp': result.get('timestamp', ''),
                        'region_name': self.molit_api.get_region_name(region_code) if self.molit_api else region_code
                    },
                    'summary': {
                        'region_code': region_code,
                        'deal_ymd': deal_ymd,
                        'total_count': len(result.get('data', [])),
                        'http_status': result.get('http_status', 'Unknown'),
                        'api_success': result.get('success', False)
                    }
                })

            except Exception as e:
                self.logger.error(f"전월세 API 테스트 오류: {e}")
                return jsonify({'success': False, 'message': f'전월세 API 오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/test')
        def api_test_page():
            """API 테스트 페이지"""
            return render_template('api_test.html')

        @self.app.route('/api/search/progress/<search_id>')
        def api_search_progress(search_id):
            """검색 진행률 조회 API"""
            try:
                progress = self.get_search_progress(search_id)
                self.logger.info(f"🔍 진행률 조회 - Search ID: {search_id}, Progress: {progress}")

                if progress:
                    return jsonify({
                        'success': True,
                        'progress': progress
                    })
                else:
                    self.logger.warning(f"⚠️ 진행률 정보 없음 - Search ID: {search_id}")
                    return jsonify({
                        'success': False,
                        'message': '진행률 정보를 찾을 수 없습니다.'
                    })
            except Exception as e:
                self.logger.error(f"진행률 조회 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/search/progress-stream/<search_id>')
        def api_search_progress_stream(search_id):
            """검색 진행률 실시간 스트림 (Server-Sent Events)"""
            def generate():
                while True:
                    progress = self.get_search_progress(search_id)
                    if progress:
                        yield f"data: {json.dumps(progress)}\n\n"

                        # 100% 완료시 스트림 종료
                        if progress.get('percentage', 0) >= 100:
                            break
                    time.sleep(0.5)  # 0.5초마다 업데이트

            return Response(generate(), mimetype='text/plain')

        @self.app.route('/api/search/with-progress', methods=['POST'])
        def api_search_with_progress():
            """진행률이 포함된 검색 API"""
            try:
                self.logger.info("🚀 진행률 검색 API 호출됨")

                if not self.molit_api or not self.db:
                    self.logger.error("❌ API 또는 데이터베이스 연결 실패")
                    return jsonify({'success': False, 'message': 'API 또는 데이터베이스 연결 실패'})

                data = request.get_json()
                city = data.get('city')
                district = data.get('district')
                dong = data.get('dong')
                search_type = data.get('search_type', 'sale')
                months = int(data.get('months', 36))

                self.logger.info(f"📍 검색 파라미터: {city} {district} {dong} ({search_type}, {months}개월)")

                if not city or not district or not dong:
                    self.logger.warning("⚠️ 필수 파라미터 누락")
                    return jsonify({'success': False, 'message': '시도, 군구, 법정동을 모두 선택해주세요.'})

                # 검색 ID 생성
                search_id = f"{city}_{district}_{dong}_{search_type}_{int(time.time())}"
                self.logger.info(f"🆔 생성된 검색 ID: {search_id}")

                # 지역 코드 조회
                region_code = self.molit_api.get_region_code_by_city_district(city, district)
                self.logger.info(f"🗺️ 지역 코드: {region_code}")
                if not region_code:
                    self.logger.error(f"❌ 지역 코드 조회 실패: {city} {district}")
                    return jsonify({'success': False, 'message': '해당 지역의 코드를 찾을 수 없습니다.'})

                # 진행률 콜백 생성
                progress_callback = self.create_progress_callback(search_id)
                self.logger.info(f"✅ 진행률 콜백 생성 완료")

                # 백그라운드에서 검색 실행
                def background_search():
                    try:
                        self.logger.info(f"🚀 백그라운드 검색 시작 - Search ID: {search_id}, Type: {search_type}, Region: {region_code}")

                        # 캐시에서 기존 데이터 확인
                        search_date = datetime.now().strftime('%Y-%m-%d')
                        cached_data = self.db.get_search_cache(region_code, months, search_date)

                        if cached_data and cached_data.get('raw_data'):
                            self.logger.info(f"🎯 캐시에서 데이터 발견! 총 {len(cached_data['raw_data'])}건")
                            # 검색 타입에 따라 필터링
                            if search_type == "sale":
                                # 매매 데이터만 필터링 (전월세 제외)
                                api_data = [
                                    tx for tx in cached_data['raw_data']
                                    if not tx.get('rentFee') and not tx.get('deposit') and not tx.get('monthlyRent')
                                ]
                                self.logger.info(f"🏢 캐시에서 매매 데이터 {len(api_data)}건 추출")
                            elif search_type == "rent":
                                # 전월세 데이터만 필터링 (매매 제외)
                                api_data = [
                                    tx for tx in cached_data['raw_data']
                                    if tx.get('rentFee') or tx.get('deposit') or tx.get('monthlyRent')
                                ]
                                self.logger.info(f"🏠 캐시에서 전월세 데이터 {len(api_data)}건 추출")
                            else:  # all - 통합 검색
                                # 모든 데이터 사용 (필터링 없음)
                                api_data = cached_data['raw_data']
                                self.logger.info(f"🌟 캐시에서 통합 데이터 {len(api_data)}건 추출")

                            # 즉시 완료 상태로 진행률 업데이트
                            progress_callback(months, months, "완료", len(api_data), "캐시에서 데이터를 가져왔습니다")
                        else:
                            # 캐시가 없으면 API 호출
                            self.logger.info(f"📡 캐시 없음 - API 호출 시작")
                            if search_type == "sale":
                                self.logger.info(f"📊 매매 데이터 조회 시작 - {months}개월")
                                api_data = self.molit_api.get_multiple_months_data(region_code, months=months, progress_callback=progress_callback)
                            elif search_type == "rent":
                                self.logger.info(f"🏠 전월세 데이터 조회 시작 - {months}개월")
                                api_data = self.molit_api.get_multiple_months_rent_data(region_code, months=months, progress_callback=progress_callback)
                            else:  # all - 통합 검색
                                self.logger.info(f"🌟 통합 데이터 조회 시작 - {months}개월")
                                # 매매와 전월세 데이터를 모두 가져와서 합치기
                                sale_data = self.molit_api.get_multiple_months_data(region_code, months=months, progress_callback=progress_callback)
                                rent_data = self.molit_api.get_multiple_months_rent_data(region_code, months=months, progress_callback=progress_callback)
                                api_data = (sale_data or []) + (rent_data or [])

                        # 선택된 동으로 필터링
                        self.logger.info(f"🔍 동 필터링 시작: 검색하는 동='{dong}', API 데이터 총 {len(api_data)}건")

                        # 실제 데이터에 포함된 동 이름들 확인
                        actual_dongs = set([tx.get('umd_nm', '') for tx in api_data[:10]])  # 처음 10개만 확인
                        self.logger.info(f"📍 실제 데이터의 동 이름들 (샘플): {actual_dongs}")

                        filtered_data = [tx for tx in api_data if tx.get('umd_nm') == dong]
                        self.logger.info(f"🎯 동 필터링 결과: {len(filtered_data)}건 ('{dong}' 동 매칭)")

                        # 아파트 목록 추출
                        apartment_list = self._extract_apartment_list_improved(filtered_data)

                        # 캐시에 원본 데이터 저장 (동 필터링 전 전체 데이터)
                        if not cached_data:  # 캐시에서 가져오지 않았을 때만 저장
                            try:
                                # 지역 이름 생성
                                region_name = f"{city} {district}"
                                search_date = datetime.now().strftime('%Y-%m-%d')

                                # 캐시에 저장 (전체 API 데이터를 저장하여 다른 동 검색에서 재사용)
                                cache_saved = self.db.save_search_cache(
                                    region_code=region_code,
                                    region_name=region_name,
                                    months=months,
                                    search_date=search_date,
                                    total_count=len(api_data),
                                    classified_data={},  # 백그라운드 검색에서는 분류 데이터 없음
                                    raw_data=api_data,
                                    cache_hours=24
                                )
                                if cache_saved:
                                    self.logger.info(f"🎯 캐시 저장 완료: {region_name} ({len(api_data)}건)")
                                else:
                                    self.logger.warning(f"⚠️ 캐시 저장 실패: {region_name}")
                            except Exception as cache_error:
                                self.logger.error(f"캐시 저장 중 오류: {cache_error}")

                        # 최종 진행률 업데이트
                        progress_callback(months, months, "완료", len(filtered_data), "검색이 완료되었습니다")

                        # 결과 저장 (나중에 결과 조회용)
                        with self.search_lock:
                            self.search_progress[search_id + '_result'] = {
                                'apartment_list': apartment_list,
                                'total_count': len(filtered_data),
                                'region_code': region_code,
                                'dong_name': dong,
                                'search_type': search_type,
                                'completed': True
                            }

                    except Exception as e:
                        self.logger.error(f"백그라운드 검색 오류: {e}")
                        progress_callback(0, months, "오류", 0, f"검색 중 오류가 발생했습니다: {str(e)}")

                # 백그라운드 스레드로 실행
                self.logger.info(f"🧵 백그라운드 스레드 생성 시작")
                thread = threading.Thread(target=background_search)
                thread.daemon = True
                thread.start()
                self.logger.info(f"🧵 백그라운드 스레드 시작됨")

                return jsonify({
                    'success': True,
                    'search_id': search_id,
                    'message': '검색이 시작되었습니다. 진행률을 확인하세요.'
                })

            except Exception as e:
                self.logger.error(f"진행률 검색 API 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/search/result/<search_id>')
        def api_search_result(search_id):
            """검색 결과 조회 API"""
            try:
                with self.search_lock:
                    result = self.search_progress.get(search_id + '_result')

                if result:
                    return jsonify({
                        'success': True,
                        'result': result
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': '검색 결과를 찾을 수 없습니다.'
                    })

            except Exception as e:
                self.logger.error(f"검색 결과 조회 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/test/progress', methods=['POST'])
        def api_test_progress():
            """진행률 테스트 API"""
            try:
                # 테스트용 진행률 데이터 생성
                test_search_id = "test_search_" + str(int(time.time()))

                # 진행률 콜백 생성 및 테스트
                progress_callback = self.create_progress_callback(test_search_id)

                # 테스트 진행률 업데이트
                for i in range(5):
                    progress_callback(i, 5, f"테스트 {i+1}", i*10, f"테스트 진행률 {i+1}/5")

                return jsonify({
                    'success': True,
                    'test_search_id': test_search_id,
                    'message': '테스트 진행률 데이터가 생성되었습니다.'
                })

            except Exception as e:
                self.logger.error(f"진행률 테스트 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/api/database/clear', methods=['POST'])
        def clear_database():
            """데이터베이스 초기화 API"""
            try:
                data = request.get_json()
                clear_type = data.get('type', 'cache')  # 'cache' 또는 'all'

                if clear_type == 'all':
                    success = self.database.clear_database()
                    message = "데이터베이스가 완전히 초기화되었습니다." if success else "데이터베이스 초기화에 실패했습니다."
                else:
                    success = self.database.clear_cache_only()
                    message = "캐시 데이터가 삭제되었습니다." if success else "캐시 삭제에 실패했습니다."

                return jsonify({
                    'success': success,
                    'message': message
                })

            except Exception as e:
                self.logger.error(f"데이터베이스 초기화 오류: {e}")
                return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

        @self.app.route('/test-simple')
        def test_simple():
            """간단한 테스트 페이지"""
            return "API 테스트 페이지가 작동합니다!"

        @self.app.route('/debug-routes')
        def debug_routes():
            """라우트 디버깅 페이지"""
            routes = []
            for rule in self.app.url_map.iter_rules():
                routes.append(f"{rule.rule} -> {rule.endpoint}")
            return "<br>".join(routes)

        self.logger.info("라우트 설정 완료")

    def _extract_apartment_list(self, transactions):
        """거래 데이터에서 아파트 목록 추출"""
        apartment_dict = {}
        
        for transaction in transactions:
            apt_name = transaction.get('apt_name', '')
            if not apt_name:
                continue
                
            if apt_name not in apartment_dict:
                apartment_dict[apt_name] = {
                    'apt_name': apt_name,
                    'region_code': transaction.get('region_code', ''),
                    'region_name': transaction.get('region_name', ''),
                    'build_year': transaction.get('build_year', 0),
                    'transaction_count': 0,
                    'avg_price': 0,
                    'min_price': float('inf'),
                    'max_price': 0,
                    'dong_list': set()
                }
            
            # 거래 건수 증가
            apartment_dict[apt_name]['transaction_count'] += 1
            
            # 가격 통계 계산 (deal_amount 기준, 만원 단위)
            price = transaction.get('deal_amount', 0)
            if price > 0:
                apartment_dict[apt_name]['min_price'] = min(
                    apartment_dict[apt_name]['min_price'], price
                )
                apartment_dict[apt_name]['max_price'] = max(
                    apartment_dict[apt_name]['max_price'], price
                )
            
            # 법정동 목록 추가
            dong_name = transaction.get('umd_nm', '')
            if dong_name:
                apartment_dict[apt_name]['dong_list'].add(dong_name)
        
        # 평균 가격 계산 및 정리
        apartment_list = []
        for apt_name, apt_data in apartment_dict.items():
            if apt_data['transaction_count'] > 0:
                # 평균 가격 계산
                total_price = sum(
                    tx.get('price_per_area', 0) for tx in transactions 
                    if tx.get('apt_name') == apt_name and tx.get('price_per_area', 0) > 0
                )
                apt_data['avg_price'] = total_price / apt_data['transaction_count'] if apt_data['transaction_count'] > 0 else 0
                
                # 무한대 처리
                if apt_data['min_price'] == float('inf'):
                    apt_data['min_price'] = 0
                
                # 법정동 목록을 리스트로 변환
                apt_data['dong_list'] = list(apt_data['dong_list'])
                
                apartment_list.append(apt_data)
        
        # 거래 건수 기준으로 정렬
        apartment_list.sort(key=lambda x: x['transaction_count'], reverse=True)
        
        return apartment_list

    def _extract_apartment_list_improved(self, transactions):
        """개선된 아파트 목록 추출 (1단계용) - 매매/전월세 구분 처리"""
        apartment_dict = {}

        for transaction in transactions:
            apt_name = transaction.get('apt_name', '')
            if not apt_name:
                continue

            if apt_name not in apartment_dict:
                apartment_dict[apt_name] = {
                    'apt_name': apt_name,
                    'region_code': transaction.get('region_code', ''),
                    'region_name': transaction.get('region_name', ''),
                    'build_year': transaction.get('build_year', 0),
                    'transaction_count': 0,
                    'sale_count': 0,      # 매매 거래 건수
                    'rent_count': 0,      # 전월세 거래 건수
                    'avg_price': 0,
                    'min_price': float('inf'),
                    'max_price': 0,
                    'dong_list': set(),
                }

            # 거래 건수 증가
            apartment_dict[apt_name]['transaction_count'] += 1

            # 매매/전월세 구분하여 카운팅
            is_rent = transaction.get('transaction_type') is not None or transaction.get('rentFee') or transaction.get('deposit') or transaction.get('monthlyRent')
            if is_rent:
                apartment_dict[apt_name]['rent_count'] += 1
            else:
                apartment_dict[apt_name]['sale_count'] += 1

            # 가격 통계 계산
            if is_rent:  # 전월세 데이터인 경우
                # 전월세는 보증금(deal_amount) 기준으로 계산
                price = transaction.get('deal_amount', 0)  # 보증금
            else:  # 매매 데이터인 경우
                price = transaction.get('deal_amount', 0)

            if price > 0:
                apartment_dict[apt_name]['min_price'] = min(
                    apartment_dict[apt_name]['min_price'], price
                )
                apartment_dict[apt_name]['max_price'] = max(
                    apartment_dict[apt_name]['max_price'], price
                )

            # 법정동 목록 추가
            dong_name = transaction.get('umd_nm', '')
            if dong_name:
                apartment_dict[apt_name]['dong_list'].add(dong_name)

        # 평균 가격 계산 및 정리
        apartment_list = []
        for apt_name, apt_data in apartment_dict.items():
            if apt_data['transaction_count'] > 0:
                # 평균 가격 계산 - 해당 아파트의 모든 거래에서 계산
                apt_transactions = [tx for tx in transactions if tx.get('apt_name') == apt_name]
                prices = [tx.get('deal_amount', 0) for tx in apt_transactions if tx.get('deal_amount', 0) > 0]

                if prices:
                    apt_data['avg_price'] = sum(prices) / len(prices)
                else:
                    apt_data['avg_price'] = 0

                # 무한대 처리
                if apt_data['min_price'] == float('inf'):
                    apt_data['min_price'] = 0

                # 법정동 목록을 리스트로 변환
                apt_data['dong_list'] = list(apt_data['dong_list'])

                apartment_list.append(apt_data)

        # 거래 건수 기준으로 정렬
        apartment_list.sort(key=lambda x: x['transaction_count'], reverse=True)

        return apartment_list

    def _classify_by_dong(self, transactions):
        """법정동 단위로 거래 데이터 분류"""
        classified = {}
        
        for transaction in transactions:
            dong_name = transaction.get('umd_nm', '알 수 없음')
            deal_month = transaction.get('deal_month', 0)
            deal_year = transaction.get('deal_year', 0)
            
            # 법정동별로 분류
            if dong_name not in classified:
                classified[dong_name] = {
                    'dong_name': dong_name,
                    'total_count': 0,
                    'months': {}
                }
            
            # 월별로 분류
            month_key = f"{deal_year}년 {deal_month}월"
            if month_key not in classified[dong_name]['months']:
                classified[dong_name]['months'][month_key] = {
                    'month_display': month_key,
                    'transactions': [],
                    'count': 0,
                    'avg_price': 0,
                    'min_price': float('inf'),
                    'max_price': 0
                }
            
            # 거래 데이터 추가
            classified[dong_name]['months'][month_key]['transactions'].append(transaction)
            classified[dong_name]['months'][month_key]['count'] += 1
            classified[dong_name]['total_count'] += 1
            
            # 가격 통계 계산
            price = transaction.get('deal_amount', 0)
            if price > 0:
                classified[dong_name]['months'][month_key]['min_price'] = min(
                    classified[dong_name]['months'][month_key]['min_price'], price
                )
                classified[dong_name]['months'][month_key]['max_price'] = max(
                    classified[dong_name]['months'][month_key]['max_price'], price
                )
        
        # 평균 가격 계산
        for dong_name in classified:
            for month_key in classified[dong_name]['months']:
                month_data = classified[dong_name]['months'][month_key]
                if month_data['count'] > 0:
                    total_price = sum(tx.get('deal_amount', 0) for tx in month_data['transactions'])
                    month_data['avg_price'] = total_price / month_data['count']
                    
                    # 무한대 처리
                    if month_data['min_price'] == float('inf'):
                        month_data['min_price'] = 0
        
        # 법정동별로 정렬 (거래 건수 기준)
        sorted_classified = dict(sorted(
            classified.items(), 
            key=lambda x: x[1]['total_count'], 
            reverse=True
        ))
        
        return sorted_classified

    def run(self, host=None, port=None, debug=None):
        """웹 서버 실행"""
        # 환경 변수에서 설정 로드
        host = host or os.getenv('FLASK_HOST', '0.0.0.0')
        port = port or int(os.getenv('FLASK_PORT', '8080'))
        debug = debug if debug is not None else os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        
        print("🏠 국토교통부 실거래가 조회 시스템이 시작되었습니다.")
        print(f"🌐 웹 브라우저에서 http://localhost:{port} 에 접속하세요.")
        print(f"🔧 디버그 모드: {'활성화' if debug else '비활성화'}")
        
        if not self.molit_api:
            print("⚠️  경고: MOLIT API 키가 설정되지 않았습니다.")
            print("💡 API 키 설정 방법:")
            print("   1. https://www.data.go.kr/ 에서 회원가입")
            print("   2. '아파트매매 실거래 상세자료' API 신청")
            print("   3. .env 파일 생성 및 API 키 설정:")
            print("      cp env.example .env")
            print("      .env 파일에서 MOLIT_API_KEY=발급받은_키 수정")
            print("   4. 시스템 재시작")
        
        self.app.run(host=host, port=port, debug=debug)

def create_app():
    """Flask 애플리케이션 팩토리"""
    app_instance = ApartmentTrackerApp()
    return app_instance.app

if __name__ == '__main__':
    app = ApartmentTrackerApp()
    app.run()
