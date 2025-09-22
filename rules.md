# 구현 요구사항 및 해결 내역

이 문서는 사용자가 정의하는 프로그램의 동작 요구사항을 기술합니다.

## 프로그램의 목적
1. 본 프로그램의 명칭은 <아파트 실거래가 조회 시스템> 으로 한다.

## 프로그램 구성
- 메뉴 구성은 다음과 같이 한다.
 -- 대시보드 , 아파트 검색, 설정

- 각 메뉴별 동작은 다음가 같이 한다.
 -- 대시보드 
  --- 관심단지로 선정된 단지들을 타일 형태로 보여준다. 
  --- 각 타일에서는 상세보기를 지원하고 상세보기를 누르면 단지별 상세정보를 보여준다. 상세정보에는 가격동향, 거래내역을 상세히 분석하여 보여준다.
  --- 각 타일별 데이터 새로고침 기능을 추가하고 버튼을 누르면 캐시를 초기화 할껀지 여부를 묻고 진행한다. 
 -- 아파트 검색
  --- 아파트를 검색하는 메뉴인데 여기서는 아래와 같은 조건으로 검색한다.
   --- 1단계 : 시/도
   --- 2단계 : 시/군/구
   --- 3단계 : 읍/면/동
  -- 각 단계별 지역 데이터는 dong_code_active.txt 파일을 활용하여 파싱한다.
  -- 2단계까지만 선택해도 5자리의 지역코드가 확보되므로 아파트 검색을 실행할 수 있게 한다. 그리고 결과를 보여줄때 2단계 선택후 검색이므로 2단계지역까지 결과를 보여준다. 그 이후에 3단계 읍/면/동 을 선택하면 거기에 맞게 해당지역만 캐시를 활용해 필터링해서 보여준다.
  -- 3단계까지 선택하면 5자리의 지역코드를 활용해서 검색을 한 후, 3단계 지역 선택한 지역만 필터링 해서 보여준다.
  -- 검색한 아파트 에서 관심단지를 선정할 수 있게 하고 선정한 아파트 단지는 관심단지 리스트로 별도 관리한다. 대시보드에서 활용한다.

 -- 설정
  --- 설정기능에는 API 테스트 기능과 데이터베이스, 캐시 초기화 기능들을 포함한다.
  --- API 테스트 기능에는 매매 API 테스트 와 전월세 API 테스트 기능을 포함한다. 지역코드 와 거래년월을 입력받고 해당 데이터를 기반으로 API 호출기능을 시험한다.
  --- 데이터베이스 초기화 와 캐시 초기화 기능은 말 그대로 가지고 있는 데이터베이스나 캐시를 초기화 하는 기능이다.

## 세부 요청사항

### 1. 검색이나 새로고침 등의 동작을 할때 캐시를 이용하는지 API 호출을 이용하는지 체크해서 알려주고 API 호출의 경우 몇회를 호출할 예정인지 알려주고 호출이 왼료되면 총 몇회의 호출이 실제로 실행되었는지 알려주는 기능 구현
### 2. 진행률 및 결과 추적 모달

### 신규구현사항 (추가)

#### 현재 구현 완료 상태 (2025-09-21 기준)
- ✅ 대시보드: 관심단지 타일 형태 표시, 상세보기, 데이터 새로고침 기능
- ✅ 아파트 검색: 3단계 계층적 검색 (시/도 → 시/군/구 → 읍/면/동)
- ✅ 검색 진행률 및 결과 추적 모달 시스템
- ✅ API 호출 횟수 예측 및 실제 호출 결과 표시
- ✅ API 테스트 기능: 매매/전월세 API 테스트
- ❌ 설정 메뉴: 별도 설정 페이지 미구현 (API는 존재)
- ❌ 통합 설정 UI: 데이터베이스/캐시 초기화 UI 메뉴 미구현

#### 향후 신규 구현 사항


