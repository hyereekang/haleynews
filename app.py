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

import streamlit.components.v1 as components

# 커스텀 CSS (디자인 강화)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
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
    
    /* 사이드바 스타일 커스텀 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #eee;
    }
    
    /* 메뉴 버튼 스타일 */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        text-align: left;
        padding: 10px 15px;
        border: 1px solid #f0f2f6;
        background-color: white;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        border-color: #007bff;
        color: #007bff;
        background-color: #f8faff;
    }
    
    /* 모바일 반응형 대응 */
    @media (max-width: 640px) {
        .job-card, .news-card {
            padding: 15px;
        }
        .job-card b, .news-card b {
            font-size: 1em;
        }
        .job-card {
            transition: none; /* 배터리 절약 */
        }
        .job-card:hover {
            transform: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        }
    }
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
        
        job_links = soup.select('a[href*="/Recruit/GI_Read/"]')
        added_urls = set()
        
        for link in job_links:
            href = link['href']
            if href in added_urls: continue
            
            title = link.get_text(strip=True)
            if len(title) > 5:
                company = "확인 필요"
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
        
    return results

def crawl_news(keyword):
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
    headers = {'User-Agent': 'Mozilla/5.0'}
    
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
    
    if not success or not results:
        combined_query = " OR ".join([f"site:reddit.com/r/{sub}" for sub in subreddit_list])
        fallback_news = crawl_news(f"({combined_query}) when:7d")
        for n in fallback_news:
            results.append({
                "title": n['title'].replace(" - reddit", ""),
                "url": n['link'],
                "comments": "N/A",
                "subreddit": "Reddit",
                "is_fallback": True
            })
    
    if any(not r['is_fallback'] for r in results):
        return sorted([r for r in results if not r['is_fallback']], key=lambda x: x['comments'], reverse=True)[:10]
    return results[:10]

@st.cache_data(ttl=3600)
def search_youtube(keyword, limit=10):
    import urllib.request
    import urllib.parse
    import re
    import json
    
    try:
        url = 'https://www.youtube.com/results?search_query=' + urllib.parse.quote(keyword)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        
        match = re.search(r'var ytInitialData = (\{.*?\});</script>', html)
        if not match: return []
            
        data = json.loads(match.group(1))
        contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
        videos = [item['videoRenderer'] for item in contents if 'videoRenderer' in item]
        
        youtube_list = []
        for v in videos[:limit]:
            title = v.get('title', {}).get('runs', [{}])[0].get('text', '제목 없음')
            video_id = v.get('videoId', '')
            channel = v.get('ownerText', {}).get('runs', [{}])[0].get('text', '알 수 없음')
            views = v.get('viewCountText', {}).get('simpleText', '')
            duration = v.get('lengthText', {}).get('simpleText', '')
            thumbnails = v.get('thumbnail', {}).get('thumbnails', [])
            thumbnail_url = thumbnails[0]['url'] if thumbnails else ""
            
            youtube_list.append({
                "title": title,
                "link": f"https://www.youtube.com/watch?v={video_id}",
                "channel": channel,
                "duration": duration,
                "views": views,
                "thumbnail": thumbnail_url
            })
            
        return youtube_list
    except Exception as e:
        return []

