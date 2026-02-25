"""
📊 식품산업통계 조회 시스템 v2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
aT 식품산업정보 API (atfis.or.kr)
- 산업분류별 비교 분석
- 전체 식품시장 대비 비중
- 연도별 추이 & 성장률
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

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
</style>
""", unsafe_allow_html=True)

# ━━━ API 설정 ━━━
API_URL = "https://www.atfis.or.kr/home/api/food/stats/basic.do"
DEFAULT_API_KEY = "z9JeRfaB44up466XHs+5pTcV31n58LqRkSHZ8H66xbw="

CATEGORY_MAP = {
    "DOMESTIC": "국내 식품산업",
    "EXPORT": "식품 수출",
    "IMPORT": "식품 수입",
}

COLORS = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel2


# ━━━ API 호출 ━━━
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stats(api_key, begin_year, end_year, category=None):
    params = {
        "apiKey": api_key,
        "beginYear": str(begin_year),
        "endYear": str(end_year),
    }
    if category:
        params["category1"] = category

    try:
        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, list):
            return data, "정상"
        if isinstance(data, dict):
            for key in ["data", "body", "items", "list", "result"]:
                if key in data and isinstance(data[key], list):
                    return data[key], "정상"
            if "fdmsId" in data:
                return [data], "정상"
            msg = data.get("message", data.get("msg", str(data)))
            return None, f"API 오류: {msg}"
        return None, f"예상치 못한 응답: {type(data)}"

    except requests.exceptions.Timeout:
        return None, "응답 시간 초과"
    except requests.exceptions.ConnectionError:
        return None, "서버 연결 실패"
    except Exception as e:
        return None, f"오류: {e}"


def fetch_all_categories(api_key, begin_year, end_year):
    all_rows = []
    errors = {}

    # 카테고리 없이 전체 조회 시도
    rows, msg = fetch_stats(api_key, begin_year, end_year, None)
    if rows and len(rows) > 5:
        return rows, errors

    # 카테고리별 개별 조회
    for code, name in CATEGORY_MAP.items():
        rows, msg = fetch_stats(api_key, begin_year, end_year, code)
        if rows:
            all_rows.extend(rows)
        else:
            errors[name] = msg
        time.sleep(0.3)

    return all_rows, errors


