#!/usr/bin/env python3
"""
관심단지 및 실거래가 데이터 저장용 데이터베이스 모듈
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json

class ApartmentDatabase:
    """아파트 실거래가 데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = "apartment_tracker.db"):
        """
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()

    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 관심단지 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS favorite_apartments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        apt_name TEXT NOT NULL,
                        region_code TEXT NOT NULL,
                        region_name TEXT NOT NULL,
                        apt_seq TEXT,
                        road_name TEXT,
                        road_name_bonbun TEXT,
                        road_name_bubun TEXT,
                        umd_nm TEXT,
                        build_year INTEGER,
                        exclusive_area REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        UNIQUE(apt_name, region_code)
                    )
                ''')
                
                # 실거래가 데이터 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transaction_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        apt_name TEXT NOT NULL,
                        apt_seq TEXT,
                        region_code TEXT NOT NULL,
                        region_name TEXT NOT NULL,
                        deal_date TEXT NOT NULL,
                        deal_year INTEGER,
                        deal_month INTEGER,
                        deal_day INTEGER,
                        deal_amount INTEGER,
                        exclusive_area REAL,
                        price_per_area REAL,
                        floor INTEGER,
                        build_year INTEGER,
                        road_name TEXT,
                        road_name_bonbun TEXT,
                        road_name_bubun TEXT,
                        umd_nm TEXT,
                        buyer_gbn TEXT,
                        sler_gbn TEXT,
                        dealing_gbn TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(apt_name, apt_seq, deal_date, deal_amount)
                    )
                ''')
                
                # 가격 변동 알림 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS price_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        apt_name TEXT NOT NULL,
                        region_code TEXT NOT NULL,
                        alert_type TEXT NOT NULL, -- 'price_drop', 'price_rise', 'new_transaction'
                        threshold_value REAL,
                        current_value REAL,
                        is_triggered BOOLEAN DEFAULT 0,
                        triggered_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT
                    )
                ''')
                
                # 검색 결과 캐시 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS search_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cache_key TEXT UNIQUE NOT NULL,
                        region_code TEXT NOT NULL,
                        region_name TEXT NOT NULL,
                        months INTEGER NOT NULL,
                        search_date TEXT NOT NULL,
                        total_count INTEGER NOT NULL,
                        classified_data TEXT NOT NULL, -- JSON 형태로 저장
                        raw_data TEXT, -- JSON 형태로 저장 (선택적)
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        is_valid BOOLEAN DEFAULT 1
                    )
                ''')
                
                # 인덱스 생성
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_favorite_apt_name ON favorite_apartments(apt_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_favorite_region ON favorite_apartments(region_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_apt_name ON transaction_data(apt_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_region ON transaction_data(region_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_date ON transaction_data(deal_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_key ON search_cache(cache_key)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_region ON search_cache(region_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires ON search_cache(expires_at)')
                
                conn.commit()
                self.logger.info("데이터베이스 초기화 완료")
                
        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 실패: {e}")
            raise

    def add_favorite_apartment(self, apt_data: Dict) -> bool:
        """관심단지 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO favorite_apartments 
                    (apt_name, region_code, region_name, apt_seq, road_name, 
                     road_name_bonbun, road_name_bubun, umd_nm, build_year, 
                     exclusive_area, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    apt_data.get('apt_name', ''),
                    apt_data.get('region_code', ''),
                    apt_data.get('region_name', ''),
                    apt_data.get('apt_seq', ''),
                    apt_data.get('road_name', ''),
                    apt_data.get('road_name_bonbun', ''),
                    apt_data.get('road_name_bubun', ''),
                    apt_data.get('umd_nm', ''),
                    apt_data.get('build_year', 0),
                    apt_data.get('exclusive_area', 0.0),
                    apt_data.get('notes', ''),
                    datetime.now()
                ))
                
                conn.commit()
                self.logger.info(f"관심단지 추가: {apt_data.get('apt_name')}")
                return True
                
        except Exception as e:
            self.logger.error(f"관심단지 추가 실패: {e}")
            return False

    def check_favorite_exists(self, apt_name: str, region_code: str) -> bool:
        """관심단지 중복 확인"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM favorite_apartments 
                    WHERE apt_name = ? AND region_code = ?
                ''', (apt_name, region_code))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            self.logger.error(f"관심단지 확인 실패: {e}")
            return False

    def get_favorite_apartments(self) -> List[Dict]:
        """관심단지 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM favorite_apartments 
                    WHERE is_active = 1 
                    ORDER BY created_at DESC
                ''')
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"관심단지 조회 실패: {e}")
            return []

    def remove_favorite_apartment(self, apt_name: str, region_code: str) -> bool:
        """관심단지 제거"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE favorite_apartments 
                    SET is_active = 0, updated_at = ?
                    WHERE apt_name = ? AND region_code = ?
                ''', (datetime.now(), apt_name, region_code))
                
                conn.commit()
                self.logger.info(f"관심단지 제거: {apt_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"관심단지 제거 실패: {e}")
            return False

    def save_transaction_data(self, transactions: List[Dict]) -> int:
        """실거래가 데이터 저장"""
        saved_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for tx in transactions:
                    try:
                        cursor.execute('''
                            INSERT OR IGNORE INTO transaction_data 
                            (apt_name, apt_seq, region_code, region_name, deal_date,
                             deal_year, deal_month, deal_day, deal_amount, exclusive_area,
                             price_per_area, floor, build_year, road_name, road_name_bonbun,
                             road_name_bubun, umd_nm, buyer_gbn, sler_gbn, dealing_gbn)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            tx.get('apt_name', ''),
                            tx.get('apt_seq', ''),
                            tx.get('region_code', ''),
                            tx.get('region_name', ''),
                            tx.get('deal_date', ''),
                            tx.get('deal_year', 0),
                            tx.get('deal_month', 0),
                            tx.get('deal_day', 0),
                            tx.get('deal_amount', 0),
                            tx.get('exclusive_area', 0.0),
                            tx.get('price_per_area', 0.0),
                            tx.get('floor', 0),
                            tx.get('build_year', 0),
                            tx.get('road_name', ''),
                            tx.get('road_name_bonbun', ''),
                            tx.get('road_name_bubun', ''),
                            tx.get('umd_nm', ''),
                            tx.get('buyer_gbn', ''),
                            tx.get('sler_gbn', ''),
                            tx.get('dealing_gbn', '')
                        ))
                        saved_count += 1
                        
                    except Exception as e:
                        self.logger.warning(f"거래 데이터 저장 실패: {tx.get('apt_name')} - {e}")
                        continue
                
                conn.commit()
                self.logger.info(f"{saved_count}건의 거래 데이터 저장 완료")
                
        except Exception as e:
            self.logger.error(f"거래 데이터 저장 실패: {e}")
            
        return saved_count

    def get_apartment_transactions_old(self, apt_name: str, region_code: str = None, months: int = 12) -> List[Dict]:
        """특정 아파트의 거래 내역 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 날짜 조건 계산
                from datetime import datetime, timedelta
                start_date = (datetime.now() - timedelta(days=30 * months)).strftime('%Y-%m-%d')
                
                if region_code:
                    cursor.execute('''
                        SELECT * FROM transaction_data 
                        WHERE apt_name = ? AND region_code = ? AND deal_date >= ?
                        ORDER BY deal_date DESC
                    ''', (apt_name, region_code, start_date))
                else:
                    cursor.execute('''
                        SELECT * FROM transaction_data 
                        WHERE apt_name = ? AND deal_date >= ?
                        ORDER BY deal_date DESC
                    ''', (apt_name, start_date))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"거래 내역 조회 실패: {e}")
            return []

    def get_price_trend(self, apt_name: str, region_code: str = None, months: int = 12) -> Dict:
        """아파트 가격 동향 분석"""
        transactions = self.get_apartment_transactions_old(apt_name, region_code, months)
        
        if not transactions:
            return {'trend': [], 'summary': {}}
        
        # 월별 평균 가격 계산
        monthly_data = {}
        for tx in transactions:
            month_key = f"{tx['deal_year']}-{tx['deal_month']:02d}"
            if month_key not in monthly_data:
                monthly_data[month_key] = []
            monthly_data[month_key].append(tx['price_per_area'])
        
        # 월별 통계 계산
        trend_data = []
        for month, prices in sorted(monthly_data.items()):
            trend_data.append({
                'month': month,
                'avg_price': sum(prices) / len(prices),
                'min_price': min(prices),
                'max_price': max(prices),
                'transaction_count': len(prices)
            })
        
        # 요약 통계
        all_prices = [tx['price_per_area'] for tx in transactions]
        summary = {
            'total_transactions': len(transactions),
            'avg_price': sum(all_prices) / len(all_prices),
            'min_price': min(all_prices),
            'max_price': max(all_prices),
            'price_change': 0
        }
        
        # 가격 변동률 계산
        if len(trend_data) >= 2:
            first_price = trend_data[0]['avg_price']
            last_price = trend_data[-1]['avg_price']
            summary['price_change'] = ((last_price - first_price) / first_price) * 100
        
        return {
            'trend': trend_data,
            'summary': summary
        }

    def get_favorite_apartments_with_latest_data(self) -> List[Dict]:
        """관심단지와 최신 거래 데이터 조회"""
        favorites = self.get_favorite_apartments()
        result = []
        
        for fav in favorites:
            # 최신 거래 데이터 조회
            latest_transactions = self.get_apartment_transactions_old(
                fav['apt_name'], 
                fav['region_code'], 
                months=3
            )
            
            # 가격 동향 분석
            price_trend = self.get_price_trend(
                fav['apt_name'], 
                fav['region_code'], 
                months=6
            )
            
            fav_data = dict(fav)
            fav_data['latest_transactions'] = latest_transactions[:5]  # 최근 5건
            fav_data['price_trend'] = price_trend
            fav_data['has_recent_data'] = len(latest_transactions) > 0
            
            result.append(fav_data)
        
        return result

    def add_price_alert(self, apt_name: str, region_code: str, alert_type: str, 
                       threshold_value: float, notes: str = "") -> bool:
        """가격 알림 설정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO price_alerts 
                    (apt_name, region_code, alert_type, threshold_value, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (apt_name, region_code, alert_type, threshold_value, notes))
                
                conn.commit()
                self.logger.info(f"가격 알림 설정: {apt_name} - {alert_type}")
                return True
                
        except Exception as e:
            self.logger.error(f"가격 알림 설정 실패: {e}")
            return False

    def get_active_alerts(self) -> List[Dict]:
        """활성 알림 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM price_alerts 
                    WHERE is_triggered = 0 
                    ORDER BY created_at DESC
                ''')
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"알림 조회 실패: {e}")
            return []

    def generate_cache_key(self, region_code: str, months: int, search_date: str) -> str:
        """캐시 키 생성"""
        return f"{region_code}_{months}_{search_date}"

    def save_search_cache(self, region_code: str, region_name: str, months: int, 
                         search_date: str, total_count: int, classified_data: Dict, 
                         raw_data: List[Dict] = None, cache_hours: int = 24) -> bool:
        """검색 결과 캐시 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cache_key = self.generate_cache_key(region_code, months, search_date)
                
                # 만료 시간 계산
                from datetime import datetime, timedelta
                expires_at = (datetime.now() + timedelta(hours=cache_hours)).strftime('%Y-%m-%d %H:%M:%S')
                
                cursor.execute('''
                    INSERT OR REPLACE INTO search_cache 
                    (cache_key, region_code, region_name, months, search_date, 
                     total_count, classified_data, raw_data, expires_at, is_valid)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    cache_key,
                    region_code,
                    region_name,
                    months,
                    search_date,
                    total_count,
                    json.dumps(classified_data, ensure_ascii=False),
                    json.dumps(raw_data, ensure_ascii=False) if raw_data else None,
                    expires_at
                ))
                
                conn.commit()
                self.logger.info(f"검색 결과 캐시 저장: {cache_key}")
                return True
                
        except Exception as e:
            self.logger.error(f"검색 결과 캐시 저장 실패: {e}")
            return False

    def get_search_cache(self, region_code: str, months: int, search_date: str) -> Optional[Dict]:
        """검색 결과 캐시 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cache_key = self.generate_cache_key(region_code, months, search_date)
                
                cursor.execute('''
                    SELECT * FROM search_cache 
                    WHERE cache_key = ? AND is_valid = 1 AND expires_at > datetime('now')
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (cache_key,))
                
                row = cursor.fetchone()
                if row:
                    cache_data = dict(row)
                    cache_data['classified_data'] = json.loads(cache_data['classified_data'])
                    if cache_data['raw_data']:
                        cache_data['raw_data'] = json.loads(cache_data['raw_data'])
                    else:
                        cache_data['raw_data'] = []
                    
                    self.logger.info(f"검색 결과 캐시 조회 성공: {cache_key}")
                    return cache_data
                else:
                    self.logger.info(f"검색 결과 캐시 없음: {cache_key}")
                    return None
                
        except Exception as e:
            self.logger.error(f"검색 결과 캐시 조회 실패: {e}")
            return None

    def invalidate_search_cache(self, region_code: str = None) -> int:
        """검색 결과 캐시 무효화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if region_code:
                    cursor.execute('''
                        UPDATE search_cache 
                        SET is_valid = 0 
                        WHERE region_code = ?
                    ''', (region_code,))
                    affected_rows = cursor.rowcount
                    self.logger.info(f"지역별 캐시 무효화: {region_code} ({affected_rows}건)")
                else:
                    cursor.execute('''
                        UPDATE search_cache 
                        SET is_valid = 0 
                        WHERE expires_at < datetime('now')
                    ''')
                    affected_rows = cursor.rowcount
                    self.logger.info(f"만료된 캐시 무효화: {affected_rows}건")
                
                conn.commit()
                return affected_rows
                
        except Exception as e:
            self.logger.error(f"캐시 무효화 실패: {e}")
            return 0

    def get_cache_statistics(self) -> Dict:
        """캐시 통계 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 전체 캐시 개수
                cursor.execute('SELECT COUNT(*) as total FROM search_cache WHERE is_valid = 1')
                total_cache = cursor.fetchone()['total']
                
                # 만료된 캐시 개수
                cursor.execute('''
                    SELECT COUNT(*) as expired 
                    FROM search_cache 
                    WHERE is_valid = 1 AND expires_at < datetime('now')
                ''')
                expired_cache = cursor.fetchone()['expired']
                
                # 지역별 캐시 개수
                cursor.execute('''
                    SELECT region_name, COUNT(*) as count 
                    FROM search_cache 
                    WHERE is_valid = 1 
                    GROUP BY region_name 
                    ORDER BY count DESC 
                    LIMIT 10
                ''')
                region_stats = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'total_cache': total_cache,
                    'expired_cache': expired_cache,
                    'valid_cache': total_cache - expired_cache,
                    'region_stats': region_stats
                }
                
        except Exception as e:
            self.logger.error(f"캐시 통계 조회 실패: {e}")
            return {}

    def get_apartments_by_dong(self, region_code: str, dong_name: str) -> List[Dict]:
        """특정 법정동의 아파트 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT DISTINCT 
                        apt_name,
                        region_code,
                        region_name,
                        build_year,
                        COUNT(*) as transaction_count,
                        AVG(price_per_area) as avg_price,
                        MIN(price_per_area) as min_price,
                        MAX(price_per_area) as max_price
                    FROM transaction_data 
                    WHERE region_code = ? AND umd_nm = ?
                    GROUP BY apt_name, region_code
                    ORDER BY transaction_count DESC, apt_name
                ''', (region_code, dong_name))
                
                apartments = []
                for row in cursor.fetchall():
                    apartments.append({
                        'apt_name': row['apt_name'],
                        'region_code': row['region_code'],
                        'region_name': row['region_name'],
                        'build_year': row['build_year'],
                        'transaction_count': row['transaction_count'],
                        'avg_price': round(row['avg_price'], 2) if row['avg_price'] else 0,
                        'min_price': row['min_price'] or 0,
                        'max_price': row['max_price'] or 0
                    })
                
                return apartments
                
        except Exception as e:
            self.logger.error(f"법정동별 아파트 목록 조회 실패: {e}")
            return []

    def get_apartment_transactions(self, region_code: str, apt_name: str) -> List[Dict]:
        """특정 아파트의 거래기록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        deal_date,
                        deal_amount,
                        exclusive_area,
                        price_per_area,
                        floor,
                        apt_name,
                        region_name,
                        umd_nm,
                        build_year
                    FROM transaction_data 
                    WHERE region_code = ? AND apt_name = ?
                    ORDER BY deal_date DESC
                ''', (region_code, apt_name))
                
                transactions = []
                for row in cursor.fetchall():
                    transactions.append({
                        'deal_date': row['deal_date'],
                        'deal_amount': row['deal_amount'],
                        'exclusive_area': row['exclusive_area'],
                        'price_per_area': row['price_per_area'],
                        'floor': row['floor'],
                        'apt_name': row['apt_name'],
                        'region_name': row['region_name'],
                        'umd_nm': row['umd_nm'],
                        'build_year': row['build_year']
                    })
                
                return transactions
                
        except Exception as e:
            self.logger.error(f"아파트 거래기록 조회 실패: {e}")
            return []

    def get_apartments_by_region(self, region_code: str) -> List[Dict]:
        """특정 지역의 모든 아파트 목록 조회 (1단계용)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT DISTINCT 
                        apt_name,
                        region_code,
                        region_name,
                        build_year,
                        umd_nm,
                        COUNT(*) as transaction_count,
                        AVG(price_per_area) as avg_price,
                        MIN(price_per_area) as min_price,
                        MAX(price_per_area) as max_price
                    FROM transaction_data 
                    WHERE region_code = ?
                    GROUP BY apt_name, region_code, umd_nm
                    ORDER BY transaction_count DESC, apt_name
                ''', (region_code,))
                
                apartments = []
                for row in cursor.fetchall():
                    apartments.append({
                        'apt_name': row['apt_name'],
                        'region_code': row['region_code'],
                        'region_name': row['region_name'],
                        'build_year': row['build_year'],
                        'umd_nm': row['umd_nm'],
                        'transaction_count': row['transaction_count'],
                        'avg_price': round(row['avg_price'], 2) if row['avg_price'] else 0,
                        'min_price': row['min_price'] or 0,
                        'max_price': row['max_price'] or 0
                    })
                
                return apartments
                
        except Exception as e:
            self.logger.error(f"지역별 아파트 목록 조회 실패: {e}")
            return []
