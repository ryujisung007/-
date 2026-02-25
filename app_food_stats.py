"""
📊 식품산업통계 조회 시스템 v3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
aT 식품산업정보 API (atfis.or.kr)
- 5개 API 통합 지원
- 세부 분류/업종/구분 필터
- 산업분류별 비교 & 전체시장 대비 비중
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import json

# ━━━ 페이지 설정 ━━━
st.set_page_config(
    page_title="식품산업통계 분석",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #f8f9fb; }
div[data-testid="stMetric"] { background: #f0f2f5; border-radius: 10px; padding: 12px; }
.sidebar-section { background: #fff; border-radius: 8px; padding: 10px; margin: 8px 0; border: 1px solid #e5e7eb; }
</style>
""", unsafe_allow_html=True)

# ━━━ API 설정 ━━━
DEFAULT_API_KEY = "z9JeRfaB44up466XHs+5pTcV31n58LqRkSHZ8H66xbw="

# 5개 API 엔드포인트
API_ENDPOINTS = {
    "국내 식품시장규모": {
        "url": "https://www.atfis.or.kr/home/api/food/stats/basic.do",
        "desc": "국내외 식품시장 규모 (십억원)",
        "icon": "🏪",
    },
    "산업현황통계": {
        "url": "https://www.atfis.or.kr/home/api/food/stats/industry.do",
        "desc": "식품제조업/외식업/유통업 산업현황",
        "icon": "🏭",
    },
    "음식료품 제조업 업종별": {
        "url": "https://www.atfis.or.kr/home/api/food/stats/manufacture.do",
        "desc": "음식료품 제조업 업종별 현황",
        "icon": "⚙️",
    },
    "식품원료 사용량": {
        "url": "https://www.atfis.or.kr/home/api/food/stats/material.do",
        "desc": "식품원료별 사용량 (총/국산/수입)",
        "icon": "🌾",
    },
    "식품산업 경기동향": {
        "url": "https://www.atfis.or.kr/home/api/food/stats/prospect.do",
        "desc": "생산·판매·고용·원재료 경기동향지수",
        "icon": "📈",
    },
}

# category1 분류 (웹사이트 기준)
CATEGORY1_OPTIONS = {
    "전체 (분류 없이 조회)": None,
    "🏠 국내 식품산업 (DOMESTIC)": "DOMESTIC",
    "📤 식품 수출 (EXPORT)": "EXPORT",
    "📥 식품 수입 (IMPORT)": "IMPORT",
    "🏭 식품 제조업 (MANUFACTURE)": "MANUFACTURE",
    "🍽️ 외식업 (EATOUT)": "EATOUT",
    "🛒 식품 유통업 (DISTIBUTION)": "DISTIBUTION",
}

# tabGubun 구분
TAB_GUBUN_OPTIONS = {
    "산업일반 (BASIC)": "BASIC",
    "업종별 (INDUSTRY)": "INDUSTRY",
}

COLORS = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel2 + px.colors.qualitative.Bold


# ━━━ API 호출 ━━━
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_api(url, api_key, begin_year, end_year, category1=None, tab_gubun=None):
    """ATFIS API 범용 호출"""
    params = {
        "apiKey": api_key,
        "beginYear": str(begin_year),
        "endYear": str(end_year),
    }
    if category1:
        params["category1"] = category1
    if tab_gubun:
        params["tabGubun"] = tab_gubun

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, list):
            return data, "정상", params
        if isinstance(data, dict):
            for key in ["data", "body", "items", "list", "result", "response"]:
                if key in data and isinstance(data[key], list):
                    return data[key], "정상", params
            if "fdmsId" in data or "fdmsYear" in data:
                return [data], "정상", params
            msg = data.get("message", data.get("msg", str(data)[:200]))
            return None, f"API 응답: {msg}", params
        return None, f"예상치 못한 응답: {type(data).__name__}", params

    except requests.exceptions.Timeout:
        return None, "응답 시간 초과 (30초)", params
    except requests.exceptions.ConnectionError:
        return None, "서버 연결 실패", params
    except json.JSONDecodeError:
        return None, f"JSON 파싱 실패 (HTTP {resp.status_code})", params
    except Exception as e:
        return None, f"오류: {e}", params


