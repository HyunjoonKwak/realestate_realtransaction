# 🏠 국토교통부 실거래가 조회 시스템

국토교통부 공식 실거래가 API를 활용한 아파트 실거래가 조회 및 관심단지 추적 시스템입니다.

## ✨ 주요 기능

- **🔍 아파트 검색**: 시/도 → 군/구 계층적 지역 선택 및 아파트명 검색
- **📊 3단계 데이터 분석**: 법정동별, 월별, 아파트별 체계적 데이터 분류
- **❤️ 관심단지 관리**: 관심단지 등록 및 가격 동향 추적
- **⚡ 스마트 캐싱**: 24시간 캐시로 빠른 검색 응답
- **📈 가격 동향 차트**: Chart.js 기반 인터랙티브 분석
- **📄 CSV 내보내기**: 거래 데이터 다운로드 기능

## 🛠 기술 스택

- **Backend**: Python, Flask
- **Database**: SQLite (캐싱 시스템)
- **Frontend**: Bootstrap 5, Chart.js
- **API**: 국토교통부 공공데이터 API

## 📋 요구사항

- Python 3.8+
- 국토교통부 공공데이터 API 키 (필수)

## ⚙️ 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd naver_real_estate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. API 키 설정 (필수!)
```bash
# .env 파일 생성 및 설정
cp env.example .env
# .env 파일에서 MOLIT_API_KEY=발급받은_키 입력
```

**📖 자세한 API 설정 방법:**
1. [공공데이터포털](https://www.data.go.kr/) 회원가입
2. '아파트매매 실거래 상세자료' API 신청
3. 승인 후 인증키 복사
4. `.env` 파일에 `MOLIT_API_KEY=발급받은_키` 설정

### 4. 프로그램 실행
```bash
python main.py
```

### 5. 웹 브라우저 접속
```
http://localhost:8080
```

## 🖥️ 백그라운드 실행 (EC2/서버용)

서버 환경에서 백그라운드로 안전하게 실행하고 관리할 수 있는 스크립트를 제공합니다.

### 백그라운드 시작
```bash
./start.sh
```

### 프로세스 중지
```bash
./stop.sh
```

### 로그 확인
```bash
tail -f app.log        # 실시간 로그 확인
cat app.log           # 전체 로그 확인
```

### 주요 기능
- **🔒 안전한 프로세스 관리**: PID 파일 기반 중복 실행 방지
- **📝 자동 로깅**: 모든 출력을 `app.log` 파일에 저장
- **🔄 스마트 종료**: 일반 종료 실패시 강제 종료 자동 시도
- **🧹 자동 정리**: 종료시 PID 파일 자동 삭제

## 🔧 환경 설정

`.env` 파일에서 다음 설정을 조정할 수 있습니다:

```bash
# 필수 설정
MOLIT_API_KEY=발급받은_실제_인증키

# 웹 서버 설정
FLASK_HOST=0.0.0.0
FLASK_PORT=8080
FLASK_DEBUG=True
FLASK_SECRET_KEY=your-secret-key-here

# API 호출 설정
API_REQUEST_DELAY=0.1     # API 호출 간격 (초)
API_TIMEOUT=15            # API 타임아웃 (초)
API_MAX_RETRIES=3         # 최대 재시도 횟수

# 로깅 설정
LOG_LEVEL=INFO
```

## 📁 프로젝트 구조

```
naver_real_estate/
├── main.py                      # 메인 실행 파일
├── requirements.txt             # 의존성 목록
├── env.example                  # 환경 설정 예제
├── README.md                    # 프로젝트 설명서
├── CLAUDE.md                    # 개발 가이드 (Claude Code용)
├── dong_code_active.txt         # 활성 법정동 코드 데이터
├── dong_labels.json             # 법정동 레이블 데이터
├── dong_labels.txt              # 법정동 레이블 (텍스트)
├── src/                         # 소스 코드
│   ├── __init__.py
│   ├── molit_api.py            # 국토교통부 API 연동
│   ├── database.py             # SQLite 데이터베이스 관리
│   └── web_app.py              # Flask 웹 애플리케이션
├── templates/                   # HTML 템플릿
│   ├── base.html               # 기본 템플릿
│   ├── index.html              # 대시보드
│   ├── search.html             # 아파트 검색 (3단계 탭)
│   ├── apartment_detail.html   # 아파트 상세 정보
│   ├── favorites.html          # 관심단지 관리
│   └── error.html              # 오류 페이지
└── apartment_tracker.db        # SQLite 데이터베이스
```

## 🚀 사용 방법

### 1. 아파트 검색
1. 시/도 선택 → 군/구 선택
2. 아파트명 입력 (선택사항)
3. 기간 설정 (기간별/날짜별)
4. 검색 실행

### 2. 3단계 데이터 분석
검색 후 3가지 탭으로 체계적 분석:
- **법정동별**: 지역별 거래 현황 (월별/아파트별 필터)
- **월별**: 시간별 시장 동향 (아파트별 필터)
- **아파트별**: 개별 단지 분석 (월별 필터)

### 3. 관심단지 관리
- 검색 결과에서 하트 아이콘 클릭으로 등록
- 대시보드에서 가격 동향 추적
- 상세 페이지에서 차트 및 CSV 내보내기

## 📊 지원 지역

**전국 17개 시/도** 모든 지역 지원
- 특별시/광역시 8개 (서울, 부산, 대구, 인천, 광주, 대전, 울산, 세종)
- 특별자치도 3개 (강원, 전북, 제주)
- 일반 도 6개 (경기, 충북, 충남, 전남, 경북, 경남)

## ⚠️ 주의사항

- **API 제한**: 일일 1,000회, 분당 100회 호출 제한
- **데이터 범위**: 최근 5년 아파트 실거래 데이터만 지원
- **개인 사용 목적**: 상업적 이용 금지

## 🔧 문제 해결

### 주요 오류 및 해결방법
- **API 키 오류**: `.env` 파일의 `MOLIT_API_KEY` 확인
- **데이터 없음**: 해당 지역/기간에 실거래가 없거나 API 키 문제
- **네트워크 오류**: 인터넷 연결 및 방화벽 설정 확인

---

**⚠️ 중요**: 교육 및 개인 사용 목적으로만 사용하시고, 관련 법규와 이용약관을 준수해주세요.