## 서비스 명세
 - REST (GET) , XML , Service Key, 암호화 없음 , Request-Response
 - 매매 실거래가 URL : http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev
 - 전우러세 실거래가 URL :  http://apis.data.go.kr/1613000/RTMSDataSvcAptRent

 - 요청메시지 명세
  serviceKey : 인증키. 필수.  .env 파일의 MOLIT_API_KEY 로 지정되어 있음.
  pageNo : 페이지번호. 옵션
  numOfRows : 한페이지 결과 수. 옵션
  LAWD_CD : 법정동 코드 10자리중 앞 5자리 지역코드. 필수. dong_code_active.txt 참고
  DEAL_YMD : 계약월. 필수. 실거래 계약년월 6자리
 - 아래 예제 참고

 - 예제
 https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev?serviceKey=서비스키&LAWD_CD=11110&DEAL_YMD=202407&pageNo=1&numOfRows=1

https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev?serviceKey=9e41238294802e6f98d37167c486623574e6d91c0d48708e9eed5ea497aea64c&LAWD_CD=11110&DEAL_YMD=201512&pageNo=1&numOfRows=100

<response>
<header>
<resultCode>000</resultCode>
<resultMsg>OK</resultMsg>
</header>
<body>
<items>
<item>
<aptDong> </aptDong>
<aptNm>인왕산2차아이파크</aptNm>
<aptSeq>11110-2417</aptSeq>
<bonbun>0088</bonbun>
<bubun>0000</bubun>
<buildYear>2015</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>63,400</dealAmount>
<dealDay>22</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.0284</excluUseAr>
<floor>10</floor>
<jibun>88</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>통일로18길</roadNm>
<roadNmBonbun>00034</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100482</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>18700</umdCd>
<umdNm>무악동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>렉스빌</aptNm>
<aptSeq>11110-973</aptSeq>
<bonbun>0019</bonbun>
<bubun>0000</bubun>
<buildYear>2006</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>57,000</dealAmount>
<dealDay>29</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>106.98</excluUseAr>
<floor>3</floor>
<jibun>19</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>혜화로3가길</roadNm>
<roadNmBonbun>00030</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100544</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17000</umdCd>
<umdNm>명륜1가</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>동아</aptNm>
<aptSeq>11110-51</aptSeq>
<bonbun>0101</bonbun>
<bubun>0000</bubun>
<buildYear>1995</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>44,600</dealAmount>
<dealDay>7</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.28</excluUseAr>
<floor>10</floor>
<jibun>101</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>송월길</roadNm>
<roadNmBonbun>00147</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100192</roadNmCd>
<roadNmSeq>05</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>18000</umdCd>
<umdNm>교북동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>경희궁파크팰리스</aptNm>
<aptSeq>11110-107</aptSeq>
<bonbun>0095</bonbun>
<bubun>0000</bubun>
<buildYear>2003</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>120,000</dealAmount>
<dealDay>24</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>146.33</excluUseAr>
<floor>4</floor>
<jibun>95</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>사직로8길</roadNm>
<roadNmBonbun>00020</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100135</roadNmCd>
<roadNmSeq>05</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>11800</umdCd>
<umdNm>내수동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>두산</aptNm>
<aptSeq>11110-34</aptSeq>
<bonbun>0232</bonbun>
<bubun>0000</bubun>
<buildYear>1999</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>50,000</dealAmount>
<dealDay>24</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.9</excluUseAr>
<floor>4</floor>
<jibun>232</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>지봉로5길</roadNm>
<roadNmBonbun>00007</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100390</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>광화문스페이스본(101동~105동)</aptNm>
<aptSeq>11110-2203</aptSeq>
<bonbun>0009</bonbun>
<bubun>0000</bubun>
<buildYear>2008</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>82,500</dealAmount>
<dealDay>10</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>94.51</excluUseAr>
<floor>11</floor>
<jibun>9</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>사직로8길</roadNm>
<roadNmBonbun>00004</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100135</roadNmCd>
<roadNmSeq>03</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>11500</umdCd>
<umdNm>사직동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>익성씨티하임</aptNm>
<aptSeq>11110-2348</aptSeq>
<bonbun>1392</bonbun>
<bubun>0000</bubun>
<buildYear>2013</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>10,500</dealAmount>
<dealDay>15</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>15.76</excluUseAr>
<floor>13</floor>
<jibun>1392</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>난계로29가길</roadNm>
<roadNmBonbun>00017</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100029</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>종로센트레빌</aptNm>
<aptSeq>11110-2224</aptSeq>
<bonbun>0002</bonbun>
<bubun>0001</bubun>
<buildYear>2008</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>52,300</dealAmount>
<dealDay>26</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.92</excluUseAr>
<floor>12</floor>
<jibun>2-1</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>동망산길</roadNm>
<roadNmBonbun>00047</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100065</roadNmCd>
<roadNmSeq>02</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>창신쌍용1</aptNm>
<aptSeq>11110-37</aptSeq>
<bonbun>0702</bonbun>
<bubun>0000</bubun>
<buildYear>1992</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>37,300</dealAmount>
<dealDay>23</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>79.87</excluUseAr>
<floor>9</floor>
<jibun>702</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>동망산길</roadNm>
<roadNmBonbun>00019</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100065</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>창신쌍용1</aptNm>
<aptSeq>11110-37</aptSeq>
<bonbun>0702</bonbun>
<bubun>0000</bubun>
<buildYear>1992</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>42,800</dealAmount>
<dealDay>22</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>106.62</excluUseAr>
<floor>12</floor>
<jibun>702</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>동망산길</roadNm>
<roadNmBonbun>00019</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100065</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>두산</aptNm>
<aptSeq>11110-34</aptSeq>
<bonbun>0232</bonbun>
<bubun>0000</bubun>
<buildYear>1999</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>39,000</dealAmount>
<dealDay>10</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>59.95</excluUseAr>
<floor>14</floor>
<jibun>232</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>지봉로5길</roadNm>
<roadNmBonbun>00007</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100390</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>종로센트레빌</aptNm>
<aptSeq>11110-2224</aptSeq>
<bonbun>0002</bonbun>
<bubun>0001</bubun>
<buildYear>2008</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>42,500</dealAmount>
<dealDay>19</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>59.92</excluUseAr>
<floor>12</floor>
<jibun>2-1</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>동망산길</roadNm>
<roadNmBonbun>00047</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100065</roadNmCd>
<roadNmSeq>02</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>현대</aptNm>
<aptSeq>11110-90</aptSeq>
<bonbun>0082</bonbun>
<bubun>0000</bubun>
<buildYear>2000</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>39,490</dealAmount>
<dealDay>12</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>60</excluUseAr>
<floor>15</floor>
<jibun>82</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>통일로</roadNm>
<roadNmBonbun>00246</roadNmBonbun>
<roadNmBubun>00020</roadNmBubun>
<roadNmCd>3000008</roadNmCd>
<roadNmSeq>06</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>18700</umdCd>
<umdNm>무악동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>경희궁의아침2단지</aptNm>
<aptSeq>11110-115</aptSeq>
<bonbun>0071</bonbun>
<bubun>0000</bubun>
<buildYear>2004</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>105,000</dealAmount>
<dealDay>14</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>124.17</excluUseAr>
<floor>8</floor>
<jibun>71</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>사직로8길</roadNm>
<roadNmBonbun>00024</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100135</roadNmCd>
<roadNmSeq>05</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>11800</umdCd>
<umdNm>내수동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>아남1</aptNm>
<aptSeq>11110-25</aptSeq>
<bonbun>0004</bonbun>
<bubun>0000</bubun>
<buildYear>1995</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>49,800</dealAmount>
<dealDay>19</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.8</excluUseAr>
<floor>1</floor>
<jibun>4</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>창경궁로</roadNm>
<roadNmBonbun>00265</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>3005008</roadNmCd>
<roadNmSeq>07</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17100</umdCd>
<umdNm>명륜2가</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>이화에수풀</aptNm>
<aptSeq>11110-2359</aptSeq>
<bonbun>0195</bonbun>
<bubun>0010</bubun>
<buildYear>2014</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>17,000</dealAmount>
<dealDay>17</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>16.98</excluUseAr>
<floor>8</floor>
<jibun>195-10</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>대학로</roadNm>
<roadNmBonbun>00047</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>3100002</roadNmCd>
<roadNmSeq>05</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>16600</umdCd>
<umdNm>연건동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>이화에수풀</aptNm>
<aptSeq>11110-2359</aptSeq>
<bonbun>0195</bonbun>
<bubun>0010</bubun>
<buildYear>2014</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>17,000</dealAmount>
<dealDay>18</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>16.98</excluUseAr>
<floor>4</floor>
<jibun>195-10</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>대학로</roadNm>
<roadNmBonbun>00047</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>3100002</roadNmCd>
<roadNmSeq>05</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>16600</umdCd>
<umdNm>연건동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>삼성</aptNm>
<aptSeq>11110-73</aptSeq>
<bonbun>0596</bonbun>
<bubun>0000</bubun>
<buildYear>1998</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>31,500</dealAmount>
<dealDay>6</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>59.97</excluUseAr>
<floor>9</floor>
<jibun>596</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>평창문화로</roadNm>
<roadNmBonbun>00172</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>3100023</roadNmCd>
<roadNmSeq>00</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd> </roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>18300</umdCd>
<umdNm>평창동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>종로유케이201</aptNm>
<aptSeq>11110-2334</aptSeq>
<bonbun>0201</bonbun>
<bubun>0011</bubun>
<buildYear>2013</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>10,800</dealAmount>
<dealDay>31</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>12.01</excluUseAr>
<floor>7</floor>
<jibun>201-11</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>난계로29길</roadNm>
<roadNmBonbun>00033</roadNmBonbun>
<roadNmBubun>00004</roadNmBubun>
<roadNmCd>4100030</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>종로청계힐스테이트</aptNm>
<aptSeq>11110-2234</aptSeq>
<bonbun>0766</bonbun>
<bubun>0000</bubun>
<buildYear>2009</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>44,900</dealAmount>
<dealDay>14</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>59.9426</excluUseAr>
<floor>12</floor>
<jibun>766</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>숭인동길</roadNm>
<roadNmBonbun>00021</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100204</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>종로센트레빌</aptNm>
<aptSeq>11110-2224</aptSeq>
<bonbun>0002</bonbun>
<bubun>0001</bubun>
<buildYear>2008</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>53,300</dealAmount>
<dealDay>5</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.92</excluUseAr>
<floor>10</floor>
<jibun>2-1</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>동망산길</roadNm>
<roadNmBonbun>00047</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100065</roadNmCd>
<roadNmSeq>02</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>창신쌍용1</aptNm>
<aptSeq>11110-37</aptSeq>
<bonbun>0702</bonbun>
<bubun>0000</bubun>
<buildYear>1992</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>34,500</dealAmount>
<dealDay>12</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>79.87</excluUseAr>
<floor>5</floor>
<jibun>702</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>동망산길</roadNm>
<roadNmBonbun>00019</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100065</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>인왕산아이파크</aptNm>
<aptSeq>11110-2212</aptSeq>
<bonbun>0060</bonbun>
<bubun>0000</bubun>
<buildYear>2008</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>61,000</dealAmount>
<dealDay>25</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.858</excluUseAr>
<floor>13</floor>
<jibun>60</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>통일로18길</roadNm>
<roadNmBonbun>00009</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100482</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>18700</umdCd>
<umdNm>무악동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>벽산블루밍평창힐스</aptNm>
<aptSeq>11110-146</aptSeq>
<bonbun>0045</bonbun>
<bubun>0000</bubun>
<buildYear>2004</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>115,000</dealAmount>
<dealDay>2</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>210.53</excluUseAr>
<floor>2</floor>
<jibun>45</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>평창문화로</roadNm>
<roadNmBonbun>00118</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>3100023</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>18300</umdCd>
<umdNm>평창동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>창신쌍용2</aptNm>
<aptSeq>11110-91</aptSeq>
<bonbun>0703</bonbun>
<bubun>0000</bubun>
<buildYear>1993</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>39,950</dealAmount>
<dealDay>11</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>115.53</excluUseAr>
<floor>2</floor>
<jibun>703</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>낙산길</roadNm>
<roadNmBonbun>00198</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100020</roadNmCd>
<roadNmSeq>02</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>명륜동주상복합아남아파트</aptNm>
<aptSeq>11110-26</aptSeq>
<bonbun>0237</bonbun>
<bubun>0000</bubun>
<buildYear>1999</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>41,000</dealAmount>
<dealDay>19</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>61.13</excluUseAr>
<floor>7</floor>
<jibun>237</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>혜화로3길</roadNm>
<roadNmBonbun>00005</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100545</roadNmCd>
<roadNmSeq>02</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17100</umdCd>
<umdNm>명륜2가</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>인왕산아이파크</aptNm>
<aptSeq>11110-2212</aptSeq>
<bonbun>0060</bonbun>
<bubun>0000</bubun>
<buildYear>2008</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>62,000</dealAmount>
<dealDay>16</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.858</excluUseAr>
<floor>5</floor>
<jibun>60</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>통일로18길</roadNm>
<roadNmBonbun>00009</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100482</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>18700</umdCd>
<umdNm>무악동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>종로청계힐스테이트</aptNm>
<aptSeq>11110-2234</aptSeq>
<bonbun>0766</bonbun>
<bubun>0000</bubun>
<buildYear>2009</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>52,500</dealAmount>
<dealDay>31</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.9478</excluUseAr>
<floor>11</floor>
<jibun>766</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>숭인동길</roadNm>
<roadNmBonbun>00021</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100204</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>현대</aptNm>
<aptSeq>11110-90</aptSeq>
<bonbun>0082</bonbun>
<bubun>0000</bubun>
<buildYear>2000</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>63,490</dealAmount>
<dealDay>15</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>114.9</excluUseAr>
<floor>6</floor>
<jibun>82</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>통일로</roadNm>
<roadNmBonbun>00246</roadNmBonbun>
<roadNmBubun>00020</roadNmBubun>
<roadNmCd>3000008</roadNmCd>
<roadNmSeq>06</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>18700</umdCd>
<umdNm>무악동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>롯데미도파광화문빌딩</aptNm>
<aptSeq>11110-12</aptSeq>
<bonbun>0145</bonbun>
<bubun>0000</bubun>
<buildYear>1981</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>60,000</dealAmount>
<dealDay>22</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>149.95</excluUseAr>
<floor>8</floor>
<jibun>145</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>세종대로23길</roadNm>
<roadNmBonbun>00047</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100190</roadNmCd>
<roadNmSeq>02</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>11700</umdCd>
<umdNm>당주동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>익성씨티하임</aptNm>
<aptSeq>11110-2348</aptSeq>
<bonbun>1392</bonbun>
<bubun>0000</bubun>
<buildYear>2013</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>10,000</dealAmount>
<dealDay>15</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>14.48</excluUseAr>
<floor>14</floor>
<jibun>1392</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>난계로29가길</roadNm>
<roadNmBonbun>00017</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100029</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>동대문</aptNm>
<aptSeq>11110-30</aptSeq>
<bonbun>0328</bonbun>
<bubun>0017</bubun>
<buildYear>1966</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>20,800</dealAmount>
<dealDay>7</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>28.8</excluUseAr>
<floor>3</floor>
<jibun>328-17</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>지봉로</roadNm>
<roadNmBonbun>00025</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>3005007</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>종로아인스빌</aptNm>
<aptSeq>11110-2344</aptSeq>
<bonbun>1392</bonbun>
<bubun>0001</bubun>
<buildYear>2013</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>12,300</dealAmount>
<dealDay>2</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>12.15</excluUseAr>
<floor>10</floor>
<jibun>1392-1</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>난계로29가길</roadNm>
<roadNmBonbun>00019</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100029</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>동대문</aptNm>
<aptSeq>11110-30</aptSeq>
<bonbun>0328</bonbun>
<bubun>0017</bubun>
<buildYear>1966</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>19,500</dealAmount>
<dealDay>3</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>28.8</excluUseAr>
<floor>6</floor>
<jibun>328-17</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>지봉로</roadNm>
<roadNmBonbun>00025</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>3005007</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>종로센트레빌</aptNm>
<aptSeq>11110-2224</aptSeq>
<bonbun>0002</bonbun>
<bubun>0001</bubun>
<buildYear>2008</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>39,700</dealAmount>
<dealDay>22</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>59.92</excluUseAr>
<floor>1</floor>
<jibun>2-1</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>동망산길</roadNm>
<roadNmBonbun>00047</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100065</roadNmCd>
<roadNmSeq>02</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>창신쌍용2</aptNm>
<aptSeq>11110-91</aptSeq>
<bonbun>0703</bonbun>
<bubun>0000</bubun>
<buildYear>1993</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>27,200</dealAmount>
<dealDay>7</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>64.66</excluUseAr>
<floor>3</floor>
<jibun>703</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>낙산길</roadNm>
<roadNmBonbun>00198</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100020</roadNmCd>
<roadNmSeq>02</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>창신쌍용1</aptNm>
<aptSeq>11110-37</aptSeq>
<bonbun>0702</bonbun>
<bubun>0000</bubun>
<buildYear>1992</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>37,000</dealAmount>
<dealDay>14</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>79.87</excluUseAr>
<floor>3</floor>
<jibun>702</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>동망산길</roadNm>
<roadNmBonbun>00019</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100065</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>아남1</aptNm>
<aptSeq>11110-25</aptSeq>
<bonbun>0004</bonbun>
<bubun>0000</bubun>
<buildYear>1995</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>52,000</dealAmount>
<dealDay>10</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.9</excluUseAr>
<floor>12</floor>
<jibun>4</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>창경궁로</roadNm>
<roadNmBonbun>00265</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>3005008</roadNmCd>
<roadNmSeq>07</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17100</umdCd>
<umdNm>명륜2가</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>숭인한양LEEPS</aptNm>
<aptSeq>11110-2366</aptSeq>
<bonbun>1421</bonbun>
<bubun>0002</bubun>
<buildYear>2014</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>11,900</dealAmount>
<dealDay>14</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>12.78</excluUseAr>
<floor>11</floor>
<jibun>1421-2</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>난계로29가길</roadNm>
<roadNmBonbun>00020</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100029</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>삼전솔하임4차</aptNm>
<aptSeq>11110-2368</aptSeq>
<bonbun>0318</bonbun>
<bubun>0002</bubun>
<buildYear>2014</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>13,000</dealAmount>
<dealDay>8</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>15.09</excluUseAr>
<floor>15</floor>
<jibun>318-2</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>지봉로4길</roadNm>
<roadNmBonbun>00013</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100389</roadNmCd>
<roadNmSeq>00</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>킹스매너</aptNm>
<aptSeq>11110-118</aptSeq>
<bonbun>0110</bonbun>
<bubun>0015</bubun>
<buildYear>2004</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>130,000</dealAmount>
<dealDay>8</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>194.43</excluUseAr>
<floor>6</floor>
<jibun>110-15</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>경희궁2길</roadNm>
<roadNmBonbun>00005</roadNmBonbun>
<roadNmBubun>00005</roadNmBubun>
<roadNmCd>4100005</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>11800</umdCd>
<umdNm>내수동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>창신이수</aptNm>
<aptSeq>11110-42</aptSeq>
<bonbun>0023</bonbun>
<bubun>0816</bubun>
<buildYear>2003</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>39,900</dealAmount>
<dealDay>3</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>68.06</excluUseAr>
<floor>8</floor>
<jibun>23-816</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>지봉로</roadNm>
<roadNmBonbun>00087</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>3005007</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>동문(비동,씨동)(494-0)</aptNm>
<aptSeq>11110-45</aptSeq>
<bonbun>0494</bonbun>
<bubun>0000</bubun>
<buildYear>1997</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>27,000</dealAmount>
<dealDay>9</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>59.94</excluUseAr>
<floor>3</floor>
<jibun>494</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>숭인동2길</roadNm>
<roadNmBonbun>00014</roadNmBonbun>
<roadNmBubun>00005</roadNmBubun>
<roadNmCd>4100203</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>아남1</aptNm>
<aptSeq>11110-25</aptSeq>
<bonbun>0004</bonbun>
<bubun>0000</bubun>
<buildYear>1995</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>44,000</dealAmount>
<dealDay>1</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.8</excluUseAr>
<floor>18</floor>
<jibun>4</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>창경궁로</roadNm>
<roadNmBonbun>00265</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>3005008</roadNmCd>
<roadNmSeq>07</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17100</umdCd>
<umdNm>명륜2가</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>숭인한양LEEPS</aptNm>
<aptSeq>11110-2366</aptSeq>
<bonbun>1421</bonbun>
<bubun>0002</bubun>
<buildYear>2014</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>11,500</dealAmount>
<dealDay>8</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>12.78</excluUseAr>
<floor>10</floor>
<jibun>1421-2</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>난계로29가길</roadNm>
<roadNmBonbun>00020</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100029</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>종로청계힐스테이트</aptNm>
<aptSeq>11110-2234</aptSeq>
<bonbun>0766</bonbun>
<bubun>0000</bubun>
<buildYear>2009</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>42,500</dealAmount>
<dealDay>5</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>59.9426</excluUseAr>
<floor>2</floor>
<jibun>766</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>숭인동길</roadNm>
<roadNmBonbun>00021</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100204</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>종로청계힐스테이트</aptNm>
<aptSeq>11110-2234</aptSeq>
<bonbun>0766</bonbun>
<bubun>0000</bubun>
<buildYear>2009</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>52,000</dealAmount>
<dealDay>3</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>84.9478</excluUseAr>
<floor>19</floor>
<jibun>766</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>숭인동길</roadNm>
<roadNmBonbun>00021</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100204</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17500</umdCd>
<umdNm>숭인동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>두산</aptNm>
<aptSeq>11110-34</aptSeq>
<bonbun>0232</bonbun>
<bubun>0000</bubun>
<buildYear>1999</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>41,000</dealAmount>
<dealDay>2</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>59.95</excluUseAr>
<floor>9</floor>
<jibun>232</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>지봉로5길</roadNm>
<roadNmBonbun>00007</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>4100390</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>17400</umdCd>
<umdNm>창신동</umdNm>
</item>
<item>
<aptDong> </aptDong>
<aptNm>롯데캐슬로잔</aptNm>
<aptSeq>11110-2246</aptSeq>
<bonbun>0108</bonbun>
<bubun>0000</bubun>
<buildYear>2009</buildYear>
<buyerGbn> </buyerGbn>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>164,500</dealAmount>
<dealDay>3</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<dealingGbn> </dealingGbn>
<estateAgentSggNm> </estateAgentSggNm>
<excluUseAr>219.775</excluUseAr>
<floor>3</floor>
<jibun>108</jibun>
<landCd>1</landCd>
<landLeaseholdGbn>N</landLeaseholdGbn>
<rgstDate> </rgstDate>
<roadNm>평창문화로</roadNm>
<roadNmBonbun>00156</roadNmBonbun>
<roadNmBubun>00000</roadNmBubun>
<roadNmCd>3100023</roadNmCd>
<roadNmSeq>01</roadNmSeq>
<roadNmSggCd>11110</roadNmSggCd>
<roadNmbCd>0</roadNmbCd>
<sggCd>11110</sggCd>
<slerGbn> </slerGbn>
<umdCd>18300</umdCd>
<umdNm>평창동</umdNm>
</item>
</items>
<numOfRows>100</numOfRows>
<pageNo>1</pageNo>
<totalCount>49</totalCount>
</body>
</response>

