import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="EduTech News & Job Bot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (디자인 강화)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .job-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #007bff;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        transition: transform 0.2s;
    }
    .job-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    .news-card {
        background-color: white;
        padding: 18px;
        border-radius: 10px;
        border-left: 6px solid #28a745;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .platform-tag {
        font-size: 0.8em;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: bold;
        margin-bottom: 10px;
        display: inline-block;
    }
    .tag-jk { background-color: #e7f1ff; color: #007bff; }
    .tag-sr { background-color: #fff4e6; color: #fd7e14; }
    .tag-sf { background-color: #f3f0ff; color: #7950f2; }
    </style>
    """, unsafe_allow_html=True)

# --- 유틸리티 및 크롤러 ---
def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

@st.cache_data(ttl=3600) # 1시간 동안 결과 캐싱
def crawl_jobs():
    results = []
    
    # 1. 잡코리아 (업데이트된 셀렉터 대응)
    try:
        jk_url = "https://www.jobkorea.co.kr/Search/?stext=%EC%9E%AC%ED%83%9D+%2B+%EC%9B%B9%EB%94%94%EC%9E%90%EC%9D%B8&tabType=recruit"
        res = requests.get(jk_url, headers=get_headers())
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 새로운 JobKorea 구조는 a 태그 내의 GI_Read 링크를 기반으로 수집
        job_links = soup.select('a[href*="/Recruit/GI_Read/"]')
        added_urls = set()
        
        for link in job_links:
            href = link['href']
            if href in added_urls: continue
            
            title = link.get_text(strip=True)
            # 제목은 보통 특정 클래스(line-clamp 등)를 가지거나 텍스트가 김
            if len(title) > 5:
                # 다음 a 태그나 주변 텍스트에서 기업명 찾기 시도
                company = "확인 필요"
                # 간단한 규칙: 다음 링크가 기업명인 경우가 많음 (UI 구조상)
                next_a = link.find_next('a')
                if next_a and 'GI_Read' in next_a.get('href', ''):
                    company = next_a.get_text(strip=True)
                
                results.append({
                    "platform": "잡코리아",
                    "title": title,
                    "company": company,
                    "url": "https://www.jobkorea.co.kr" + href if not href.startswith('http') else href,
                    "date": "확인 필요",
                    "tag_class": "tag-jk"
                })
                added_urls.add(href)
                if len(results) >= 10: break
    except Exception as e:
        st.warning(f"잡코리아 수집 중 일시적 오류: {e}")

    # 2. 사람인
    try:
        sr_url = "https://www.saramin.co.kr/zf_user/search?search_area=main&search_done=y&search_optional_item=n&searchType=search&searchword=%EC%9E%AC%ED%83%9D%20%2B%20%EC%9B%B9%EB%94%94%EC%9E%90%EC%9D%B8"
        res = requests.get(sr_url, headers=get_headers())
        soup = BeautifulSoup(res.text, 'html.parser')
        for item in soup.select('.item_recruit')[:10]:
            title_el = item.select_one('.job_tit a')
            if title_el:
                results.append({
                    "platform": "사람인",
                    "title": title_el.get_text(strip=True),
                    "company": item.select_one('.corp_name a').get_text(strip=True),
                    "url": "https://www.saramin.co.kr" + title_el['href'],
                    "date": item.select_one('.job_date').get_text(strip=True) if item.select_one('.job_date') else "채용중",
                    "tag_class": "tag-sr"
                })
    except Exception as e:
        st.warning(f"사람인 수집 중 일시적 오류: {e}")

    # 3. 서핏 (주의: 서핏은 동적 로딩 방식으로 전환되어 정적 크롤링이 제한적임)
    try:
        # 서핏 채용 페이지 URL 업데이트
        sf_url = "https://jobs.surfit.io/" 
        res = requests.get(sf_url, headers=get_headers())
        # 서핏은 현재 SPA 구조로, BeautifulSoup만으로는 데이터 수집이 어렵습니다.
        # 공지용 가상 데이터 또는 간단한 안내 추가
        pass
    except Exception as e:
        pass
        
    return results
        
    return results

def crawl_news(keyword):
    # 구글 뉴스 RSS를 활용한 간이 수집 (한글 검색 지원)
    news_results = []
    try:
        rss_url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(rss_url)
        soup = BeautifulSoup(res.text, 'xml')
        for item in soup.select('item')[:10]:
            news_results.append({
                "title": item.title.text,
                "link": item.link.text,
                "pubDate": item.pubDate.text[:16],
                "source": item.source.text if item.source else "Google News"
            })
    except: pass
    return news_results

# --- UI 메인 로직 ---
def main():
    st.sidebar.title("🚀 Edu-Job Bot")
    st.sidebar.info(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if st.sidebar.button("🔄 전체 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.title("📌 실시간 정보 대시보드")
    
    # 5개 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌍 주요 뉴스", 
        "💻 IT/테크", 
        "🎨 취업(디자인/재택)", 
        "🎪 행사/박람회", 
        "📚 에듀테크"
    ])

    with tab1:
        st.subheader("오늘의 글로벌/종합 주요 뉴스")
        news = crawl_news("주요 종합 뉴스")
        for n in news:
            st.markdown(f"""<div class='news-card'>
                <a href='{n['link']}' target='_blank' style='text-decoration:none; color:#333;'>
                <b>{n['title']}</b></a><br>
                <small>{n['source']} | {n['pubDate']}</small>
                </div>""", unsafe_allow_html=True)

    with tab2:
        st.subheader("최신 IT 및 기술 트렌드")
        news = crawl_news("IT 기술 최신")
        for n in news:
            st.markdown(f"<div class='news-card'><a href='{n['link']}'><b>{n['title']}</b></a><br><small>{n['source']}</small></div>", unsafe_allow_html=True)

    with tab3:
        st.subheader("🎨 디자인 & 재택근무 채용 공고")
        st.caption("클라우드 환경에서는 보안 정책상 자동 수집이 제한될 수 있습니다. 아래 버튼을 클릭하여 직접 최신 공고를 확인하세요!")
        
        # 직접 바로가기 버튼 섹션
        col1, col2, col3 = st.columns(3)
        with col1:
            st.link_button("🔍 잡코리아에서 보기", "https://www.jobkorea.co.kr/Search/?stext=%EC%9E%AC%ED%83%9D%20%EB%94%94%EC%9E%90%EC%9D%B8", use_container_width=True)
        with col2:
            st.link_button("🔍 사람인에서 보기", "https://www.saramin.co.kr/zf_user/search?searchword=%EC%9E%AC%ED%83%9D%20%EB%94%94%EC%9E%90%EC%9D%B8", use_container_width=True)
        with col3:
            st.link_button("🔍 서핏에서 보기", "https://jobs.surfit.io/", use_container_width=True)
        
        st.divider()
        
        jobs = crawl_jobs()
        if not jobs:
            st.warning("수집된 공고가 없습니다.")
        else:
            for job in jobs:
                st.markdown(f"""
                <div class='job-card'>
                    <div class='platform-tag {job.get('tag_class', '')}'>{job['platform']}</div>
                    <div style='font-size:1.2em; margin-bottom:10px;'>
                        <a href='{job['url']}' target='_blank' style='text-decoration:none; color:#333;'><b>{job['title']}</b></a>
                    </div>
                    <div style='display:flex; justify-content:space-between; color:#666;'>
                        <span>🏢 {job['company']}</span>
                        <span style='font-size:0.9em;'>📅 {job['date']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 서핏 안내 추가
            st.info("💡 **서핏(Surfit)** 공고는 현재 사이트 보안 및 동적 로딩 정책으로 인해 자동 수집이 제한됩니다. 직접 방문하여 최신 공고를 확인해보세요!")
            st.link_button("서핏 채용 페이지 바로가기", "https://jobs.surfit.io/", use_container_width=True)

    with tab4:
        st.subheader("🎪 전시, 행사 및 박람회 소식")
        news = crawl_news("전시회 박람회 일정")
        for n in news:
             st.markdown(f"<div class='news-card'><a href='{n['link']}'><b>{n['title']}</b></a></div>", unsafe_allow_html=True)

    with tab5:
        st.subheader("📚 에듀테크 및 교육 혁신 소식")
        news = crawl_news("에듀테크 미래 교육")
        for n in news:
             st.markdown(f"<div class='news-card'><a href='{n['link']}'><b>{n['title']}</b></a></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