def fetch_multi_category(url, api_key, begin_year, end_year, categories, tab_gubun=None):
    """여러 카테고리를 순차 호출 후 병합"""
    all_rows = []
    results_info = []

    for cat_label, cat_code in categories:
        rows, msg, params = fetch_api(url, api_key, begin_year, end_year, cat_code, tab_gubun)
        cnt = len(rows) if rows else 0
        results_info.append({"분류": cat_label, "코드": cat_code or "-", "건수": cnt, "상태": msg})
        if rows:
            # 카테고리 태그 추가
            for r in rows:
                r["_query_category"] = cat_label
            all_rows.extend(rows)
        time.sleep(0.3)

    return all_rows, results_info


def to_df(rows):
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    col_map = {
        "fdmsId": "ID", "fdmsYear": "연도", "fdmsSectorCd": "산업분류",
        "fdmsNumber": "금액", "fdmsRatio": "비율", "fdmsUnit": "단위",
        "fdmsIndustryGubun": "구분코드", "_query_category": "조회분류",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)

    if "연도" in df.columns:
        df["연도"] = df["연도"].astype(str)
    if "금액" in df.columns:
        df["금액"] = pd.to_numeric(df["금액"], errors="coerce")
    if "비율" in df.columns:
        df["비율"] = pd.to_numeric(df["비율"], errors="coerce")

    # 구분 매핑
    gubun_map = {
        "DOMESTIC": "국내 식품산업", "EXPORT": "식품 수출", "IMPORT": "식품 수입",
        "MANUFACTURE": "식품 제조업", "EATOUT": "외식업", "DISTIBUTION": "식품 유통업",
    }
    if "구분코드" in df.columns:
        df["구분"] = df["구분코드"].map(gubun_map).fillna(df["구분코드"])

    return df.sort_values(["연도"] + (["산업분류"] if "산업분류" in df.columns else [])).reset_index(drop=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  사이드바
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("## 📊 통계 조회 설정")

    # ─── 1. API 인증키 ───
    with st.expander("🔑 API 인증키", expanded=False):
        api_key = st.text_input("인증키", value=DEFAULT_API_KEY, type="password", label_visibility="collapsed")

    st.markdown("---")

    # ─── 2. API 종류 선택 ───
    st.markdown("### 📡 API 선택")
    api_names = list(API_ENDPOINTS.keys())
    selected_api = st.selectbox(
        "통계 종류",
        api_names,
        index=0,
        format_func=lambda x: f"{API_ENDPOINTS[x]['icon']} {x}",
    )
    st.caption(API_ENDPOINTS[selected_api]["desc"])

    st.markdown("---")

    # ─── 3. 기간 설정 ───
    st.markdown("### 📅 조회 기간")
    cur = datetime.now().year
    c1, c2 = st.columns(2)
    begin_year = c1.number_input("시작", 2000, cur, 2015, key="by")
    end_year = c2.number_input("종료", 2000, cur, cur - 1, key="ey")

    st.markdown("---")

    # ─── 4. 분류 조건 (category1) ───
    st.markdown("### 🏷️ 분류 조건")

    query_mode = st.radio(
        "조회 방식",
        ["단일 분류", "복수 분류 (비교)", "전체 일괄"],
        index=0,
        horizontal=True,
    )

    sel_categories = []

    if query_mode == "단일 분류":
        cat_choice = st.selectbox("분류 선택", list(CATEGORY1_OPTIONS.keys()))
        cat_code = CATEGORY1_OPTIONS[cat_choice]
        sel_categories = [(cat_choice, cat_code)]

    elif query_mode == "복수 분류 (비교)":
        st.caption("비교할 분류를 체크하세요")
        for label, code in CATEGORY1_OPTIONS.items():
            if code is None:
                continue
            if st.checkbox(label, value=(code in ["DOMESTIC", "EXPORT"]), key=f"mc_{code}"):
                sel_categories.append((label, code))

    else:  # 전체 일괄
        for label, code in CATEGORY1_OPTIONS.items():
            if code is not None:
                sel_categories.append((label, code))
        st.info(f"6개 분류 모두 조회합니다")

    st.markdown("---")

    # ─── 5. 탭 구분 (산업일반/업종별) ───
    st.markdown("### 📑 구분")
    tab_gubun_label = st.radio(
        "데이터 구분",
        list(TAB_GUBUN_OPTIONS.keys()),
        index=0,
        horizontal=True,
    )
    tab_gubun = TAB_GUBUN_OPTIONS[tab_gubun_label]

    st.markdown("---")

    # ─── 6. 후처리 필터 옵션 ───
    st.markdown("### 🔍 결과 필터")
    keyword_filter = st.text_input("산업분류 키워드 (포함)", placeholder="예: 제조, 음식점, 유통")
    exclude_keyword = st.text_input("제외 키워드", placeholder="예: 담배, 농림")
    min_amount = st.number_input("최소 금액 (0=없음)", 0, 999999999, 0, step=1000)

    st.markdown("---")

    # ─── 조회 실행 ───
    run = st.button("🚀 조회 실행", use_container_width=True, type="primary")

    st.markdown("---")
    st.caption("📡 aT 식품산업정보 (atfis.or.kr)")
    st.caption(f"선택 API: {selected_api}")
    st.caption(f"분류: {len(sel_categories)}개 | 구분: {tab_gubun}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  메인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("# 📊 식품산업통계 분석 시스템")
st.markdown(f"**{API_ENDPOINTS[selected_api]['icon']} {selected_api}** · 세부 분류별 비교 · 전체시장 대비 비중 · 연도별 추이")
st.markdown("---")

if not run:
    st.info("👈 사이드바에서 조건을 설정하고 **[조회 실행]** 버튼을 누르세요.")

    cl1, cl2 = st.columns(2)
    with cl1:
        st.markdown("""
        ### 📡 제공 API (5종)
        | API | 설명 |
        |---|---|
        | 🏪 국내 식품시장규모 | 시장 총규모, 산업분류별 추이 |
        | 🏭 산업현황통계 | 제조/외식/유통 산업현황 |
        | ⚙️ 음식료품 제조업 | 업종별 세부 현황 |
        | 🌾 식품원료 사용량 | 원료별 총/국산/수입량 |
        | 📈 경기동향 | 분기별 경기동향지수 |
        """)
    with cl2:
        st.markdown("""
        ### 🏷️ 분류 조건 (category1)
        | 코드 | 설명 |
        |---|---|
        | DOMESTIC | 국내 식품산업 전체 |
        | EXPORT | 식품 수출 |
        | IMPORT | 식품 수입 |
        | MANUFACTURE | 식품 제조업 |
        | EATOUT | 외식업 |
        | DISTIBUTION | 식품 유통업 |

        ### 📑 구분 (tabGubun)
        - **산업일반(BASIC)**: 시장규모 총괄
        - **업종별(INDUSTRY)**: 업종별 세분화
        """)
    st.stop()


# ━━━ 데이터 수집 ━━━
api_url = API_ENDPOINTS[selected_api]["url"]

with st.spinner(f"📡 {selected_api} 데이터 조회 중... ({len(sel_categories)}개 분류)"):
    if len(sel_categories) == 1:
        label, code = sel_categories[0]
        all_rows, msg, params = fetch_api(api_url, api_key, begin_year, end_year, code, tab_gubun)
        results_info = [{"분류": label, "코드": code or "-", "건수": len(all_rows) if all_rows else 0, "상태": msg}]
    else:
        all_rows, results_info = fetch_multi_category(api_url, api_key, begin_year, end_year, sel_categories, tab_gubun)

# 조회 결과 요약
with st.expander("📋 조회 결과 요약", expanded=True):
    ri_df = pd.DataFrame(results_info)
    st.dataframe(ri_df, use_container_width=True, hide_index=True)

if not all_rows:
    st.error("❌ 조회된 데이터가 없습니다. 분류 조건이나 API를 변경해보세요.")
    with st.expander("🔧 디버그 정보"):
        st.write("요청 URL:", api_url)
        if len(sel_categories) == 1:
            st.write("요청 파라미터:", params)
        st.write("결과:", results_info)
    st.stop()

df = to_df(all_rows)

# ━━━ 후처리 필터 적용 ━━━
original_count = len(df)

if keyword_filter and "산업분류" in df.columns:
    keywords = [k.strip() for k in keyword_filter.split(",")]
    mask = df["산업분류"].str.contains("|".join(keywords), na=False, case=False)
    df = df[mask]

if exclude_keyword and "산업분류" in df.columns:
    ex_keywords = [k.strip() for k in exclude_keyword.split(",")]
    mask = ~df["산업분류"].str.contains("|".join(ex_keywords), na=False, case=False)
    df = df[mask]

if min_amount > 0 and "금액" in df.columns:
    df = df[df["금액"] >= min_amount]

filtered_count = len(df)

if filtered_count == 0:
    st.warning("⚠️ 필터 적용 후 데이터가 없습니다. 필터 조건을 완화하세요.")
    st.stop()

# ━━━ 디버그 ━━━
with st.expander("🔧 원본 응답 확인", expanded=False):
    st.json(all_rows[:5])
    st.caption(f"총 {len(all_rows)}건 → 필터 후 {filtered_count}건")

# ━━━ 기본 정보 ━━━
sectors = sorted(df["산업분류"].unique().tolist()) if "산업분류" in df.columns else []
years = sorted(df["연도"].unique().tolist()) if "연도" in df.columns else []
latest_year = years[-1] if years else ""
unit = df["단위"].iloc[0] if "단위" in df.columns and not df["단위"].isna().all() else "십억원"

# ━━━ 상단 메트릭 ━━━
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("조회 건수", f"{filtered_count}건" + (f" (/{original_count})" if filtered_count != original_count else ""))
m2.metric("기간", f"{years[0]}~{latest_year}" if years else "-")
m3.metric("산업분류", f"{len(sectors)}개")
m4.metric("분류 조건", f"{len(sel_categories)}개")
if "금액" in df.columns and latest_year:
    tot = df[df["연도"] == latest_year]["금액"].sum()
    m5.metric(f"{latest_year}년 합계", f"{tot:,.0f} {unit}")

st.markdown("---")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  탭
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 산업분류별 비교",
    "🥧 전체시장 대비 비중",
    "📈 연도별 추이·성장률",
    "📋 데이터 테이블",
    "📥 다운로드",
])


