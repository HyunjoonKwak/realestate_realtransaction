#!/usr/bin/env python3
"""
API 호출 추적 및 결과 비교 모듈
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

class APICallTracker:
    """API 호출 추적 클래스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.call_history = {}  # 호출 기록 저장
        self.active_operations = {}  # 진행 중인 작업

    def start_operation(self, operation_id: str, operation_type: str, estimated_calls: int, details: Dict) -> str:
        """
        API 작업 시작 추적

        Args:
            operation_id: 작업 고유 ID
            operation_type: 작업 타입 ('search', 'refresh', 'step1')
            estimated_calls: 예상 API 호출 횟수
            details: 작업 상세 정보

        Returns:
            str: 추적 ID
        """
        start_time = time.time()

        tracking_data = {
            'operation_id': operation_id,
            'operation_type': operation_type,
            'estimated_calls': estimated_calls,
            'actual_calls': 0,
            'start_time': start_time,
            'end_time': None,
            'duration': None,
            'estimated_duration': details.get('estimated_time', {}).get('seconds', 0),
            'details': details,
            'api_calls': [],  # 개별 API 호출 기록
            'status': 'running',
            'error': None
        }

        self.active_operations[operation_id] = tracking_data
        self.logger.info(f"🚀 API 작업 시작 추적: {operation_id} ({operation_type})")

        return operation_id

    def record_api_call(self, operation_id: str, api_type: str, region_code: str, deal_ymd: str, success: bool, response_time: float, data_count: int = 0):
        """
        개별 API 호출 기록

        Args:
            operation_id: 작업 ID
            api_type: API 타입 ('sale', 'rent')
            region_code: 지역코드
            deal_ymd: 거래년월
            success: 성공 여부
            response_time: 응답 시간
            data_count: 받은 데이터 개수
        """
        if operation_id not in self.active_operations:
            self.logger.warning(f"⚠️ 알 수 없는 작업 ID: {operation_id}")
            return

        call_record = {
            'timestamp': time.time(),
            'api_type': api_type,
            'region_code': region_code,
            'deal_ymd': deal_ymd,
            'success': success,
            'response_time': response_time,
            'data_count': data_count
        }

        self.active_operations[operation_id]['api_calls'].append(call_record)
        self.active_operations[operation_id]['actual_calls'] += 1

        self.logger.debug(f"📞 API 호출 기록: {operation_id} - {api_type} {region_code} {deal_ymd} ({'성공' if success else '실패'})")

    def complete_operation(self, operation_id: str, success: bool = True, error: str = None, total_data_count: int = 0) -> Dict:
        """
        API 작업 완료 및 결과 생성

        Args:
            operation_id: 작업 ID
            success: 전체 작업 성공 여부
            error: 에러 메시지 (있는 경우)
            total_data_count: 총 받은 데이터 개수

        Returns:
            Dict: 작업 결과 및 분석 정보
        """
        if operation_id not in self.active_operations:
            self.logger.warning(f"⚠️ 완료할 작업을 찾을 수 없음: {operation_id}")
            return {}

        tracking_data = self.active_operations[operation_id]
        end_time = time.time()

        tracking_data['end_time'] = end_time
        tracking_data['duration'] = end_time - tracking_data['start_time']
        tracking_data['status'] = 'completed' if success else 'failed'
        tracking_data['error'] = error
        tracking_data['total_data_count'] = total_data_count

        # 결과 분석
        result = self._analyze_operation_result(tracking_data)

        # 기록을 history로 이동
        self.call_history[operation_id] = tracking_data
        del self.active_operations[operation_id]

        self.logger.info(f"✅ API 작업 완료: {operation_id} - 예상: {tracking_data['estimated_calls']}회, 실제: {tracking_data['actual_calls']}회")

        return result

    def _analyze_operation_result(self, tracking_data: Dict) -> Dict:
        """작업 결과 분석"""
        estimated_calls = tracking_data['estimated_calls']
        actual_calls = tracking_data['actual_calls']
        estimated_duration = tracking_data['estimated_duration']
        actual_duration = tracking_data['duration']

        # 호출 횟수 정확도
        call_accuracy = self._calculate_accuracy(estimated_calls, actual_calls)

        # 시간 정확도
        time_accuracy = self._calculate_accuracy(estimated_duration, actual_duration)

        # 성공률 계산
        successful_calls = sum(1 for call in tracking_data['api_calls'] if call['success'])
        success_rate = (successful_calls / actual_calls * 100) if actual_calls > 0 else 0

        # 평균 응답 시간
        avg_response_time = sum(call['response_time'] for call in tracking_data['api_calls']) / len(tracking_data['api_calls']) if tracking_data['api_calls'] else 0

        # 총 데이터 수
        total_data_from_calls = sum(call['data_count'] for call in tracking_data['api_calls'])

        result = {
            'operation_info': {
                'operation_id': tracking_data['operation_id'],
                'operation_type': tracking_data['operation_type'],
                'status': tracking_data['status'],
                'duration': actual_duration,
                'total_data_count': tracking_data.get('total_data_count', total_data_from_calls)
            },
            'prediction_vs_actual': {
                'estimated_calls': estimated_calls,
                'actual_calls': actual_calls,
                'call_difference': actual_calls - estimated_calls,
                'call_accuracy': call_accuracy,
                'estimated_duration': estimated_duration,
                'actual_duration': actual_duration,
                'time_difference': actual_duration - estimated_duration,
                'time_accuracy': time_accuracy
            },
            'performance_metrics': {
                'success_rate': success_rate,
                'successful_calls': successful_calls,
                'failed_calls': actual_calls - successful_calls,
                'avg_response_time': avg_response_time,
                'total_data_received': total_data_from_calls
            },
            'api_call_details': tracking_data['api_calls'],
            'accuracy_assessment': self._get_accuracy_assessment(call_accuracy, time_accuracy),
            'recommendations': self._get_recommendations(tracking_data, call_accuracy, time_accuracy)
        }

        return result

    def _calculate_accuracy(self, estimated: float, actual: float) -> float:
        """정확도 계산 (0-100%)"""
        if estimated == 0 and actual == 0:
            return 100.0
        if estimated == 0:
            return 0.0

        accuracy = max(0, 100 - abs(estimated - actual) / estimated * 100)
        return round(accuracy, 1)

    def _get_accuracy_assessment(self, call_accuracy: float, time_accuracy: float) -> Dict:
        """정확도 평가"""
        overall_accuracy = (call_accuracy + time_accuracy) / 2

        if overall_accuracy >= 90:
            grade = "매우 정확"
            color = "success"
            icon = "fas fa-check-circle"
        elif overall_accuracy >= 70:
            grade = "정확"
            color = "info"
            icon = "fas fa-info-circle"
        elif overall_accuracy >= 50:
            grade = "보통"
            color = "warning"
            icon = "fas fa-exclamation-triangle"
        else:
            grade = "부정확"
            color = "danger"
            icon = "fas fa-times-circle"

        return {
            'overall_accuracy': overall_accuracy,
            'grade': grade,
            'color': color,
            'icon': icon,
            'call_accuracy': call_accuracy,
            'time_accuracy': time_accuracy
        }

    def _get_recommendations(self, tracking_data: Dict, call_accuracy: float, time_accuracy: float) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []

        # 호출 횟수 정확도 기반 권장사항
        if call_accuracy < 80:
            actual_calls = tracking_data['actual_calls']
            estimated_calls = tracking_data['estimated_calls']

            if actual_calls > estimated_calls:
                recommendations.append("예상보다 많은 API 호출이 발생했습니다. 캐시 활용을 늘려보세요.")
            else:
                recommendations.append("예상보다 적은 API 호출이 발생했습니다. 예측 모델을 조정해야 합니다.")

        # 시간 정확도 기반 권장사항
        if time_accuracy < 80:
            actual_duration = tracking_data['duration']
            estimated_duration = tracking_data['estimated_duration']

            if actual_duration > estimated_duration:
                recommendations.append("예상보다 오래 걸렸습니다. 네트워크 상태를 확인하거나 동시 호출 수를 늘려보세요.")
            else:
                recommendations.append("예상보다 빠르게 완료되었습니다. 시간 예측 모델을 개선할 수 있습니다.")

        # 성공률 기반 권장사항
        successful_calls = sum(1 for call in tracking_data['api_calls'] if call['success'])
        success_rate = (successful_calls / tracking_data['actual_calls'] * 100) if tracking_data['actual_calls'] > 0 else 0

        if success_rate < 95:
            recommendations.append("일부 API 호출이 실패했습니다. 재시도 로직을 개선해보세요.")

        # 응답 시간 기반 권장사항
        if tracking_data['api_calls']:
            avg_response_time = sum(call['response_time'] for call in tracking_data['api_calls']) / len(tracking_data['api_calls'])
            if avg_response_time > 2.0:
                recommendations.append("API 응답 시간이 느립니다. 요청 간격을 조정하거나 서버 상태를 확인하세요.")

        if not recommendations:
            recommendations.append("모든 지표가 양호합니다. 현재 설정을 유지하세요.")

        return recommendations

    def get_operation_summary(self, operation_id: str) -> Optional[Dict]:
        """작업 요약 정보 조회"""
        if operation_id in self.call_history:
            return self.call_history[operation_id]
        elif operation_id in self.active_operations:
            return self.active_operations[operation_id]
        else:
            return None

    def get_operation_result(self, operation_id: str) -> Optional[Dict]:
        """작업 결과 정보 조회 (웹 응답용)"""
        operation_data = self.get_operation_summary(operation_id)
        if not operation_data:
            return None

        # 완료된 작업만 결과 반환
        if operation_data.get('status') != 'completed':
            return None

        # 결과 분석 생성
        result = self._analyze_operation_result(operation_data)
        return result

    def generate_completion_message(self, result: Dict) -> str:
        """완료 메시지 생성"""
        op_info = result['operation_info']
        prediction = result['prediction_vs_actual']
        performance = result['performance_metrics']
        assessment = result['accuracy_assessment']

        operation_type_names = {
            'search': '검색',
            'refresh': '새로고침',
            'step1': '1단계 검색'
        }

        operation_name = operation_type_names.get(op_info['operation_type'], op_info['operation_type'])

        message = f"""
🎯 **{operation_name} 작업 완료**

**📊 예측 vs 실제 결과:**
- API 호출: {prediction['estimated_calls']}회 예상 → **{prediction['actual_calls']}회 실제** ({prediction['call_difference']:+d})
- 소요 시간: {prediction['estimated_duration']:.1f}초 예상 → **{prediction['actual_duration']:.1f}초 실제** ({prediction['time_difference']:+.1f}초)

**📈 성능 지표:**
- 성공률: **{performance['success_rate']:.1f}%** ({performance['successful_calls']}/{prediction['actual_calls']})
- 평균 응답 시간: **{performance['avg_response_time']:.2f}초**
- 총 데이터: **{performance['total_data_received']:,}건**

**🎖️ 예측 정확도:**
- 전체 정확도: **{assessment['overall_accuracy']:.1f}%** ({assessment['grade']})
- 호출 횟수: {assessment['call_accuracy']:.1f}%
- 시간 예측: {assessment['time_accuracy']:.1f}%

**💡 권장사항:**
{chr(10).join(f"• {rec}" for rec in result['recommendations'])}
"""
        return message.strip()


# 전역 추적기 인스턴스
api_tracker = APICallTracker()


def track_api_calls(operation_type: str):
    """API 호출 추적 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 작업 ID 생성
            operation_id = f"{operation_type}_{int(time.time())}_{id(func)}"

            try:
                # 함수 실행
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # 에러 발생 시 추적 완료
                if operation_id in api_tracker.active_operations:
                    api_tracker.complete_operation(operation_id, success=False, error=str(e))
                raise
        return wrapper
    return decorator