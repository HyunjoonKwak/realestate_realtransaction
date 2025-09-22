/**
 * API 호출 결과 표시 모달 관련 JavaScript
 */

class APIResultModal {
    constructor() {
        this.modal = null;
    }

    /**
     * API 호출 결과 모달 표시
     * @param {Object} result - API 호출 결과 데이터
     */
    showResultModal(result) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'apiResultModal';
        modal.innerHTML = this.generateModalHTML(result);

        // 기존 모달 제거
        const existingModal = document.getElementById('apiResultModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        // 모달이 닫힐 때 정리
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    /**
     * 모달 HTML 생성
     * @param {Object} result - API 호출 결과
     * @returns {string} HTML 문자열
     */
    generateModalHTML(result) {
        const opInfo = result.operation_info;
        const prediction = result.prediction_vs_actual;
        const performance = result.performance_metrics;
        const assessment = result.accuracy_assessment;

        const operationTypeNames = {
            'search': '검색',
            'refresh': '새로고침',
            'step1': '1단계 검색'
        };

        const operationName = operationTypeNames[opInfo.operation_type] || opInfo.operation_type;

        return `
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-chart-line text-success me-2"></i>
                            ${operationName} 작업 완료 결과
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- 전체 요약 -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <div class="alert alert-${assessment.color}">
                                    <i class="${assessment.icon} me-2"></i>
                                    <strong>전체 정확도: ${assessment.overall_accuracy.toFixed(1)}% (${assessment.grade})</strong>
                                </div>
                            </div>
                        </div>

                        <!-- 예측 vs 실제 비교 -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h6><i class="fas fa-balance-scale text-primary me-2"></i>예측 vs 실제 결과</h6>
                                <div class="table-responsive">
                                    <table class="table table-striped">
                                        <thead class="table-primary">
                                            <tr>
                                                <th>항목</th>
                                                <th>예상값</th>
                                                <th>실제값</th>
                                                <th>차이</th>
                                                <th>정확도</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td><strong>API 호출 횟수</strong></td>
                                                <td>${prediction.estimated_calls}회</td>
                                                <td><strong>${prediction.actual_calls}회</strong></td>
                                                <td class="${this.getDifferenceClass(prediction.call_difference)}">${this.formatDifference(prediction.call_difference, '회')}</td>
                                                <td>${this.getAccuracyBadge(prediction.call_accuracy)}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>소요 시간</strong></td>
                                                <td>${prediction.estimated_duration.toFixed(1)}초</td>
                                                <td><strong>${prediction.actual_duration.toFixed(1)}초</strong></td>
                                                <td class="${this.getDifferenceClass(prediction.time_difference)}">${this.formatDifference(prediction.time_difference, '초', 1)}</td>
                                                <td>${this.getAccuracyBadge(prediction.time_accuracy)}</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <!-- 성능 지표 -->
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="card bg-light">
                                    <div class="card-body text-center">
                                        <h6 class="card-title">성공률</h6>
                                        <h3 class="text-${performance.success_rate >= 95 ? 'success' : performance.success_rate >= 80 ? 'warning' : 'danger'}">
                                            ${performance.success_rate.toFixed(1)}%
                                        </h3>
                                        <small class="text-muted">${performance.successful_calls}/${prediction.actual_calls}</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-light">
                                    <div class="card-body text-center">
                                        <h6 class="card-title">평균 응답시간</h6>
                                        <h3 class="text-info">${performance.avg_response_time.toFixed(2)}초</h3>
                                        <small class="text-muted">호출당 평균</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-light">
                                    <div class="card-body text-center">
                                        <h6 class="card-title">총 데이터</h6>
                                        <h3 class="text-primary">${performance.total_data_received.toLocaleString()}건</h3>
                                        <small class="text-muted">수집된 데이터</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-light">
                                    <div class="card-body text-center">
                                        <h6 class="card-title">실행 시간</h6>
                                        <h3 class="text-secondary">${opInfo.duration.toFixed(1)}초</h3>
                                        <small class="text-muted">총 소요시간</small>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- API 호출 상세 내역 -->
                        ${this.generateCallDetailsHTML(result.api_call_details)}

                        <!-- 권장사항 -->
                        <div class="row">
                            <div class="col-12">
                                <h6><i class="fas fa-lightbulb text-warning me-2"></i>권장사항</h6>
                                <div class="alert alert-info">
                                    <ul class="mb-0">
                                        ${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-1"></i>닫기
                        </button>
                        <button type="button" class="btn btn-primary" onclick="apiResultModal.exportResult()">
                            <i class="fas fa-download me-1"></i>결과 내보내기
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * API 호출 상세 내역 HTML 생성
     * @param {Array} callDetails - API 호출 상세 내역
     * @returns {string} HTML 문자열
     */
    generateCallDetailsHTML(callDetails) {
        if (!callDetails || callDetails.length === 0) {
            return '<div class="alert alert-warning">API 호출 상세 내역이 없습니다.</div>';
        }

        const totalCalls = callDetails.length;
        const successfulCalls = callDetails.filter(call => call.success).length;
        const failedCalls = totalCalls - successfulCalls;

        let html = `
            <div class="row mb-4">
                <div class="col-12">
                    <h6><i class="fas fa-list text-secondary me-2"></i>API 호출 상세 내역</h6>
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <span>총 ${totalCalls}건 (성공: ${successfulCalls}건, 실패: ${failedCalls}건)</span>
                        <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#callDetailsCollapse">
                            <i class="fas fa-eye me-1"></i>상세보기
                        </button>
                    </div>
                    <div class="collapse" id="callDetailsCollapse">
                        <div class="table-responsive" style="max-height: 300px; overflow-y: auto;">
                            <table class="table table-sm table-striped">
                                <thead class="table-secondary sticky-top">
                                    <tr>
                                        <th>#</th>
                                        <th>타입</th>
                                        <th>지역코드</th>
                                        <th>년월</th>
                                        <th>응답시간</th>
                                        <th>데이터 수</th>
                                        <th>상태</th>
                                    </tr>
                                </thead>
                                <tbody>
        `;

        callDetails.forEach((call, index) => {
            const statusClass = call.success ? 'success' : 'danger';
            const statusIcon = call.success ? 'check-circle' : 'times-circle';
            const statusText = call.success ? '성공' : '실패';

            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td><span class="badge bg-${call.api_type === 'sale' ? 'primary' : 'info'}">${call.api_type === 'sale' ? '매매' : '전월세'}</span></td>
                    <td>${call.region_code}</td>
                    <td>${call.deal_ymd}</td>
                    <td>${call.response_time.toFixed(2)}초</td>
                    <td>${call.data_count.toLocaleString()}건</td>
                    <td><span class="badge bg-${statusClass}"><i class="fas fa-${statusIcon} me-1"></i>${statusText}</span></td>
                </tr>
            `;
        });