# ━━━ TAB 1: 산업분류별 비교 ━━━
with tab1:
    st.markdown("### 📊 산업분류별 규모 비교")

    if "금액" not in df.columns or not sectors:
        st.warning("금액 또는 산업분류 데이터가 없습니다.")
    else:
        sel_year = st.select_slider("비교 연도", options=years, value=latest_year, key="cmp_yr")
        yr_df = df[df["연도"] == sel_year].copy()

        if yr_df.empty:
            st.warning(f"{sel_year}년 데이터 없음")
        else:
            # 조회분류별 또는 구분별로 그룹
            group_col = None
            if "조회분류" in yr_df.columns and yr_df["조회분류"].nunique() > 1:
                group_col = "조회분류"
            elif "구분" in yr_df.columns and yr_df["구분"].nunique() > 1:
                group_col = "구분"

            groups = yr_df[group_col].unique().tolist() if group_col else ["전체"]

            for grp in groups:
                g = yr_df[yr_df[group_col] == grp] if group_col else yr_df
                g = g.sort_values("금액", ascending=True)
                if g.empty:
                    continue

                prefix = f"[{grp}] " if group_col else ""

                fig = px.bar(
                    g, y="산업분류", x="금액", orientation="h",
                    title=f"{prefix}{sel_year}년 산업분류별 규모 ({unit})",
                    color="산업분류", color_discrete_sequence=COLORS,
                    text="금액",
                )
                fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                fig.update_layout(height=max(350, len(g) * 50), showlegend=False, xaxis_title=f"금액 ({unit})")
                st.plotly_chart(fig, use_container_width=True)

                # 메트릭
                cols = st.columns(min(len(g), 5))
                for i, (_, row) in enumerate(g.sort_values("금액", ascending=False).iterrows()):
                    with cols[i % len(cols)]:
                        st.metric(row["산업분류"][:10], f"{row['금액']:,.0f}")
                st.markdown("---")


