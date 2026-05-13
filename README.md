# 🚀 EduTech News & Job Aggregator

에듀테크 분야의 최신 뉴스, IT 트렌드, 그리고 디자인/재택 관련 채용 정보를 한곳에서 모아볼 수 있는 통합 대시보드입니다.

## ✨ 주요 기능

-   **🌍 주요 뉴스**: 구글 뉴스 RSS를 활용한 오늘의 실시간 글로벌/종합 주요 뉴스 수집
-   **💻 IT/테크**: 최신 IT 기술 트렌드 및 에듀테크 관련 기술 소식 업데이트
-   **🎨 채용 정보**: 사람인, 잡코리아, 서핏 등 주요 채용 플랫폼에서 '디자인', '재택' 관련 공고 실시간 스크래핑
-   **🎪 행사/박람회**: 업계 관련 전시회, 박람회, 세미나 일정 정보 제공
-   **📚 에듀테크**: 교육 혁신 및 에듀테크 전문 소식 큐레이션

## 🛠 기술 스택

-   **Frontend**: [Streamlit](https://streamlit.io/) (Python 기반 웹 프레임워크)
-   **Scraping**: BeautifulSoup4, Requests
-   **Data Processing**: Pandas
-   **Language**: Python 3.9+

## 🚀 시작하기

1.  **필요 라이브러리 설치**
    ```bash
    pip install -r requirements.txt
    ```

2.  **앱 실행**
    ```bash
    streamlit run app.py
    ```

## ⚠️ 참고 사항 (현재 이슈)

현재 일부 채용 플랫폼(잡코리아, 서핏)의 구조 변경 및 동적 로딩 방식으로 인해 데이터 수집이 원활하지 않을 수 있습니다.

1.  **사람인**: 정상 작동 중
2.  **잡코리아**: 웹사이트 개편으로 인한 셀렉터 업데이트 필요
3.  **서핏**: SPA(Single Page Application) 구조로 전환되어 정적 크롤링(BeautifulSoup)으로는 한계가 있음 (향후 Selenium 등 도입 검토 중)

---
© 2026 Edu-Job Bot Project
