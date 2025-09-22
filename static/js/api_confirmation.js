/**
 * API 호출 확인 관련 JavaScript 함수들
 */

class APIConfirmation {
    constructor() {
        this.pendingOperation = null;
    }

    /**
     * API 호출 확인 모달 표시
     * @param {Object} data - 확인 데이터
     * @param {Function} onConfirm - 확인 시 실행할 함수
     */
    showConfirmationModal(data, onConfirm) {
        this.pendingOperation = onConfirm;

        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'apiConfirmationModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                            API 호출 확인
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-warning">
                            <strong>주의:</strong> 이 작업은 외부 API를 호출합니다.
                        </div>

                        <div class="row">
                            <div class="col-md-6">
                                <div class="card bg-light">
                                    <div class="card-body">
                                        <h6 class="card-title">예상 API 호출</h6>
                                        <h3 class="text-primary">${data.api_calls}회</h3>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card bg-light">
                                    <div class="card-body">
                                        <h6 class="card-title">예상 소요 시간</h6>
                                        <h3 class="text-info">${data.details.estimated_time.display}</h3>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="mt-3">
                            <h6>상세 정보:</h6>
                            <ul class="list-unstyled">
                                ${this.generateDetailsList(data.details)}
                            </ul>
                        </div>

                        <div class="mt-3">
                            <h6>API 사용량:</h6>
                            <div class="progress">
                                <div class="progress-bar ${this.getProgressBarClass(data.details.cost_info.usage_percentage)}"
                                     style="width: ${Math.min(100, data.details.cost_info.usage_percentage)}%">
                                    ${data.details.cost_info.usage_percentage.toFixed(1)}%
                                </div>
                            </div>
                            <small class="text-muted">
                                일일 한도: ${data.details.cost_info.daily_limit}회 중 ${data.api_calls}회 사용 예정
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-1"></i>취소
                        </button>
                        <button type="button" class="btn btn-primary" onclick="apiConfirmation.confirmOperation()">
                            <i class="fas fa-check me-1"></i>계속 진행
                        </button>
                    </div>
                </div>
            </div>
        `;

        // 기존 모달 제거
        const existingModal = document.getElementById('apiConfirmationModal');
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
     * 상세 정보 리스트 생성
     * @param {Object} details - 상세 정보
     * @returns {string} HTML 문자열
     */
    generateDetailsList(details) {
        const items = [];

        if (details.operation === 'refresh') {
            items.push(`<li><strong>대상:</strong> ${details.apt_name}</li>`);
            items.push(`<li><strong>조회 기간:</strong> ${details.months}개월</li>`);
        } else if (details.operation === 'step1_search') {
            items.push(`<li><strong>지역:</strong> ${details.city} ${details.district}</li>`);
            items.push(`<li><strong>검색 타입:</strong> ${details.api_type}</li>`);
            items.push(`<li><strong>조회 기간:</strong> ${details.months}개월</li>`);
        } else {
            if (details.api_type) {
                items.push(`<li><strong>검색 타입:</strong> ${details.api_type}</li>`);
            }
            if (details.months) {
                items.push(`<li><strong>조회 기간:</strong> ${details.months}개월</li>`);
            }
            if (details.force_refresh) {
                items.push(`<li><strong>강제 새로고침:</strong> 예</li>`);
            }
        }

        return items.join('');
    }

    /**
     * 진행률 바 클래스 반환
     * @param {number} percentage - 사용률
     * @returns {string} CSS 클래스
     */
    getProgressBarClass(percentage) {
        if (percentage < 50) return 'bg-success';
        if (percentage < 80) return 'bg-warning';
        return 'bg-danger';
    }

    /**
     * 작업 확인
     */
    confirmOperation() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('apiConfirmationModal'));
        modal.hide();

        if (this.pendingOperation) {
            this.pendingOperation();
            this.pendingOperation = null;
        }
    }

    /**
     * 검색 API 호출 (확인 포함)
     * @param {Object} searchData - 검색 데이터
     * @param {Function} onSuccess - 성공 콜백
     * @param {Function} onError - 에러 콜백
     */
    performSearch(searchData, onSuccess, onError) {
        // 먼저 캐시 확인을 위한 검색 요청
        this.checkSearchCache(searchData, onSuccess, onError);
    }

    checkSearchCache(searchData, onSuccess, onError) {
        // 먼저 캐시 확인
        fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(searchData)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                // 성공적으로 검색 완료 (캐시 또는 새 데이터)
                onSuccess(result);
            } else if (result.has_cache) {
                // 캐시가 있는 경우 사용자에게 선택권 제공
                this.showCacheChoiceModal(result.cache_info, searchData, onSuccess, onError);
            } else if (result.requires_confirmation) {
                // API 호출 확인이 필요한 경우
                this.showConfirmationModal(result, () => {
                    this.executeConfirmedSearch(searchData, onSuccess, onError);
                });
            } else {
                onError(result);
            }
        })
        .catch(error => {
            console.error('검색 요청 오류:', error);
            onError(error);
        });
    }

    executeConfirmedSearch(searchData, onSuccess, onError) {
        const confirmedData = { ...searchData, confirmed: true };
        fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(confirmedData)
        })
        .then(response => response.json())
        .then(result => {
            // API 추적 결과가 있으면 결과 모달 표시
            if (result.success && result.api_tracking_result) {
                apiResultModal.setCurrentResult(result.api_tracking_result);
                apiResultModal.showResultModal(result.api_tracking_result);
            }
            onSuccess(result);
        })
        .catch(error => {
            console.error('검색 실행 오류:', error);
            onError(error);
        });
    }

    /**
     * 새로고침 API 호출 (확인 포함)
     * @param {string} aptName - 아파트명
     * @param {string} regionCode - 지역코드
     * @param {Function} onSuccess - 성공 콜백
     * @param {Function} onError - 에러 콜백
     */
    performRefresh(aptName, regionCode, onSuccess, onError) {
        // 먼저 예측 API 호출
        fetch(`/api/refresh/estimate/${encodeURIComponent(aptName)}/${regionCode}`)
        .then(response => response.json())
        .then(estimateData => {
            if (estimateData.success) {
                // 확인 모달 표시
                this.showConfirmationModal(estimateData, () => {
                    // 확인된 경우 실제 새로고침 실행
                    fetch(`/api/refresh/${encodeURIComponent(aptName)}/${regionCode}?confirmed=true`)
                    .then(response => response.json())
                    .then(result => {
                        // API 추적 결과가 있으면 결과 모달 표시
                        if (result.api_tracking_result) {
                            apiResultModal.setCurrentResult(result.api_tracking_result);
                            apiResultModal.showResultModal(result.api_tracking_result);
                        }
                        onSuccess(result);
                    })
                    .catch(onError);
                });
            } else {
                onError(estimateData);
            }
        })
        .catch(onError);
    }

    /**
     * 1단계 검색 API 호출 (확인 포함)
     * @param {Object} step1Data - 1단계 검색 데이터
     * @param {Function} onSuccess - 성공 콜백
     * @param {Function} onError - 에러 콜백
     */
    performStep1Search(step1Data, onSuccess, onError) {
        // 먼저 예측 API 호출
        fetch('/api/search/step1/estimate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(step1Data)
        })
        .then(response => response.json())
        .then(estimateData => {
            if (estimateData.success) {
                // 확인 모달 표시
                this.showConfirmationModal(estimateData, () => {
                    // 확인된 경우 실제 검색 실행
                    const confirmedData = { ...step1Data, confirmed: true };
                    fetch('/api/search/step1', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(confirmedData)
                    })
                    .then(response => response.json())
                    .then(onSuccess)
                    .catch(onError);
                });
            } else {
                onError(estimateData);
            }
        })
        .catch(onError);
    }

    /**
     * 캐시 선택 모달 표시
     * @param {Object} cacheInfo - 캐시 정보
     * @param {Object} searchData - 검색 데이터
     * @param {Function} onSuccess - 성공 콜백
     * @param {Function} onError - 에러 콜백
     */
    showCacheChoiceModal(cacheInfo, searchData, onSuccess, onError) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'cacheChoiceModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-database text-info me-2"></i>
                            캐시된 데이터 발견
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            <strong>${cacheInfo.region_name}</strong> 지역의 캐시된 데이터가 있습니다.
                        </div>

                        <div class="row mb-3">
                            <div class="col-md-4">
                                <div class="card bg-light">
                                    <div class="card-body text-center">
                                        <h6 class="card-title">데이터 수</h6>
                                        <h4 class="text-primary">${cacheInfo.total_count.toLocaleString()}건</h4>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card bg-light">
                                    <div class="card-body text-center">
                                        <h6 class="card-title">생성 시간</h6>
                                        <p class="mb-0">${new Date(cacheInfo.created_at).toLocaleString()}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card bg-light">
                                    <div class="card-body text-center">
                                        <h6 class="card-title">데이터 나이</h6>
                                        <h4 class="text-warning">${cacheInfo.data_age_hours}시간</h4>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-6">
                                <div class="card h-100">
                                    <div class="card-body">
                                        <h6 class="card-title">
                                            <i class="fas fa-lightning-bolt text-success me-2"></i>
                                            캐시 사용
                                        </h6>
                                        <ul class="list-unstyled">
                                            <li><i class="fas fa-check text-success me-2"></i>즉시 결과 표시</li>
                                            <li><i class="fas fa-check text-success me-2"></i>API 호출 없음</li>
                                            <li><i class="fas fa-check text-success me-2"></i>빠른 로딩</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card h-100">
                                    <div class="card-body">
                                        <h6 class="card-title">
                                            <i class="fas fa-sync-alt text-primary me-2"></i>
                                            새로 조회
                                        </h6>
                                        <ul class="list-unstyled">
                                            <li><i class="fas fa-check text-primary me-2"></i>최신 데이터</li>
                                            <li><i class="fas fa-check text-primary me-2"></i>정확한 정보</li>
                                            <li><i class="fas fa-clock text-warning me-2"></i>API 호출 시간 필요</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-success" id="useCacheBtn">
                            <i class="fas fa-lightning-bolt me-2"></i>캐시 사용
                        </button>
                        <button type="button" class="btn btn-primary" id="refreshDataBtn">
                            <i class="fas fa-sync-alt me-2"></i>새로 조회
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const bootstrapModal = new bootstrap.Modal(modal);

        // 캐시 사용 버튼 클릭
        modal.querySelector('#useCacheBtn').onclick = () => {
            bootstrapModal.hide();
            const cacheData = { ...searchData, cache_choice: 'use_cache' };
            this.executeSearch(cacheData, onSuccess, onError);
        };

        // 새로 조회 버튼 클릭
        modal.querySelector('#refreshDataBtn').onclick = () => {
            bootstrapModal.hide();
            const refreshData = { ...searchData, cache_choice: 'refresh' };
            this.executeAPISearch(refreshData, onSuccess, onError);
        };

        // 모달 닫힐 때 DOM에서 제거
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });

        bootstrapModal.show();
    }

    executeSearch(searchData, onSuccess, onError) {
        fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(searchData)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                onSuccess(result);
            } else {
                onError(result);
            }
        })
        .catch(error => {
            console.error('검색 실행 오류:', error);
            onError(error);
        });
    }

    executeAPISearch(searchData, onSuccess, onError) {
        // API 예측 먼저 확인
        fetch('/api/search/estimate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(searchData)
        })
        .then(response => response.json())
        .then(estimateData => {
            if (estimateData.success) {
                // 확인 모달 표시
                this.showConfirmationModal(estimateData, () => {
                    this.executeConfirmedSearch(searchData, onSuccess, onError);
                });
            } else {
                onError(estimateData);
            }
        })
        .catch(error => {
            console.error('검색 예측 오류:', error);
            onError(error);
        });
    }
}

// 전역 인스턴스 생성
const apiConfirmation = new APIConfirmation();