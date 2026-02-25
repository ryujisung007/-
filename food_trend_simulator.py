import streamlit as st
import pandas as pd
import plotly.express as px
import openai
import os

# =================================================================
# 1. 데이터베이스 관리 및 업데이트 로직
# =================================================================
DB_FILE = "food_trend_database.csv"

def get_default_data():
    """기본 초기 데이터셋 (파일이 없을 경우 생성)"""
    return [
        ["음료시장분석", "탄산음료", "제로 시장 비중", "탄산 내 제로 비중 약 25% 돌파", "감미료 최적 배합 및 바디감 보완 기술 필수"],
        ["음료시장분석", "RTD커피", "프리미엄화", "고함량 원두 추출물 시장 확대", "살균 시 향 손실 최소화 및 유화 안정성 설계"],
        ["소비자지표", "유통채널", "편의점(CVS)", "음료 구매의 45%가 CVS에서 발생", "CVS 특화 소용량 패키징 및 시인성 강화"],
        ["국내트렌드", "마이 헬시", "저속노화", "혈당 스파이크 방지 음료 수요 증가", "알룰로스 등 저혈당 지수 감미료 배합 연구"],
        ["글로벌", "미국/중국", "K-음료 수출", "전통 발효 음료 수출 증가", "수출국별 첨가물 규정 준수 및 유통기한 연장"]
    ]

def load_data():
    """데이터를 로드합니다. 업로드된 파일이 있으면 우선순위를 가집니다."""
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except:
            return pd.DataFrame(get_default_data(), columns=["Classification", "Category", "Item", "Value_Detail", "RD_Insight"])
    else:
        df = pd.DataFrame(get_default_data(), columns=["Classification", "Category", "Item", "Value_Detail", "RD_Insight"])
        df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
        return df

# =================================================================
# 2. AI R&D 엔진
# =================================================================
def generate_expert_report(row, target, api_key):
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
    식품 공학 전문가로서 다음 데이터를 바탕으로 음료를 설계하세요.
    - 데이터: {row['Category']} ({row['Item']}) / {row['Value_Detail']}
    - R&D 인사이트: {row['RD_Insight']}
    - 타겟: {target}
    표준 배합비 표(원료명, %, 사용 목적, 용법, 주의사항)를 포함한 리포트를 작성하세요.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "시니어 식품 기술사로서 답변하십시오."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"연동 실패: {e}"

# =================================================================
# 3. UI 및 인터랙션
# =================================================================
def main():
    st.set_page_config(page_title="Food Trend Intelligence", layout="wide")
    
    # 세션 상태에 데이터 저장 (업데이트 반영용)
    if 'main_df' not in st.session_state:
        st.session_state.main_df = load_data()

    # 사이드바
    st.sidebar.title("🧬 R&D Control Center")
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔼 데이터 업데이트 (CSV 업로드)")
    uploaded_file = st.sidebar.file_uploader("수정된 CSV 파일을 업로드하세요", type="csv")
    
    if uploaded_file is not None:
        new_df = pd.read_csv(uploaded_file)
        # 5칼럼 양식 검증
        if list(new_df.columns) == ["Classification", "Category", "Item", "Value_Detail", "RD_Insight"]:
            st.session_state.main_df = new_df
            # 로컬 환경인 경우 파일 저장 (GitHub 연동 시 로컬 저장본이 업데이트됨)
            new_df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
            st.sidebar.success("데이터베이스가 성공적으로 업데이트되었습니다!")
        else:
            st.sidebar.error("CSV 양식이 올바르지 않습니다. (5칼럼 확인 필요)")

    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 데이터 내보내기")
    csv_bytes = st.session_state.main_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.sidebar.download_button(label="현재 DB 다운로드", data=csv_bytes, file_name="food_trend_database.csv", mime="text/csv")

    # 메인 화면
    st.title("🥤식품정보원 LAB: 신제품 개발 시뮬레이터")
    
    tab1, tab2 = st.tabs(["📊 통합 트렌드 DB", "🧪 레시피 시뮬레이터"])

    with tab1:
        st.subheader("카테고리별 트렌드 분석")
        
        # 필터 UI: 카테고리별 선택 출력
        all_categories = st.session_state.main_df['Category'].unique().tolist()
        selected_categories = st.multiselect("출력할 카테고리를 선택하세요", all_categories, default=all_categories)
        
        # 필터링 결과 출력
        filtered_df = st.session_state.main_df[st.session_state.main_df['Category'].isin(selected_categories)]
        st.dataframe(filtered_df, use_container_width=True)
        
        # 시각화
        if not filtered_df.empty:
            fig = px.pie(filtered_df, names='Classification', title="분류별 데이터 분포")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("데이터 기반 제품 설계")
        c1, c2 = st.columns(2)
        with c1:
            # 현재 로드된 데이터의 카테고리만 출력
            selected_cat = st.selectbox("분석 대상 카테고리 선택", st.session_state.main_df['Category'].unique())
            target = st.selectbox("타겟 고객 설정", ["5060 뉴그레이", "MZ세대 헬스플레저", "1인 가구"])
        
        with c2:
            row_data = st.session_state.main_df[st.session_state.main_df['Category'] == selected_cat].iloc[0]
            st.info(f"**R&D Insight:** {row_data['RD_Insight']}")

        if st.button("🚀 전문가 배합비 생성"):
            if not api_key:
                st.error("API 키를 입력해주세요.")
            else:
                with st.spinner("전문가 엔진 가동 중..."):
                    report = generate_expert_report(row_data, target, api_key)
                    st.markdown("---")
                    st.markdown(report)

if __name__ == "__main__":
    main()