def to_df(rows):
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    col_map = {
        "fdmsId": "ID", "fdmsYear": "연도", "fdmsSectorCd": "산업분류",
        "fdmsNumber": "금액", "fdmsRatio": "비율", "fdmsUnit": "단위",
        "fdmsIndustryGubun": "구분코드",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)

    if "연도" in df.columns:
        df["연도"] = df["연도"].astype(str)
    if "금액" in df.columns:
        df["금액"] = pd.to_numeric(df["금액"], errors="coerce")
    if "비율" in df.columns:
        df["비율"] = pd.to_numeric(df["비율"], errors="coerce")
    if "구분코드" in df.columns:
        df["구분"] = df["구분코드"].map(CATEGORY_MAP).fillna(df["구분코드"])

    return df.sort_values(["연도", "산업분류"]).reset_index(drop=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  사이드바
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("## 📊 조회 설정")
    st.markdown("---")

    api_key = st.text_input("🔑 API 인증키", value=DEFAULT_API_KEY, type="password")

    st.markdown("---")
    cur = datetime.now().year
    c1, c2 = st.columns(2)
    begin_year = c1.number_input("시작연도", 2000, cur, 2012)
    end_year = c2.number_input("종료연도", 2000, cur, cur - 1)

    st.markdown("---")
    st.markdown("**카테고리**")
    sel_cats = []
    for code, name in CATEGORY_MAP.items():
        if st.checkbox(name, value=(code == "DOMESTIC"), key=f"c_{code}"):
            sel_cats.append(code)
    fetch_all = st.checkbox("전체 조회 (모든 카테고리)", value=True)

    st.markdown("---")
    run = st.button("🚀 조회 실행", use_container_width=True, type="primary")

    st.markdown("---")
    st.caption("📡 aT 식품산업정보 (atfis.or.kr)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  메인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("# 📊 식품산업통계 분석 시스템")
st.markdown("산업분류별 비교 · 전체 식품시장 대비 비중 · 연도별 추이 분석")
st.markdown("---")

if not run:
    st.info("👈 사이드바에서 조건 설정 후 **[조회 실행]** 버튼을 누르세요.")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        ### 주요 기능
        - **산업분류별 비교** — 협의/광의 식품산업, 외식산업 등 규모 비교
        - **전체 식품시장 대비** — 각 분류가 전체에서 차지하는 비중(%)
        - **연도별 추이** — 시계열 라인차트 + 전년대비 성장률
        - **성장률 히트맵** — 산업분류 × 연도 한눈에 비교
        """)
    with col_b:
        st.markdown("""
        ### API 정보
        | 항목 | 내용 |
        |---|---|
        | 엔드포인트 | `atfis.or.kr/.../basic.do` |
        | 파라미터 | beginYear, endYear, category1 |
        | 카테고리 | DOMESTIC, EXPORT, IMPORT |
        | 응답필드 | 연도, 산업분류, 금액, 비율, 단위 |
        """)
    st.stop()


# ━━━ 데이터 수집 ━━━
with st.spinner("📡 데이터 조회 중..."):
    if fetch_all:
        all_rows, errs = fetch_all_categories(api_key, begin_year, end_year)
        for k, v in errs.items():
            st.warning(f"⚠️ {k}: {v}")
    else:
        all_rows = []
        for cat in sel_cats:
            rows, msg = fetch_stats(api_key, begin_year, end_year, cat)
            if rows:
                all_rows.extend(rows)
            else:
                st.warning(f"⚠️ {CATEGORY_MAP.get(cat, cat)}: {msg}")

if not all_rows:
    st.error("❌ 조회된 데이터가 없습니다.")
    st.stop()

df = to_df(all_rows)

with st.expander("🔧 원본 응답 확인", expanded=False):
    st.json(all_rows[:5])
    st.caption(f"총 {len(all_rows)}건")

sectors = df["산업분류"].unique().tolist() if "산업분류" in df.columns else []
years = sorted(df["연도"].unique().tolist()) if "연도" in df.columns else []
latest_year = years[-1] if years else ""
unit = df["단위"].iloc[0] if "단위" in df.columns and not df["단위"].isna().all() else ""

# 상단 메트릭
m1, m2, m3, m4 = st.columns(4)
m1.metric("조회 건수", f"{len(df)}건")
m2.metric("기간", f"{years[0]}~{latest_year}" if years else "-")
m3.metric("산업분류", f"{len(sectors)}개")
if "금액" in df.columns and latest_year:
    tot = df[df["연도"] == latest_year]["금액"].sum()
    m4.metric(f"{latest_year}년 합계", f"{tot:,.0f} {unit}")

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
            # 구분별로 분리
            gubuns = yr_df["구분"].unique().tolist() if "구분" in yr_df.columns else ["전체"]

            for gubun in gubuns:
                g = yr_df[yr_df["구분"] == gubun] if gubun != "전체" else yr_df
                g = g.sort_values("금액", ascending=True)
                if g.empty:
                    continue

                prefix = f"[{gubun}] " if gubun != "전체" else ""

                fig = px.bar(
                    g, y="산업분류", x="금액", orientation="h",
                    title=f"{prefix}{sel_year}년 산업분류별 규모 ({unit})",
                    color="산업분류", color_discrete_sequence=COLORS,
                    text="금액",
                )
                fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                fig.update_layout(
                    height=max(350, len(g) * 50),
                    showlegend=False, xaxis_title=f"금액 ({unit})",
                )
                st.plotly_chart(fig, use_container_width=True)

                # 메트릭 카드
                cols = st.columns(min(len(g), 5))
                for i, (_, row) in enumerate(g.sort_values("금액", ascending=False).iterrows()):
                    with cols[i % len(cols)]:
                        st.metric(row["산업분류"], f"{row['금액']:,.0f} {unit}")
                st.markdown("---")


# ━━━ TAB 2: 전체시장 대비 ━━━
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
            gubuns2 = yr2["구분"].unique().tolist() if "구분" in yr2.columns else ["전체"]

            for gubun in gubuns2:
                g2 = yr2[yr2["구분"] == gubun] if gubun != "전체" else yr2
                if g2.empty or g2["금액"].sum() == 0:
                    continue

                total_val = g2["금액"].sum()
                g2 = g2.copy()
                g2["비중(%)"] = (g2["금액"] / total_val * 100).round(1)
                prefix = f"[{gubun}] " if gubun != "전체" else ""

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

                # 비중 표
                tbl = g2[["산업분류", "금액", "비중(%)"]].sort_values("금액", ascending=False).copy()
                tbl["금액"] = tbl["금액"].apply(lambda x: f"{x:,.0f} {unit}")
                tbl["비중(%)"] = tbl["비중(%)"].apply(lambda x: f"{x:.1f}%")
                st.dataframe(tbl.reset_index(drop=True), use_container_width=True, hide_index=True)
                st.markdown("---")

            # 비중 변화 추이 (Stacked Area)
            st.markdown("#### 📈 연도별 비중 변화 추이")

            if "구분" in df.columns and len(gubuns2) > 1:
                g_sel = st.selectbox("구분 선택", gubuns2, key="area_gub")
                trend_df = df[df["구분"] == g_sel].copy()
            else:
                trend_df = df.copy()

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
        sel_sec = st.multiselect("산업분류 선택", sectors, default=sectors[:5], key="line_sec")
        filt = df[df["산업분류"].isin(sel_sec)] if sel_sec else df

        if filt.empty:
            st.warning("선택된 데이터 없음")
        else:
            # 라인차트
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
                st.markdown("#### 🌡️ 성장률 히트맵 (산업분류 × 연도)")
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

    fc1, fc2 = st.columns(2)
    with fc1:
        s_f = st.multiselect("산업분류", ["전체"] + sectors, default=["전체"], key="t_sec")
    with fc2:
        if "구분" in df.columns:
            g_f = st.selectbox("구분", ["전체"] + df["구분"].unique().tolist(), key="t_gub")

    tbl = df.copy()
    if "전체" not in s_f:
        tbl = tbl[tbl["산업분류"].isin(s_f)]
    if "구분" in df.columns and g_f != "전체":
        tbl = tbl[tbl["구분"] == g_f]

    show = [c for c in ["연도", "산업분류", "금액", "비율", "단위", "구분"] if c in tbl.columns]
    st.dataframe(tbl[show].reset_index(drop=True), use_container_width=True, height=500)

    if "산업분류" in df.columns and "금액" in df.columns:
        st.markdown("#### 피벗 테이블")
        pv = tbl.pivot_table(index="연도", columns="산업분류", values="금액", aggfunc="sum")
        st.dataframe(pv.style.format("{:,.0f}", na_rep="-"), use_container_width=True)


# ━━━ TAB 5: 다운로드 ━━━
with tab5:
    st.markdown("### 📥 다운로드")

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 전체 CSV", csv,
        f"식품산업통계_{begin_year}_{end_year}.csv", "text/csv", use_container_width=True)

    if "산업분류" in df.columns and "금액" in df.columns:
        pv_csv = df.pivot_table(index="연도", columns="산업분류", values="금액", aggfunc="sum").to_csv().encode("utf-8-sig")
        st.download_button("📥 피벗 CSV", pv_csv,
            f"식품산업_피벗_{begin_year}_{end_year}.csv", "text/csv", use_container_width=True)

    st.markdown("---")
    st.json(all_rows[:10])
    st.caption(f"총 {len(all_rows)}건 중 10건")
