import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

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
        res = requests.get(jk_url, headers=get_headers(), timeout=10)
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
        pass

    # 2. 사람인
    try:
        sr_url = "https://www.saramin.co.kr/zf_user/search?search_area=main&search_done=y&search_optional_item=n&searchType=search&searchword=%EC%9E%AC%ED%83%9D%2B%EC%9B%B9%EB%94%94%EC%9E%90%EC%9D%B8"
        res = requests.get(sr_url, headers=get_headers(), timeout=10)
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
        pass

    # 3. 서핏 (주의: 서핏은 동적 로딩 방식으로 전환되어 정적 크롤링이 제한적임)
    try:
        # 서핏 채용 페이지 URL 업데이트
        sf_url = "https://jobs.surfit.io/" 
        res = requests.get(sf_url, headers=get_headers(), timeout=10)
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
        res = requests.get(rss_url, timeout=10)
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

@st.cache_data(ttl=1800)
def crawl_reddit_hot(subreddit_list):
    results = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    # 1. 레딧 직접 수집 시도
    success = False
    for sub in subreddit_list:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                success = True
                data = res.json()
                posts = data['data']['children']
                for post in posts:
                    p = post['data']
                    if not p['stickied']:
                        results.append({
                            "title": p['title'],
                            "url": "https://www.reddit.com" + p['permalink'],
                            "comments": p['num_comments'],
                            "subreddit": sub,
                            "is_fallback": False
                        })
        except: pass
    
    # 2. 직접 수집 실패 시 구글 뉴스를 통한 우회 수집 (백업)
    if not success or not results:
        combined_query = " OR ".join([f"site:reddit.com/r/{sub}" for sub in subreddit_list])
        fallback_news = crawl_news(f"({combined_query}) when:7d")
        for n in fallback_news:
            results.append({
                "title": n['title'].replace(" - reddit", ""),
                "url": n['link'],
                "comments": "N/A", # 백업 모드에서는 댓글 수 확인 불가
                "subreddit": "Reddit",
                "is_fallback": True
            })
    
    # 직접 수집 데이터는 댓글 순 정렬, 백업 데이터는 수집 순 유지
    if any(not r['is_fallback'] for r in results):
        return sorted([r for r in results if not r['is_fallback']], key=lambda x: x['comments'], reverse=True)[:10]
    return results[:10]