        html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;

        return html;
    }

    /**
     * 차이값에 따른 CSS 클래스 반환
     * @param {number} difference - 차이값
     * @returns {string} CSS 클래스
     */
    getDifferenceClass(difference) {
        if (difference > 0) return 'text-danger';
        if (difference < 0) return 'text-success';
        return 'text-muted';
    }

    /**
     * 차이값 포맷팅
     * @param {number} difference - 차이값
     * @param {string} unit - 단위
     * @param {number} decimals - 소수점 자릿수
     * @returns {string} 포맷된 문자열
     */
    formatDifference(difference, unit, decimals = 0) {
        const sign = difference > 0 ? '+' : '';
        const value = decimals > 0 ? difference.toFixed(decimals) : Math.round(difference);
        return `${sign}${value}${unit}`;
    }

    /**
     * 정확도 배지 생성
     * @param {number} accuracy - 정확도 (0-100)
     * @returns {string} 배지 HTML
     */
    getAccuracyBadge(accuracy) {
        let badgeClass, icon;
        if (accuracy >= 90) {
            badgeClass = 'success';
            icon = 'check-circle';
        } else if (accuracy >= 70) {
            badgeClass = 'info';
            icon = 'info-circle';
        } else if (accuracy >= 50) {
            badgeClass = 'warning';
            icon = 'exclamation-triangle';
        } else {
            badgeClass = 'danger';
            icon = 'times-circle';
        }

        return `<span class="badge bg-${badgeClass}"><i class="fas fa-${icon} me-1"></i>${accuracy.toFixed(1)}%</span>`;
    }

    /**
     * 결과 내보내기
     */
    exportResult() {
        // 현재 모달의 데이터를 JSON 파일로 내보내기
        const modalData = this.currentResult;
        if (!modalData) {
            alert('내보낼 데이터가 없습니다.');
            return;
        }

        const dataStr = JSON.stringify(modalData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });

        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `api_result_${modalData.operation_info.operation_id}_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }

    /**
     * 결과 데이터 저장 (내보내기용)
     * @param {Object} result - 결과 데이터
     */
    setCurrentResult(result) {
        this.currentResult = result;
    }
}

// 전역 인스턴스 생성
const apiResultModal = new APIResultModal();