# ━━━ TAB 2: 전체시장 대비 비중 ━━━
with tab2:
    st.markdown("### 🥧 전체 식품시장 대비 비중 분석")

    if "금액" not in df.columns or not sectors:
        st.warning("데이터 부족")
    else:
        sel_year2 = st.select_slider("분석 연도", options=years, value=latest_year, key="pie_yr")
        yr2 = df[df["연도"] == sel_year2].copy()

        if yr2.empty:
            st.warning(f"{sel_year2}년 데이터 없음")
        else:
            group_col2 = None
            if "조회분류" in yr2.columns and yr2["조회분류"].nunique() > 1:
                group_col2 = "조회분류"
            elif "구분" in yr2.columns and yr2["구분"].nunique() > 1:
                group_col2 = "구분"

            groups2 = yr2[group_col2].unique().tolist() if group_col2 else ["전체"]

            for grp in groups2:
                g2 = yr2[yr2[group_col2] == grp] if group_col2 else yr2
                if g2.empty or g2["금액"].sum() == 0:
                    continue

                total_val = g2["금액"].sum()
                g2 = g2.copy()
                g2["비중(%)"] = (g2["금액"] / total_val * 100).round(1)
                prefix = f"[{grp}] " if group_col2 else ""

                ch1, ch2 = st.columns(2)
                with ch1:
                    fig_pie = px.pie(
                        g2, values="금액", names="산업분류",
                        title=f"{prefix}{sel_year2}년 산업분류별 비중",
                        color_discrete_sequence=COLORS, hole=0.35,
                    )
                    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                    fig_pie.update_layout(height=420)
                    st.plotly_chart(fig_pie, use_container_width=True)

                with ch2:
                    fig_tree = px.treemap(
                        g2, path=["산업분류"], values="금액",
                        title=f"{prefix}규모 트리맵",
                        color="금액", color_continuous_scale="Blues",
                    )
                    fig_tree.update_layout(height=420)
                    fig_tree.update_coloraxes(showscale=False)
                    st.plotly_chart(fig_tree, use_container_width=True)

                tbl_show = g2[["산업분류", "금액", "비중(%)"]].sort_values("금액", ascending=False).copy()
                tbl_show["금액"] = tbl_show["금액"].apply(lambda x: f"{x:,.0f} {unit}")
                tbl_show["비중(%)"] = tbl_show["비중(%)"].apply(lambda x: f"{x:.1f}%")
                st.dataframe(tbl_show.reset_index(drop=True), use_container_width=True, hide_index=True)
                st.markdown("---")

            # 비중 변화 추이
            st.markdown("#### 📈 연도별 비중 변화 추이")
            trend_df = df.copy()
            if group_col2 and len(groups2) > 1:
                g_sel = st.selectbox("구분 선택", groups2, key="area_gub")
                trend_df = df[df[group_col2] == g_sel].copy()

            yr_totals = trend_df.groupby("연도")["금액"].sum().rename("합계")
            merged = trend_df.merge(yr_totals, on="연도")
            merged["비중(%)"] = (merged["금액"] / merged["합계"] * 100).round(1)

            fig_area = px.area(
                merged.sort_values(["연도", "산업분류"]),
                x="연도", y="비중(%)", color="산업분류",
                title="산업분류별 비중 변화 추이",
                color_discrete_sequence=COLORS,
            )
            fig_area.update_layout(height=450, yaxis_title="비중 (%)", legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig_area, use_container_width=True)