# --- UI 메인 로직 ---
def main():
    st.sidebar.title("🚀 Edu-Job Bot")
    st.sidebar.info(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if st.sidebar.button("🔄 전체 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.title("📌 실시간 정보 대시보드")
    
    # 6개 탭 생성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🌍 주요 뉴스", 
        "💻 IT/테크", 
        "🎨 취업(디자인/재택)", 
        "🎪 행사/박람회", 
        "🏢 회사 / 투자",
        "🍱 맛집/여행"
    ])

    with tab1:
        st.subheader("오늘의 글로벌/종합 주요 뉴스")
        news = crawl_news("주요 종합 뉴스 when:1d")
        for n in news:
            st.markdown(f"""<div class='news-card'>
                <a href='{n['link']}' target='_blank' style='text-decoration:none; color:#333;'>
                <b>{n['title']}</b></a><br>
                <small>{n['source']} | {n['pubDate']}</small>
                </div>""", unsafe_allow_html=True)

    with tab2:
        st.subheader("🚀 IT 전문 채널 최신 아티클")
        st.caption("요즘IT, 서핏, 커리어리, 긱뉴스의 최신 기술 트렌드를 모아봅니다.")
        # 지정된 전문 사이트들에서만 최신글 수집 (site: 연산자 활용)
        special_query = "(site:yozm.wishket.com OR site:surfit.io OR site:careerly.co.kr OR site:news.hada.io) when:7d"
        news = crawl_news(special_query)
        for n in news:
            st.markdown(f"<div class='news-card'><a href='{n['link']}' target='_blank' style='text-decoration:none; color:#333;'><b>{n['title']}</b></a><br><small>{n['source']}</small></div>", unsafe_allow_html=True)

        st.divider()
        
        # 레딧 글로벌 핫 토픽 TOP 10 (댓글 수 기준)
        st.subheader("🌐 글로벌 핫 토픽 TOP 10")
        
        hot_reddit_posts = crawl_reddit_hot(['EdTech', 'UXDesign', 'OpenAI', 'Technology'])
        
        if hot_reddit_posts:
            for i, p in enumerate(hot_reddit_posts, 1):
                st.markdown(f"""
                <div class='news-card' style='border-left-color: #FF4500; padding: 12px 18px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div style='flex: 1;'>
                            <span style='color: #FF4500; font-weight: bold; margin-right: 10px;'>{i}위</span>
                            <a href='{p['url']}' target='_blank' style='text-decoration:none; color:#333;'><b>{p['title']}</b></a>
                        </div>
                        <div style='background: #fff0eb; padding: 2px 8px; border-radius: 20px; font-size: 0.85em; color: #FF4500;'>
                            💬 {p['comments']}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("실시간 데이터를 불러올 수 없습니다.")

    with tab3:
        st.subheader("🎨 디자인 & 재택근무 채용 공고")
        st.info("🔍 현재 검색 키워드는 **'재택 디자인'** 입니다.")
        
        jobs = crawl_jobs()
        
        if jobs:
            # 수집된 공고가 있는 경우
            st.caption("실시간으로 수집된 공고 리스트입니다.")
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
            
            st.divider()
            st.caption("더 많은 공고가 궁금하다면?")
        else:
            # 수집된 공고가 없는 경우 (차단 또는 오류)
            st.warning("⚠️ 현재 클라우드 환경의 보안 정책으로 인해 실시간 수집이 제한되고 있습니다.")
            st.write("아래 버튼을 클릭하여 각 플랫폼에서 최신 공고를 직접 확인하실 수 있습니다.")

        # 공통 바로가기 버튼 (수집 여부와 상관없이 접근 가능하게 하단 배치 또는 실패 시 강조)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.link_button("🔍 잡코리아에서 보기", "https://www.jobkorea.co.kr/Search/?stext=%EC%9E%AC%ED%83%9D%20%EB%94%94%EC%9E%90%EC%9D%B8", use_container_width=True)
        with col2:
            st.link_button("🔍 사람인에서 보기", "https://www.saramin.co.kr/zf_user/search?searchword=%EC%9E%AC%ED%83%9D%20%EB%94%94%EC%9E%90%EC%9D%B8", use_container_width=True)
        with col3:
            st.link_button("🔍 서핏에서 보기", "https://jobs.surfit.io/", use_container_width=True)

    with tab4:
        st.subheader("🎪 전시, 행사 및 박람회 소식")
        news = crawl_news("전시회 박람회 일정 when:30d")
        for n in news:
             st.markdown(f"<div class='news-card'><a href='{n['link']}'><b>{n['title']}</b></a></div>", unsafe_allow_html=True)

    with tab5:
        st.subheader("🏢 IT 기업 가치 및 투자 트렌드")
        
        # 1. KRX Value-up IT 상위 기업 (조사 데이터 기반)
        st.markdown("#### 📈 KRX Value-up IT 상위 기업 (PBR 기준)")
        value_up_data = pd.DataFrame({
            "순위": [1, 2, 3, 4, 5],
            "종목명": ["파두", "하이딥", "노타", "클로봇", "한미반도체"],
            "PBR": [54.39, 39.06, 35.96, 26.09, 17.51],
            "시가총액": ["약 5조", "미확인", "비상장", "미확인", "약 37.7조"]
        })
        st.table(value_up_data)
        
        # 1-2. The VC 선정 핫 스타트업 (조사 데이터 기반)
        st.markdown("#### 🔥 The VC 선정: 지금 가장 핫한 스타트업 7선")
        hot_startups = pd.DataFrame({
            "기업명": ["원프레딕트", "콘토로로보틱스", "노보렉스", "리얼월드", "이노오토텍", "이노제닉스", "비저너리"],
            "주요분야": ["산업용 AI", "물류 로봇", "AI 신약개발", "피지컬 AI", "제조 자동화", "분자진단", "자율주행 데이터"],
            "투자단계": ["Pre-IPO", "Series B", "Series B", "전략적투자", "Series A", "Series A", "Seed"],
            "Hot 포인트": ["상장 앞둔 산업용 AI 대장주", "글로벌 물류 자동화 수요 급증", "210억 대규모 투자 유치 성공", "대기업들과 협업하는 AI 로봇", "파격적 규모의 투자 진행 중", "바이오 테크 분야의 라이징 스타", "자율주행 핵심 데이터 솔루션"]
        })
        st.table(hot_startups)

        # 2. 경제 지표 해설 Expander
        with st.expander("🧐 디자이너 & IT 직군을 위한 경제 지표 가이드"):
            st.markdown("""
            **이 지표를 왜 봐야 할까요?**
            - **PBR (주가순자산비율)**: 기업의 '장부상 가치' 대비 주가가 몇 배인지 나타냅니다.
                - IT/테크 기업은 공장 같은 물리적 자산보다 **'인적 자원(개발/디자인)'**과 **'기술력'**이 핵심이기에 PBR이 높게 형성됩니다.
                - **인사이트**: PBR이 높을수록 시장은 그 회사의 **디자인 감각, UX, 브랜드 가치**를 높게 평가한다는 뜻입니다.
            - **시가총액**: 회사의 전체 몸값입니다. 시가총액이 크고 PBR이 높은 회사(예: 한미반도체)는 업계의 트렌드를 주도하는 **'표준'**이 될 확률이 높습니다.
            """)

        with st.expander("🚀 스타트업 투자 단계(Series)의 비밀"):
            st.markdown("""
            **The VC 데이터를 볼 때 '단계'가 중요한 이유:**
            - **Seed ~ Series A**: 아이디어를 제품으로 만드는 단계. **(취업 팁: 초기 멤버로서 영향력을 발휘하고 싶다면!)**
            - **Series B ~ C**: 시장 점유율을 확장하는 단계. 서비스 리뉴얼과 고도화가 활발함. **(취업 팁: 체계적인 시스템에서 고도화된 작업을 하고 싶다면!)**
            - **Pre-IPO**: 상장 직전 단계. 재무적으로 안정적이며 큰 보상이 기대됨.
            
            **💡 인사이트**: 최근 투자가 '어떤 단계'에 몰리는지를 보면, 지금이 **'새로운 도전'**의 시기인지 **'내실 다지기'**의 시기인지 알 수 있습니다.
            """)

        st.divider()
        
        # 3. 에듀테크 투자 및 뉴스
        st.markdown("#### 🎓 에듀테크(EduTech) 투자 및 산업 동향")
        st.caption("최근 에듀테크 투자는 **'개인화 AI 학습'**과 **'성인 직무 교육'**에 집중되고 있습니다.")
        if not news:
            st.write("최근 주요 투자 소식이 없습니다. [The VC](https://thevc.kr/)에서 직접 확인해보세요.")
        else:
            for n in news:
                st.markdown(f"<div class='news-card' style='border-left-color:#6f42c1;'><a href='{n['link']}'><b>{n['title']}</b></a></div>", unsafe_allow_html=True)
        
        st.link_button("더 자세한 투자 정보 (The VC)", "https://thevc.kr/", use_container_width=True)

    with tab6:
        st.subheader("🍱 나의 맛집 지도: 우리맛집지도")
        
        # 1. 지도 데이터 정의 (공유 리스트 기반 주요 거점)
        if 'map_places' not in st.session_state:
            st.session_state['map_places'] = [
                {"name": "부천집", "lat": 37.5028, "lng": 126.7531, "cat": "생선구이", "addr": "경기 부천시 상동 534-1"},
                {"name": "진주집", "lat": 37.5212, "lng": 126.9242, "cat": "국수", "addr": "서울 영등포구 여의도동 36-2"},
                {"name": "삼거리먼지막순대국", "lat": 37.4932, "lng": 126.8981, "cat": "순대국", "addr": "서울 영등포구 대림동 963-9"},
                {"name": "샤브올데이 가산점", "lat": 37.4812, "lng": 126.8831, "cat": "샤브샤브", "addr": "서울 금천구 가산동 60-3"},
                {"name": "쿄카이젠", "lat": 37.3942, "lng": 126.9631, "cat": "일식당", "addr": "안양 동안구 관양동 1588-13"},
                {"name": "타르데마 베이커리", "lat": 37.5512, "lng": 126.8371, "cat": "베이커리", "addr": "서울 강서구 내발산동 702-22"},
                {"name": "소플러스 부천점", "lat": 37.5052, "lng": 126.7511, "cat": "소고기구이", "addr": "경기 부천시 상동 1110"}
            ]

        # 2. 지도 표시 영역
        st.markdown("#### 📍 주요 맛집 거점 확인")
        
        # 지도 중심점 계산 (평균 위치)
        m = folium.Map(location=[37.49, 126.85], zoom_start=11, tiles="cartodbpositron")
        
        for p in st.session_state['map_places']:
            folium.Marker(
                [p['lat'], p['lng']],
                popup=f"<b>{p['name']}</b><br>{p['cat']}",
                tooltip=p['name'],
                icon=folium.Icon(color='green', icon='info-sign')
            ).add_to(m)
        
        # 스트림릿에 지도 렌더링
        st_folium(m, width="100%", height=400)

        st.divider()

        # 3. 상세 리스트 및 검색
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("#### 📑 전체 리스트")
            st.link_button("📍 네이버 지도에서 전체보기 (438개)", "https://naver.me/GzdECsoU", use_container_width=True)
            
            search_p = st.text_input("🔍 장소 이름 검색", "")
            for p in st.session_state['map_places']:
                if search_p.lower() in p['name'].lower():
                    st.markdown(f"""
                    <div style='background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #00c73c; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                        <div style='display:flex; justify-content:space-between;'>
                            <b>{p['name']}</b>
                            <span style='color: #00c73c; font-size: 0.85em;'>{p['cat']}</span>
                        </div>
                        <div style='font-size: 0.85em; color: #666; margin-top: 5px;'>{p['addr']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### 💡 지도 활용 팁")
            st.info("""
            - 지도의 마커를 클릭하면 가게 이름을 볼 수 있습니다.
            - 위 지도는 공유해주신 리스트 중 **주요 거점 7곳**을 우선 표시하고 있습니다.
            - 새로운 장소를 추가하려면 아래 버튼을 이용하세요.
            """)
            if st.button("➕ 새 장소 추가 (준비중)", use_container_width=True):
                st.toast("추후 업데이트 예정입니다!")

if __name__ == "__main__":
    main()