# --- UI 메인 로직 ---
def main():
    # 세션 상태 초기화
    if 'menu' not in st.session_state:
        st.session_state['menu'] = "🌍 주요 뉴스"

    # 사이드바 설정
    st.sidebar.title("🚀 Edu-Job Bot")
    st.sidebar.info(f"업데이트: {datetime.now().strftime('%m-%d %H:%M')}")
    
    if st.sidebar.button("🔄 전체 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 카테고리")
    
    # 햄버거 메뉴 대용 (사이드바 버튼 메뉴)
    menu_items = [
        "🌍 주요 뉴스", 
        "💻 IT/테크", 
        "🎨 취업(디자인/재택)", 
        "🎪 행사/박람회", 
        "🏢 회사 / 투자", 
        "🍱 맛집/여행"
    ]
    
    for item in menu_items:
        # 현재 선택된 메뉴는 강조 스타일 적용 (Streamlit 기본 버튼은 스타일링이 제한적이므로 CSS 클래스 활용 가능하나 여기선 로직 우선)
        if st.sidebar.button(item, key=f"btn_{item}", use_container_width=True):
            st.session_state['menu'] = item
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption("© 2024 Edu-Job Bot")

    current_menu = st.session_state['menu']
    
    if current_menu == "🌍 주요 뉴스":
        st.subheader("오늘의 글로벌/종합 주요 뉴스")
        news = crawl_news("주요 종합 뉴스 when:1d")
        for n in news[:5]:
            st.markdown(f"""<div class='news-card'>
                <a href='{n['link']}' target='_blank' style='text-decoration:none; color:#333;'>
                <b>{n['title']}</b></a><br>
                <small>{n['source']} | {n['pubDate']}</small>
                </div>""", unsafe_allow_html=True)
                
        if len(news) > 5:
            with st.expander("🔽 더 많은 뉴스 보기"):
                for n in news[5:]:
                    st.markdown(f"""<div class='news-card'>
                        <a href='{n['link']}' target='_blank' style='text-decoration:none; color:#333;'>
                        <b>{n['title']}</b></a><br>
                        <small>{n['source']} | {n['pubDate']}</small>
                        </div>""", unsafe_allow_html=True)

    elif current_menu == "💻 IT/테크":
        st.subheader("🚀 IT 전문 채널 최신 아티클")
        st.caption("요즘IT, 서핏, 커리어리, 긱뉴스의 최신 트렌드")
        special_query = "(site:yozm.wishket.com OR site:surfit.io OR site:careerly.co.kr OR site:news.hada.io) when:7d"
        news = crawl_news(special_query)
        for n in news[:5]:
            st.markdown(f"<div class='news-card'><a href='{n['link']}' target='_blank' style='text-decoration:none; color:#333;'><b>{n['title']}</b></a><br><small>{n['source']}</small></div>", unsafe_allow_html=True)
            
        if len(news) > 5:
            with st.expander("🔽 더 많은 아티클 보기"):
                for n in news[5:]:
                    st.markdown(f"<div class='news-card'><a href='{n['link']}' target='_blank' style='text-decoration:none; color:#333;'><b>{n['title']}</b></a><br><small>{n['source']}</small></div>", unsafe_allow_html=True)

        st.divider()
        st.subheader("📺 추천 IT/테크 유튜브 영상")
        st.caption("키워드: 'IT 트렌드', '에듀테크' 기반 검색 결과")
        youtube_videos = search_youtube("IT 트렌드 에듀테크", limit=10)
        
        def render_youtube(v):
            st.markdown(f"""
            <div class='news-card' style='border-left-color: #ff0000; display:flex; align-items:center;'>
                <div style='flex-shrink: 0; margin-right: 15px;'>
                    <img src='{v['thumbnail']}' style='width: 120px; border-radius: 8px; object-fit: cover;'>
                </div>
                <div>
                    <a href='{v['link']}' target='_blank' style='text-decoration:none; color:#333; font-size:1.05em;'><b>{v['title']}</b></a>
                    <div style='color: #666; font-size: 0.85em; margin-top: 5px;'>
                        📺 {v['channel']} | 👁️ {v['views']} | ⏱️ {v['duration']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        if youtube_videos:
            for v in youtube_videos[:3]:
                render_youtube(v)
            if len(youtube_videos) > 3:
                with st.expander("🔽 더 많은 추천 영상 보기"):
                    for v in youtube_videos[3:]:
                        render_youtube(v)

        st.divider()
        st.subheader("🌐 글로벌 핫 토픽 TOP 10")
        hot_reddit_posts = crawl_reddit_hot(['EdTech', 'UXDesign', 'OpenAI', 'Technology'])
        if hot_reddit_posts:
            for i, p in enumerate(hot_reddit_posts[:3], 1):
                st.markdown(f"""
                <div class='news-card' style='border-left-color: #FF4500;'>
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
            
            if len(hot_reddit_posts) > 3:
                with st.expander("🔽 전체 TOP 10 보기"):
                    for i, p in enumerate(hot_reddit_posts[3:], 4):
                        st.markdown(f"""
                        <div class='news-card' style='border-left-color: #FF4500;'>
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

    elif current_menu == "🎨 취업(디자인/재택)":
        st.subheader("🎨 디자인 & 재택근무 채용 공고")
        st.info("🔍 검색 키워드: '재택 디자인'")
        jobs = crawl_jobs()
        if jobs:
            for job in jobs[:5]:
                st.markdown(f"""
                <div class='job-card'>
                    <div class='platform-tag {job.get('tag_class', '')}'>{job['platform']}</div>
                    <div style='font-size:1.1em; margin-bottom:10px;'>
                        <a href='{job['url']}' target='_blank' style='text-decoration:none; color:#333;'><b>{job['title']}</b></a>
                    </div>
                    <div style='display:flex; justify-content:space-between; color:#666; font-size:0.9em;'>
                        <span>🏢 {job['company']}</span>
                        <span>📅 {job['date']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            if len(jobs) > 5:
                with st.expander("🔽 더 많은 채용 공고 보기"):
                    for job in jobs[5:]:
                        st.markdown(f"""
                        <div class='job-card'>
                            <div class='platform-tag {job.get('tag_class', '')}'>{job['platform']}</div>
                            <div style='font-size:1.1em; margin-bottom:10px;'>
                                <a href='{job['url']}' target='_blank' style='text-decoration:none; color:#333;'><b>{job['title']}</b></a>
                            </div>
                            <div style='display:flex; justify-content:space-between; color:#666; font-size:0.9em;'>
                                <span>🏢 {job['company']}</span>
                                <span>📅 {job['date']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.warning("실시간 수집 제한 중. 아래 링크를 이용하세요.")
        
        col1, col2, col3 = st.columns(3)
        with col1: st.link_button("잡코리아 바로가기", "https://www.jobkorea.co.kr/Search/?stext=%EC%9E%AC%ED%83%9D%20%EB%94%94%EC%9E%90%EC%9D%B8", use_container_width=True)
        with col2: st.link_button("사람인 바로가기", "https://www.saramin.co.kr/zf_user/search?searchword=%EC%9E%AC%ED%83%9D%20%EB%94%94%EC%9E%90%EC%9D%B8", use_container_width=True)
        with col3: st.link_button("서핏 바로가기", "https://jobs.surfit.io/", use_container_width=True)

    elif current_menu == "🎪 행사/박람회":
        st.subheader("🎪 전국 행사 및 박람회 일정")
        st.caption("💡 구글 '전국행사' 검색 상위 트렌드 (인기/관련도 순)")
        
        # 구글 검색(RSS)이 판단한 관련도/화제성 상위 결과를 가져옵니다.
        news = crawl_news("전국행사 when:30d")
        for i, n in enumerate(news[:5], 1):
            st.markdown(f"""
            <div class='news-card' style='border-left-color: #ffca28;'>
                <div style='display:flex; align-items:flex-start;'>
                    <span style='color: #f57f17; font-weight: bold; font-size: 1.1em; margin-right: 12px;'>{i}</span>
                    <div>
                        <a href='{n['link']}' target='_blank' style='text-decoration:none; color:#333; font-size: 1.05em;'><b>{n['title']}</b></a>
                        <div style='margin-top: 5px;'><small style='color:#666;'>{n['source']} | {n['pubDate']}</small></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        if len(news) > 5:
            with st.expander("🔽 더 많은 행사 보기"):
                for i, n in enumerate(news[5:], 6):
                    st.markdown(f"""
                    <div class='news-card' style='border-left-color: #ffca28;'>
                        <div style='display:flex; align-items:flex-start;'>
                            <span style='color: #f57f17; font-weight: bold; font-size: 1.1em; margin-right: 12px;'>{i}</span>
                            <div>
                                <a href='{n['link']}' target='_blank' style='text-decoration:none; color:#333; font-size: 1.05em;'><b>{n['title']}</b></a>
                                <div style='margin-top: 5px;'><small style='color:#666;'>{n['source']} | {n['pubDate']}</small></div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
        st.divider()
        st.markdown("#### 🎯 추천 행사/레퍼런스 사이트")
        st.link_button("🌸 서울시 축제 공식 홈페이지 방문하기", "https://festival.seoul.go.kr/festival/main/festivalMain.do", use_container_width=True)

    elif current_menu == "🏢 회사 / 투자":
        st.subheader("🏢 IT 기업 가치 및 투자 트렌드")
        st.markdown("#### 📈 KRX Value-up IT 상위 기업 (PBR 기준)")
        value_up_data = pd.DataFrame({
            "순위": [1, 2, 3, 4, 5],
            "종목명": ["파두", "하이딥", "노타", "클로봇", "한미반도체"],
            "PBR": [54.39, 39.06, 35.96, 26.09, 17.51],
            "시가총액": ["약 5조", "미확인", "비상장", "미확인", "약 37.7조"]
        })
        st.table(value_up_data)
        
        st.markdown("#### 🔥 The VC 선정 핫 스타트업")
        hot_startups = pd.DataFrame({
            "기업명": ["원프레딕트", "콘토로로보틱스", "노보렉스", "리얼월드", "이노오토텍", "이노제닉스", "비저너리"],
            "주요분야": ["산업용 AI", "물류 로봇", "AI 신약개발", "피지컬 AI", "제조 자동화", "분자진단", "자율주행 데이터"],
            "투자단계": ["Pre-IPO", "Series B", "Series B", "전략적투자", "Series A", "Series A", "Seed"]
        })
        st.table(hot_startups)

        with st.expander("🧐 경제 지표 가이드"):
            st.markdown("PBR(주가순자산비율)이 높을수록 시장은 그 회사의 인적 자원과 기술력을 높게 평가합니다.")

        st.divider()
        st.markdown("#### 🎓 에듀테크(EduTech) 투자 동향")
        edu_news = crawl_news("에듀테크 투자 뉴스 when:7d")
        for n in edu_news:
            st.markdown(f"<div class='news-card' style='border-left-color:#6f42c1;'><a href='{n['link']}' target='_blank' style='text-decoration:none; color:#333;'><b>{n['title']}</b></a></div>", unsafe_allow_html=True)
        st.link_button("더 자세한 투자 정보 (The VC)", "https://thevc.kr/", use_container_width=True)

    elif current_menu == "🍱 맛집/여행":
        st.subheader("🍱 나의 맛집 지도")
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

        st.info("💡 모바일 배터리 절약을 위해 지도는 클릭 시에만 로드됩니다.")
        if st.button("🗺️ 인터랙티브 지도 열기 / 닫기", use_container_width=True):
            st.session_state['show_map'] = not st.session_state.get('show_map', False)
            
        if st.session_state.get('show_map', False):
            m = folium.Map(location=[37.49, 126.85], zoom_start=11, tiles="cartodbpositron")
            for p in st.session_state['map_places']:
                folium.Marker([p['lat'], p['lng']], popup=p['name'], tooltip=p['name']).add_to(m)
            st_folium(m, width="100%", height=400)

        st.divider()
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("#### 📑 전체 리스트")
            st.link_button("📍 네이버 지도 전체보기", "https://naver.me/GzdECsoU", use_container_width=True)
            search_p = st.text_input("🔍 장소 검색", "")
            for p in st.session_state['map_places']:
                if search_p.lower() in p['name'].lower():
                    st.markdown(f"<div style='background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #00c73c; margin-bottom: 10px;'><b>{p['name']}</b> ({p['cat']})<br><small>{p['addr']}</small></div>", unsafe_allow_html=True)
        with col2:
            st.info("지도의 마커를 클릭해 보세요!")
            if st.button("➕ 추가 (준비중)", use_container_width=True):
                st.toast("곧 업데이트됩니다!")

    # 모바일 등 좁은 화면에서 사이드바 외부(메인 영역) 클릭 시 자연스럽게 접히도록 하는 자바스크립트
    components.html(
        """
        <script>
        const doc = window.parent.document;
        doc.addEventListener('click', function(event) {
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            
            // 사이드바 바깥(메인 영역)을 클릭했을 때
            if (sidebar && !sidebar.contains(event.target)) {
                // 입력창, 버튼, 링크 등 상호작용이 필요한 요소가 아닌 일반 배경을 클릭했을 때만 동작
                const tagName = event.target.tagName;
                const isInteractive = ['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON', 'A'].includes(tagName);
                
                if (!isInteractive) {
                    // ESC 키 이벤트를 발생시켜 사이드바 닫기 (Streamlit 기본 단축키)
                    const escEvent = new KeyboardEvent('keydown', {
                        key: 'Escape',
                        code: 'Escape',
                        keyCode: 27,
                        which: 27,
                        bubbles: true
                    });
                    doc.dispatchEvent(escEvent);
                }
            }
        });
        </script>
        """,
        height=0,
        width=0
    )

if __name__ == "__main__":
    main()
