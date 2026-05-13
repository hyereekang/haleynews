# 🚀 EduTech News & Job Aggregator

에듀테크 분야의 최신 뉴스, 전문 IT 아티클, 글로벌 커뮤니티 트렌드, 그리고 기업 투자 정보를 한곳에서 모아볼 수 있는 통합 대시보드입니다.

## ✨ 탭별 주요 기능 및 출처

본 서비스는 각 분야의 신뢰도 높은 소스들로부터 데이터를 실시간으로 수집합니다.

### 1. 🌍 주요 뉴스
- **설명**: 국내외 주요 일간지 및 포털의 종합 뉴스 브리핑
- **출처**: 구글 뉴스 RSS (실시간)

### 2. 💻 IT/테크 (전문 큐레이션)
- **설명**: IT 현직자들이 가장 선호하는 전문 채널 및 글로벌 커뮤니티 트렌드
- **IT 전문 아티클 출처**: 
  - [요즘IT](https://yozm.wishket.com/magazine/list/all/) (실무 인사이트)
  - [서핏(Surfit)](https://www.surfit.io/) (디자인/테크 큐레이션)
  - [커리어리](https://careerly.co.kr/) (현직자 소셜 뉴스)
  - [GeekNews(긱뉴스)](https://news.hada.io/) (실시간 기술 속보)
- **글로벌 트렌드 출처**: 
  - [Reddit](https://www.reddit.com/) (r/EdTech, r/UXDesign, r/OpenAI 커뮤니티의 **댓글 많은 순 TOP 10**)

### 3. 🎨 취업 (디자인/재택)
- **설명**: '재택 디자인' 키워드 중심의 실시간 채용 공고
- **출처**: [사람인](https://www.saramin.co.kr/), [잡코리아](https://www.jobkorea.co.kr/), [서핏](https://jobs.surfit.io/)

### 4. 🎪 행사/박람회
- **설명**: 디자인, IT, 교육 관련 최신 컨퍼런스 및 전시 일정
- **출처**: 구글 뉴스 검색 엔진 (최근 30일 데이터)

### 5. 🏢 회사 / 투자
- **설명**: 상장 IT 기업의 가치 분석 및 유망 스타트업 투자 동향
- **출처**: 
  - [KRX (한국거래소)](https://kind.krx.co.kr/) Value-up 데이터
  - [The VC](https://thevc.kr/) (한국 스타트업 투자 데이터베이스)

---

## 🛠 기술 스택

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Scraping**: BeautifulSoup4, Requests, Reddit JSON API
- **Data Processing**: Pandas
- **Language**: Python 3.9+

## 🚀 시작하기

1. **필요 라이브러리 설치**
   ```bash
   pip install -r requirements.txt
   ```

2. **앱 실행**
   ```bash
   streamlit run app.py
   ```

## 🔄 데이터 새로고침 안내
사이드바의 **[🔄 전체 새로고침]** 버튼을 누르면 내부 캐시가 초기화되며, 위 명시된 모든 사이트로부터 **가장 최신 뉴스**를 다시 크롤링해 옵니다.

---
© 2026 Edu-Job Bot Project (hyereekang)