# ━━━ TAB 3: 연도별 추이·성장률 ━━━
with tab3:
    st.markdown("### 📈 연도별 추이 & 성장률")

    if "금액" not in df.columns:
        st.warning("금액 데이터 없음")
    else:
        sel_sec = st.multiselect("산업분류 선택", sectors, default=sectors[:8], key="line_sec")
        filt = df[df["산업분류"].isin(sel_sec)] if sel_sec else df

        if filt.empty:
            st.warning("선택된 데이터 없음")
        else:
            fig_line = px.line(
                filt, x="연도", y="금액", color="산업분류",
                title=f"산업분류별 연도 추이 ({unit})",
                markers=True, color_discrete_sequence=COLORS,
            )
            fig_line.update_layout(height=500, yaxis_title=f"금액 ({unit})", legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig_line, use_container_width=True)

            # 성장률
            st.markdown("#### 📊 전년대비 성장률")
            growth_list = []
            for sec in sel_sec:
                s = filt[filt["산업분류"] == sec].sort_values("연도").copy()
                if len(s) > 1:
                    s["성장률(%)"] = s["금액"].pct_change() * 100
                    growth_list.append(s)

            if growth_list:
                gdf = pd.concat(growth_list).dropna(subset=["성장률(%)"])

                fig_g = px.bar(
                    gdf, x="연도", y="성장률(%)", color="산업분류",
                    barmode="group", title="전년대비 성장률 (%)",
                    color_discrete_sequence=COLORS, text="성장률(%)",
                )
                fig_g.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig_g.update_layout(height=450, legend=dict(orientation="h", y=-0.15))
                st.plotly_chart(fig_g, use_container_width=True)

                # 히트맵
                st.markdown("#### 🌡️ 성장률 히트맵")
                piv = gdf.pivot_table(index="산업분류", columns="연도", values="성장률(%)", aggfunc="first")
                fig_h = px.imshow(
                    piv.values, x=piv.columns.tolist(), y=piv.index.tolist(),
                    color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
                    title="성장률 히트맵 (%)", text_auto=".1f", aspect="auto",
                )
                fig_h.update_layout(height=max(300, len(piv) * 45))
                st.plotly_chart(fig_h, use_container_width=True)

            # 누적 바
            st.markdown("#### 📊 연도별 산업분류 구성 (누적)")
            fig_stk = px.bar(
                filt.sort_values(["연도", "산업분류"]),
                x="연도", y="금액", color="산업분류",
                title=f"연도별 산업분류 구성 ({unit})",
                color_discrete_sequence=COLORS,
            )
            fig_stk.update_layout(height=450, barmode="stack", yaxis_title=f"금액 ({unit})", legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig_stk, use_container_width=True)