https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent?serviceKey=9e41238294802e6f98d37167c486623574e6d91c0d48708e9eed5ea497aea64c&LAWD_CD=11110&DEAL_YMD=201512

 <response>
<header>
<resultCode>000</resultCode>
<resultMsg>OK</resultMsg>
</header>
<body>
<items>
<item>
<aptNm>송림아마레스아파트</aptNm>
<buildYear>2003</buildYear>
<contractTerm> </contractTerm>
<contractType> </contractType>
<dealDay>15</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<deposit>33,000</deposit>
<excluUseAr>75.62</excluUseAr>
<floor>5</floor>
<jibun>2-12</jibun>
<monthlyRent>0</monthlyRent>
<preDeposit> </preDeposit>
<preMonthlyRent> </preMonthlyRent>
<sggCd>11110</sggCd>
<umdNm>명륜1가</umdNm>
<useRRRight> </useRRRight>
</item>
<item>
<aptNm>삼성</aptNm>
<buildYear>1998</buildYear>
<contractTerm> </contractTerm>
<contractType> </contractType>
<dealDay>22</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<deposit>22,000</deposit>
<excluUseAr>59.97</excluUseAr>
<floor>7</floor>
<jibun>596</jibun>
<monthlyRent>0</monthlyRent>
<preDeposit> </preDeposit>
<preMonthlyRent> </preMonthlyRent>
<sggCd>11110</sggCd>
<umdNm>평창동</umdNm>
<useRRRight> </useRRRight>
</item>
<item>
<aptNm>창신쌍용2</aptNm>
<buildYear>1993</buildYear>
<contractTerm> </contractTerm>
<contractType> </contractType>
<dealDay>5</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<deposit>17,000</deposit>
<excluUseAr>64.66</excluUseAr>
<floor>4</floor>
<jibun>703</jibun>
<monthlyRent>40</monthlyRent>
<preDeposit> </preDeposit>
<preMonthlyRent> </preMonthlyRent>
<sggCd>11110</sggCd>
<umdNm>창신동</umdNm>
<useRRRight> </useRRRight>
</item>
<item>
<aptNm>경희궁의아침3단지</aptNm>
<buildYear>2004</buildYear>
<contractTerm> </contractTerm>
<contractType> </contractType>
<dealDay>28</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<deposit>77,000</deposit>
<excluUseAr>149</excluUseAr>
<floor>4</floor>
<jibun>72</jibun>
<monthlyRent>0</monthlyRent>
<preDeposit> </preDeposit>
<preMonthlyRent> </preMonthlyRent>
<sggCd>11110</sggCd>
<umdNm>내수동</umdNm>
<useRRRight> </useRRRight>
</item>
<item>
<aptNm>아남2</aptNm>
<buildYear>1996</buildYear>
<contractTerm> </contractTerm>
<contractType> </contractType>
<dealDay>18</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<deposit>17,000</deposit>
<excluUseAr>59.4</excluUseAr>
<floor>4</floor>
<jibun>236</jibun>
<monthlyRent>60</monthlyRent>
<preDeposit> </preDeposit>
<preMonthlyRent> </preMonthlyRent>
<sggCd>11110</sggCd>
<umdNm>명륜2가</umdNm>
<useRRRight> </useRRRight>
</item>
<item>
<aptNm>종로청계힐스테이트</aptNm>
<buildYear>2009</buildYear>
<contractTerm> </contractTerm>
<contractType> </contractType>
<dealDay>16</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<deposit>35,000</deposit>
<excluUseAr>59.9426</excluUseAr>
<floor>3</floor>
<jibun>766</jibun>
<monthlyRent>0</monthlyRent>
<preDeposit> </preDeposit>
<preMonthlyRent> </preMonthlyRent>
<sggCd>11110</sggCd>
<umdNm>숭인동</umdNm>
<useRRRight> </useRRRight>
</item>
<item>
<aptNm>현대뜨레비앙</aptNm>
<buildYear>2003</buildYear>
<contractTerm> </contractTerm>
<contractType> </contractType>
<dealDay>9</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<deposit>18,000</deposit>
<excluUseAr>45.5</excluUseAr>
<floor>3</floor>
<jibun>55</jibun>
<monthlyRent>0</monthlyRent>
<preDeposit> </preDeposit>
<preMonthlyRent> </preMonthlyRent>
<sggCd>11110</sggCd>
<umdNm>익선동</umdNm>
<useRRRight> </useRRRight>
</item>
<item>
<aptNm>아남1</aptNm>
<buildYear>1995</buildYear>
<contractTerm> </contractTerm>
<contractType> </contractType>
<dealDay>29</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<deposit>8,100</deposit>
<excluUseAr>84.9</excluUseAr>
<floor>2</floor>
<jibun>4</jibun>
<monthlyRent>0</monthlyRent>
<preDeposit> </preDeposit>
<preMonthlyRent> </preMonthlyRent>
<sggCd>11110</sggCd>
<umdNm>명륜2가</umdNm>
<useRRRight> </useRRRight>
</item>
<item>
<aptNm>창신쌍용2</aptNm>
<buildYear>1993</buildYear>
<contractTerm> </contractTerm>
<contractType> </contractType>
<dealDay>23</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<deposit>21,000</deposit>
<excluUseAr>79.87</excluUseAr>
<floor>8</floor>
<jibun>703</jibun>
<monthlyRent>20</monthlyRent>
<preDeposit> </preDeposit>
<preMonthlyRent> </preMonthlyRent>
<sggCd>11110</sggCd>
<umdNm>창신동</umdNm>
<useRRRight> </useRRRight>
</item>
<item>
<aptNm>광화문스페이스본(101동~105동)</aptNm>
<buildYear>2008</buildYear>
<contractTerm> </contractTerm>
<contractType> </contractType>
<dealDay>21</dealDay>
<dealMonth>12</dealMonth>
<dealYear>2015</dealYear>
<deposit>53,000</deposit>
<excluUseAr>126.34</excluUseAr>
<floor>4</floor>
<jibun>9</jibun>
<monthlyRent>80</monthlyRent>
<preDeposit> </preDeposit>
<preMonthlyRent> </preMonthlyRent>
<sggCd>11110</sggCd>
<umdNm>사직동</umdNm>
<useRRRight> </useRRRight>
</item>
</items>
<numOfRows>10</numOfRows>
<pageNo>1</pageNo>
<totalCount>95</totalCount>
</body>
</response>
