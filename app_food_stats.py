"""
📊 식품산업통계 조회 시스템
━━━━━━━━━━━━━━━━━━━━━━━━━━━
aT 식품산업정보 API (atfis.or.kr)
식품산업 기초통계 연도별 조회 및 시각화
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ━━━ 페이지 설정 ━━━
st.set_page_config(
    page_title="식품산업통계 조회",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ━━━ 스타일 ━━━
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #f8f9fb; }
div[data-testid="stMetric"] { background: #f0f2f5; border-radius: 10px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# ━━━ API 설정 ━━━
API_URL = "https://www.atfis.or.kr/home/api/food/stats/basic.do"
DEFAULT_API_KEY = "z9JeRfaB44up466XHs+5pTcV31n58LqRkSHZ8H66xbw="

# ━━━ 카테고리 정보 ━━━
CATEGORIES = {
    "DOMESTIC": "국내 식품산업",
    "EXPORT": "식품 수출",
    "IMPORT": "식품 수입",
}

# ━━━ API 호출 ━━━
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_food_stats(api_key, begin_year, end_year, category=None):
    """aT 식품산업통계 API 호출"""
    params = {
        "apiKey": api_key,
        "beginYear": str(begin_year),
        "endYear": str(end_year),
    }
    if category:
        params["category1"] = category

    try:
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # 응답이 리스트인 경우
        if isinstance(data, list):
            return data, "정상", len(data)

        # 응답이 딕셔너리인 경우 (에러 등)
        if isinstance(data, dict):
            if "result" in data:
                return data.get("data", []), data.get("result", ""), 0
            # 데이터가 특정 키 안에 있을 수 있음
            for key in ["data", "body", "items", "list"]:
                if key in data:
                    items = data[key]
                    if isinstance(items, list):
                        return items, "정상", len(items)
            # 자체가 단일 레코드일 수 있음
            return [data], "정상", 1

        return None, f"예상치 못한 응답 형식: {type(data)}", 0

    except requests.exceptions.Timeout:
        return None, "API 응답 시간 초과", 0
    except requests.exceptions.ConnectionError:
        return None, "API 서버 연결 실패", 0
    except requests.exceptions.JSONDecodeError:
        return None, f"JSON 파싱 실패 (응답: {response.text[:200]})", 0
    except Exception as e:
        return None, f"오류: {str(e)}", 0


def to_dataframe(rows):
    """API 응답을 보기 좋은 DataFrame으로 변환"""
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # 컬럼 한글 매핑
    col_map = {
        "fdmsId": "ID",
        "fdmsYear": "연도",
        "fdmsSectorCd": "산업분류",
        "fdmsNumber": "금액",
        "fdmsRatio": "비율(%)",
        "fdmsUnit": "단위",
        "fdmsIndustryGubun": "구분코드",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)

    # 연도 정렬
    if "연도" in df.columns:
        df["연도"] = df["연도"].astype(str)
        df = df.sort_values("연도").reset_index(drop=True)

    # 금액 숫자 변환
    if "금액" in df.columns:
        df["금액"] = pd.to_numeric(df["금액"], errors="coerce")

    # 비율 숫자 변환
    if "비율(%)" in df.columns:
        df["비율(%)"] = pd.to_numeric(df["비율(%)"], errors="coerce")

    # 구분 한글화
    if "구분코드" in df.columns:
        df["구분"] = df["구분코드"].map(CATEGORIES).fillna(df["구분코드"])

    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  사이드바
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("## 📊 조회 설정")
    st.markdown("---")

    # API 키
    api_key = st.text_input(
        "🔑 API 인증키",
        value=DEFAULT_API_KEY,
        type="password",
        help="atfis.or.kr에서 발급받은 인증키"
    )

    st.markdown("---")

    # 연도 범위
    current_year = datetime.now().year
    col1, col2 = st.columns(2)
    with col1:
        begin_year = st.number_input("시작연도", 2000, current_year, 2015)
    with col2:
        end_year = st.number_input("종료연도", 2000, current_year, current_year - 1)

    if begin_year > end_year:
        st.error("시작연도가 종료연도보다 큽니다.")

    st.markdown("---")

    # 카테고리 선택
    st.markdown("**카테고리 선택:**")
    sel_categories = []
    for code, name in CATEGORIES.items():
        if st.checkbox(name, value=(code == "DOMESTIC"), key=f"cat_{code}"):
            sel_categories.append(code)

    all_at_once = st.checkbox("전체 조회 (카테고리 무관)", value=False)

    st.markdown("---")
    run = st.button("🚀 조회 실행", use_container_width=True, type="primary")

    st.markdown("---")
    st.caption("📡 데이터: aT 식품산업정보")
    st.caption("🌐 atfis.or.kr")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  메인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("# 📊 식품산업통계 조회 시스템")
st.markdown("aT 식품산업정보 API를 활용한 연도별 식품산업 기초통계 조회")
st.markdown("---")

if run:
    if begin_year > end_year:
        st.error("❌ 시작연도가 종료연도보다 큽니다. 수정해주세요.")
        st.stop()

    if not all_at_once and not sel_categories:
        st.warning("⚠️ 카테고리를 1개 이상 선택하거나 '전체 조회'를 체크하세요.")
        st.stop()

    # ━━━ 데이터 수집 ━━━
    all_rows = []

    if all_at_once:
        with st.spinner("📡 전체 데이터 조회 중..."):
            rows, msg, total = fetch_food_stats(api_key, begin_year, end_year)
            if rows:
                all_rows = rows
            elif rows is None:
                st.error(f"❌ 조회 실패: {msg}")
                st.stop()
    else:
        progress = st.progress(0, text="조회 중...")
        for i, cat in enumerate(sel_categories):
            progress.progress((i + 1) / len(sel_categories), text=f"📡 {CATEGORIES[cat]} 조회 중...")
            rows, msg, total = fetch_food_stats(api_key, begin_year, end_year, cat)
            if rows:
                all_rows.extend(rows)
        progress.empty()

    if not all_rows:
        st.warning("⚠️ 조회 결과가 없습니다.")
        st.stop()

    df = to_dataframe(all_rows)

    # ━━━ 디버그 (접을 수 있게) ━━━
    with st.expander("🔧 API 응답 원본 확인 (디버그)", expanded=False):
        st.json(all_rows[:5])
        st.caption(f"총 {len(all_rows)}건 수신")

    # ━━━ 상단 메트릭 ━━━
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("조회 건수", f"{len(df)}건")
    c2.metric("기간", f"{begin_year}~{end_year}")

    if "산업분류" in df.columns:
        c3.metric("산업분류 수", f"{df['산업분류'].nunique()}개")

    if "금액" in df.columns and not df["금액"].isna().all():
        latest_year = df["연도"].max()
        latest_total = df[df["연도"] == latest_year]["금액"].sum()
        unit = df["단위"].iloc[0] if "단위" in df.columns else ""
        c4.metric(f"{latest_year}년 합계", f"{latest_total:,.1f} {unit}")

    st.markdown("---")

    # ━━━ 탭 ━━━
    tab1, tab2, tab3 = st.tabs(["📊 차트 분석", "📋 데이터 테이블", "📥 다운로드"])

    with tab1:
        st.markdown("### 📊 식품산업 통계 시각화")

        # 산업분류별 연도 추이
        if "산업분류" in df.columns and "금액" in df.columns:
            sectors = df["산업분류"].unique().tolist()

            if len(sectors) > 1:
                # 복수 산업분류 → 그룹 라인차트
                fig_line = px.line(
                    df, x="연도", y="금액", color="산업분류",
                    title="산업분류별 연도 추이",
                    markers=True,
                    labels={"금액": f"금액 ({df['단위'].iloc[0] if '단위' in df.columns else ''})"},
                )
                fig_line.update_layout(height=500, legend=dict(orientation="h", y=-0.15))
                st.plotly_chart(fig_line, use_container_width=True)

                # 산업분류별 최신연도 비교
                latest = df[df["연도"] == df["연도"].max()]
                if not latest.empty:
                    fig_bar = px.bar(
                        latest, x="산업분류", y="금액",
                        title=f"{df['연도'].max()}년 산업분류별 비교",
                        color="산업분류",
                        text="금액",
                    )
                    fig_bar.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                    fig_bar.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_bar, use_container_width=True)

            else:
                # 단일 산업분류 → 바차트
                fig = px.bar(
                    df, x="연도", y="금액",
                    title=f"{sectors[0]} — 연도별 추이",
                    text="금액",
                    color="금액",
                    color_continuous_scale="Blues",
                )
                fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                fig.update_layout(height=500, showlegend=False)
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            # 성장률 계산
            st.markdown("#### 📈 전년대비 성장률")
            for sector in sectors:
                s_df = df[df["산업분류"] == sector].sort_values("연도").copy()
                if len(s_df) > 1 and "금액" in s_df.columns:
                    s_df["성장률(%)"] = s_df["금액"].pct_change() * 100

                    fig_growth = px.bar(
                        s_df.dropna(subset=["성장률(%)"]),
                        x="연도", y="성장률(%)",
                        title=f"{sector} — 전년대비 성장률",
                        color="성장률(%)",
                        color_continuous_scale="RdYlGn",
                        color_continuous_midpoint=0,
                    )
                    fig_growth.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
                    fig_growth.update_layout(height=350)
                    fig_growth.update_coloraxes(showscale=False)
                    st.plotly_chart(fig_growth, use_container_width=True)

        # 비율 데이터가 있으면
        if "비율(%)" in df.columns and df["비율(%)"].notna().any() and (df["비율(%)"] != 0).any():
            st.markdown("#### 🥧 산업분류별 비율")
            latest_ratio = df[df["연도"] == df["연도"].max()]
            if not latest_ratio.empty:
                fig_pie = px.pie(
                    latest_ratio, values="비율(%)", names="산업분류",
                    title=f"{df['연도'].max()}년 산업분류별 비율",
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.markdown(f"### 📋 조회 데이터 ({len(df)}건)")

        # 필터
        if "산업분류" in df.columns:
            filter_sectors = ["전체"] + sorted(df["산업분류"].unique().tolist())
            sel = st.selectbox("산업분류 필터", filter_sectors)
            show_df = df if sel == "전체" else df[df["산업분류"] == sel]
        else:
            show_df = df

        # 테이블 표시할 컬럼
        show_cols = ["연도", "산업분류", "금액", "비율(%)", "단위", "구분"]
        show_cols = [c for c in show_cols if c in show_df.columns]

        st.dataframe(
            show_df[show_cols].reset_index(drop=True),
            use_container_width=True,
            height=500,
        )

        # 피벗 테이블
        if "산업분류" in df.columns and "금액" in df.columns:
            st.markdown("#### 📊 피벗 테이블 (연도 × 산업분류)")
            pivot = df.pivot_table(
                index="연도", columns="산업분류", values="금액", aggfunc="sum"
            )
            st.dataframe(
                pivot.style.format("{:,.1f}"),
                use_container_width=True,
            )

    with tab3:
        st.markdown("### 📥 데이터 다운로드")

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 CSV 다운로드",
            csv,
            f"식품산업통계_{begin_year}_{end_year}_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True,
        )

        st.markdown("---")
        st.markdown("#### 원시 데이터 (전체 필드)")
        st.dataframe(df, use_container_width=True)

else:
    # ━━━ 초기 안내 ━━━
    st.info("👈 왼쪽 사이드바에서 조건을 설정하고 **[조회 실행]** 버튼을 누르세요.")

    st.markdown("""
    ### 사용 방법

    1. **API 인증키** — atfis.or.kr에서 발급받은 키 입력 (샘플키 기본 설정됨)
    2. **조회 기간** — 시작/종료 연도 설정
    3. **카테고리** — 국내 식품산업, 수출, 수입 중 선택 (복수 가능)
    4. **조회 실행** — 버튼 클릭

    ### API 정보

    | 항목 | 내용 |
    |---|---|
    | 서비스명 | 식품산업 기초통계 |
    | 제공기관 | aT 한국농수산식품유통공사 |
    | 엔드포인트 | `atfis.or.kr/home/api/food/stats/basic.do` |
    | 응답필드 | 연도, 산업분류, 금액, 비율, 단위 |
    """)

    # 샘플 데이터 구조 표시
    st.markdown("### 응답 데이터 구조 (샘플)")
    sample = pd.DataFrame([
        {"연도": "2016", "산업분류": "협의의 식품산업", "금액": 227413.9, "비율(%)": 0, "단위": "십억원", "구분": "DOMESTIC"},
        {"연도": "2017", "산업분류": "협의의 식품산업", "금액": 245000.0, "비율(%)": 0, "단위": "십억원", "구분": "DOMESTIC"},
        {"연도": "2018", "산업분류": "협의의 식품산업", "금액": 260000.0, "비율(%)": 0, "단위": "십억원", "구분": "DOMESTIC"},
    ])
    st.dataframe(sample, use_container_width=True)
