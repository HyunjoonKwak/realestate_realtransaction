#!/usr/bin/env python3
"""
API 호출 횟수 예측 및 사용자 확인 모듈
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class APICallEstimator:
    """API 호출 횟수 예측 클래스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def estimate_search_calls(self, search_params: Dict) -> Tuple[int, Dict]:
        """
        검색 API 호출 횟수 예측

        Args:
            search_params: 검색 파라미터
                - search_type: 'sale', 'rent', 'all'
                - months: 조회할 개월 수
                - force_refresh: 강제 새로고침 여부
                - apt_name: 특정 아파트명 (있으면 전체 조회)

        Returns:
            Tuple[int, Dict]: (예상 API 호출 횟수, 상세 정보)
        """
        search_type = search_params.get('search_type', 'sale')
        months = search_params.get('months', 6)
        force_refresh = search_params.get('force_refresh', False)
        apt_name = search_params.get('apt_name', '')

        # 기본 호출 횟수는 개월 수
        base_calls = months

        # 검색 타입에 따른 호출 횟수 계산
        # 실제 구현에서는 매매와 전월세를 병렬로 수집하므로 둘 다 호출됨
        if search_type == 'sale':
            # 매매 데이터만 조회하지만 실제로는 병렬로 매매+전월세 모두 호출
            api_calls = base_calls * 2  # 매매 + 전월세 병렬 호출
            api_type = "매매 (병렬 전월세 포함)"
        elif search_type == 'rent':
            # 전월세 데이터만 조회하지만 실제로는 병렬로 매매+전월세 모두 호출
            api_calls = base_calls * 2  # 매매 + 전월세 병렬 호출
            api_type = "전월세 (병렬 매매 포함)"
        elif search_type == 'all':
            # 매매 + 전월세 데이터 모두 조회
            api_calls = base_calls * 2
            api_type = "매매 + 전월세"
        else:
            api_calls = base_calls * 2  # 기본적으로 병렬 호출
            api_type = "매매 (병렬 전월세 포함)"

        # 상세 정보 생성
        details = {
            'search_type': search_type,
            'api_type': api_type,
            'months': months,
            'force_refresh': force_refresh,
            'apt_name': apt_name,
            'base_calls': base_calls,
            'total_calls': api_calls,
            'estimated_time': self._estimate_time(api_calls),
            'cost_info': self._get_cost_info(api_calls)
        }

        return api_calls, details

    def estimate_refresh_calls(self, refresh_params: Dict) -> Tuple[int, Dict]:
        """
        데이터 새로고침 API 호출 횟수 예측

        Args:
            refresh_params: 새로고침 파라미터
                - apt_name: 아파트명
                - region_code: 지역코드
                - months: 조회할 개월 수 (기본 6개월)

        Returns:
            Tuple[int, Dict]: (예상 API 호출 횟수, 상세 정보)
        """
        months = refresh_params.get('months', 6)
        apt_name = refresh_params.get('apt_name', '')
        region_code = refresh_params.get('region_code', '')

        # 새로고침은 일반적으로 매매 데이터만 조회
        api_calls = months

        details = {
            'operation': 'refresh',
            'apt_name': apt_name,
            'region_code': region_code,
            'months': months,
            'total_calls': api_calls,
            'estimated_time': self._estimate_time(api_calls),
            'cost_info': self._get_cost_info(api_calls)
        }

        return api_calls, details

    def estimate_step1_calls(self, step1_params: Dict) -> Tuple[int, Dict]:
        """
        1단계 검색 API 호출 횟수 예측

        Args:
            step1_params: 1단계 검색 파라미터
                - city: 시/도
                - district: 군/구
                - search_type: 'sale', 'rent', 'all'

        Returns:
            Tuple[int, Dict]: (예상 API 호출 횟수, 상세 정보)
        """
        search_type = step1_params.get('search_type', 'sale')
        city = step1_params.get('city', '')
        district = step1_params.get('district', '')

        # 1단계는 36개월 데이터를 조회
        months = 36
        base_calls = months

        if search_type == 'sale':
            api_calls = base_calls
            api_type = "매매"
        elif search_type == 'rent':
            api_calls = base_calls
            api_type = "전월세"
        elif search_type == 'all':
            api_calls = base_calls * 2
            api_type = "매매 + 전월세"
        else:
            api_calls = base_calls
            api_type = "매매"

        details = {
            'operation': 'step1_search',
            'city': city,
            'district': district,
            'search_type': search_type,
            'api_type': api_type,
            'months': months,
            'total_calls': api_calls,
            'estimated_time': self._estimate_time(api_calls),
            'cost_info': self._get_cost_info(api_calls)
        }

        return api_calls, details

    def _estimate_time(self, api_calls: int) -> Dict:
        """API 호출 시간 예측"""
        # API 딜레이: 기본 0.05초 + 네트워크/처리 시간
        estimated_seconds = api_calls * 0.5  # 호출당 평균 0.5초로 가정

        if estimated_seconds < 60:
            time_text = f"{estimated_seconds:.0f}초"
        elif estimated_seconds < 3600:
            time_text = f"{estimated_seconds/60:.1f}분"
        else:
            time_text = f"{estimated_seconds/3600:.1f}시간"

        return {
            'seconds': estimated_seconds,
            'display': time_text
        }

    def _get_cost_info(self, api_calls: int) -> Dict:
        """API 호출 비용 정보"""
        # 국토교통부 API는 무료이지만 일일 호출 제한이 있음
        daily_limit = 10000  # 일일 호출 제한

        return {
            'is_free': True,
            'daily_limit': daily_limit,
            'remaining_calls': max(0, daily_limit - api_calls),
            'usage_percentage': min(100, (api_calls / daily_limit) * 100)
        }

    def generate_confirmation_message(self, operation: str, api_calls: int, details: Dict) -> str:
        """사용자 확인 메시지 생성"""
        if operation == 'search':
            message = f"""
🔍 **검색 작업 확인**

**검색 정보:**
- 검색 타입: {details['api_type']}
- 조회 기간: {details['months']}개월
- 예상 API 호출: **{api_calls}회**
- 예상 소요 시간: **{details['estimated_time']['display']}**

**API 사용량:**
- 일일 한도: {details['cost_info']['daily_limit']}회
- 사용률: {details['cost_info']['usage_percentage']:.1f}%

이 작업을 계속 진행하시겠습니까?
"""
        elif operation == 'refresh':
            message = f"""
🔄 **데이터 새로고침 확인**

**새로고침 정보:**
- 대상: {details['apt_name']}
- 조회 기간: {details['months']}개월
- 예상 API 호출: **{api_calls}회**
- 예상 소요 시간: **{details['estimated_time']['display']}**

**API 사용량:**
- 일일 한도: {details['cost_info']['daily_limit']}회
- 사용률: {details['cost_info']['usage_percentage']:.1f}%

이 작업을 계속 진행하시겠습니까?
"""
        elif operation == 'step1':
            message = f"""
📍 **지역 검색 확인**

**검색 정보:**
- 지역: {details['city']} {details['district']}
- 검색 타입: {details['api_type']}
- 조회 기간: {details['months']}개월
- 예상 API 호출: **{api_calls}회**
- 예상 소요 시간: **{details['estimated_time']['display']}**

**API 사용량:**
- 일일 한도: {details['cost_info']['daily_limit']}회
- 사용률: {details['cost_info']['usage_percentage']:.1f}%

이 작업을 계속 진행하시겠습니까?
"""
        else:
            message = f"""
⚙️ **API 호출 확인**

- 예상 API 호출: **{api_calls}회**
- 예상 소요 시간: **{details['estimated_time']['display']}**

이 작업을 계속 진행하시겠습니까?
"""

        return message.strip()