# ━━━ TAB 4: 데이터 테이블 ━━━
with tab4:
    st.markdown(f"### 📋 전체 데이터 ({len(df)}건)")

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        s_f = st.multiselect("산업분류", ["전체"] + sectors, default=["전체"], key="t_sec")
    with fc2:
        if "구분" in df.columns:
            g_opts = ["전체"] + sorted(df["구분"].dropna().unique().tolist())
            g_f = st.selectbox("구분", g_opts, key="t_gub")
        else:
            g_f = "전체"
    with fc3:
        if "조회분류" in df.columns and df["조회분류"].nunique() > 1:
            q_opts = ["전체"] + sorted(df["조회분류"].dropna().unique().tolist())
            q_f = st.selectbox("조회분류", q_opts, key="t_qry")
        else:
            q_f = "전체"

    tbl = df.copy()
    if "전체" not in s_f:
        tbl = tbl[tbl["산업분류"].isin(s_f)]
    if g_f != "전체" and "구분" in tbl.columns:
        tbl = tbl[tbl["구분"] == g_f]
    if q_f != "전체" and "조회분류" in tbl.columns:
        tbl = tbl[tbl["조회분류"] == q_f]

    show = [c for c in ["연도", "산업분류", "금액", "비율", "단위", "구분", "조회분류"] if c in tbl.columns]
    st.dataframe(tbl[show].reset_index(drop=True), use_container_width=True, height=500)

    if "산업분류" in df.columns and "금액" in df.columns:
        st.markdown("#### 피벗 테이블 (연도 × 산업분류)")
        pv = tbl.pivot_table(index="연도", columns="산업분류", values="금액", aggfunc="sum")
        st.dataframe(pv.style.format("{:,.0f}", na_rep="-"), use_container_width=True)


# ━━━ TAB 5: 다운로드 ━━━
with tab5:
    st.markdown("### 📥 다운로드")

    ts = datetime.now().strftime("%Y%m%d_%H%M")

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 전체 CSV", csv,
        f"식품통계_{selected_api}_{begin_year}_{end_year}_{ts}.csv", "text/csv", use_container_width=True)

    if "산업분류" in df.columns and "금액" in df.columns:
        pv_csv = df.pivot_table(index="연도", columns="산업분류", values="금액", aggfunc="sum").to_csv().encode("utf-8-sig")
        st.download_button("📥 피벗 CSV", pv_csv,
            f"식품통계_피벗_{ts}.csv", "text/csv", use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📡 조회 정보")
    st.json({
        "API": selected_api,
        "URL": api_url,
        "기간": f"{begin_year}~{end_year}",
        "분류": [c[0] for c in sel_categories],
        "구분": tab_gubun,
        "필터_키워드": keyword_filter or "-",
        "필터_제외": exclude_keyword or "-",
        "필터_최소금액": min_amount,
    })

    st.markdown("#### 원시 JSON (상위 10건)")
    st.json(all_rows[:10])
