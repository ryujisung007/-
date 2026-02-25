"""
🧪 Food R&D Platform — 메인 대시보드
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from data.common import *

st.set_page_config(page_title="Food R&D Platform", page_icon="🧪", layout="wide")

# 학생 이름 세션
if "student_name" not in st.session_state:
    st.session_state.student_name = ""

st.markdown("# 🧪 Food R&D Platform")
st.markdown("**매출 분석 → AI 배합비 → 공정 설계 → 규제 검토 → 배합 연습**")
st.markdown("---")

# 학생 이름 입력
with st.sidebar:
    st.markdown("### 👤 사용자 정보")
    name = st.text_input("이름 (저장 시 사용)", value=st.session_state.student_name, placeholder="예: 홍길동")
    if name:
        st.session_state.student_name = name
        st.success(f"👋 {name}님 환영합니다!")
    st.markdown("---")
    st.markdown("### 📂 페이지 안내")
    st.markdown("""
    왼쪽 사이드바 메뉴에서 이동:
    1. **📈 매출추이** — 유형별 매출 트렌드
    2. **🏷️ 브랜드** — 브랜드별 연도 비교
    3. **🤖 AI카드** — AI 배합비 생성
    4. **⚗️ 배합비** — 상세 배합표
    5. **🏭 공정** — 제조공정 & 리스크
    6. **📋 규제** — 서류 & 허가
    7. **✏️ 배합연습** — CSV 배합비 작성
    """)

# 대시보드 메트릭
sorted_cats = get_sorted_categories()
total_2024 = sum(SALES_DATA[c]["2024"] for c in SALES_DATA)

c1, c2, c3, c4 = st.columns(4)
c1.metric("📊 음료 유형", f"{len(SALES_DATA)}개")
c2.metric("🏷️ 브랜드 수", f"{sum(len(v) for v in BRAND_DATA.values())}개")
c3.metric("💰 2024 총매출", f"{total_2024/10000:,.0f}만 백만원")
c4.metric("📁 저장된 배합비", f"{len(load_saved_formulas())}건")

st.markdown("---")

# 매출 순위 요약
st.markdown("### 🏆 2024 음료 매출 순위")
cols = st.columns(5)
for i, cat in enumerate(sorted_cats[:5]):
    val = SALES_DATA[cat]["2024"]
    prev = SALES_DATA[cat]["2023"]
    growth = (val - prev) / prev * 100
    with cols[i]:
        st.metric(f"#{i+1} {cat}", f"{val/10000:.0f}만", f"{growth:+.1f}%")

st.markdown("---")

# 워크플로우 안내
st.markdown("### 🔄 학습 워크플로우")
st.markdown("""
```
📈 매출 분석  →  🏷️ 브랜드 선택  →  🤖 AI 배합비 생성
                                          ↓
📋 규제 검토  ←  🏭 공정 설계    ←  ⚗️ 배합비 상세
                                          ↓
                               ✏️ 배합비 CSV 연습 (직접 작성·검증·저장)
```
""")

st.info("👈 **왼쪽 사이드바**에서 각 페이지로 이동하세요. 여러 명이 동시에 접속해도 각자 세션이 분리됩니다.")
