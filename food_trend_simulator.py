import streamlit as st
import pandas as pd
import plotly.express as px
import openai
import os

# =================================================================
# 1. 고도화된 데이터베이스(CSV) 초기화 및 로드
# =================================================================
DB_FILE = "trend_database.csv"

def get_initial_data():
    """보고서의 핵심 내용을 반영한 고도화 데이터셋"""
    return [
        # [분류, 카테고리, 항목/키워드, 수치/내용, R&D 인사이트]
        ["국내트렌드", "서바이벌 다이닝", "초가성비/효율", "경기 불황 속 생존형 소비 확산", "원가 절감형 대체 소재 및 대용량/소용량 이원화 전략"],
        ["국내트렌드", "진정성 미식", "로컬/스토리텔링", "검증된 맛과 브랜드의 진실성 중시", "원재료 산지 강조 및 무첨가/클린라벨 배합 설계"],
        ["국내트렌드", "마이 헬시 다이닝", "저당/저속노화", "헬스플레저 및 기능성 음료 수요 급증", "대체당(알룰로스 등) 최적 배합 및 혈당 관리 기능성 강화"],
        ["국내트렌드", "가성비&가치비", "푸드테크/시성비", "조리 간소화 및 기술 기반 가치 소비", "RTD 음료의 품질 유지 기술 및 무인 자판기 최적화"],
        
        ["소비자지표", "인구구조", "1인 가구 비중", "36.1", "소포장, 원핸드(One-hand) 패키징 음료 개발 필수"],
        ["소비자지표", "인구구조", "고령인구 비중", "20.3", "실버 세대용 고단백, 저작 용이성 강화 음료 설계"],
        ["소비자지표", "소비선호", "제로슈거 선호도", "85.0", "탄산 외 티, 커피, 유음료 전 영역 제로화 적용"],
        
        ["글로벌", "미국", "Wellness AI", "AI 기반 개인화 맞춤형 건강 음료", "어댑토젠 및 천연 에너지 부스팅 소재 활용"],
        ["글로벌", "일본", "인력부족 대응", "조리 공정 최소화 및 장기 보관 기술", "살균 공정 최적화를 통한 유통기한 연장 및 품질 보존"],
        ["글로벌", "중국", "건강 가성비", "전통 약재의 현대적 음료화(중식 미식)", "한방 소재의 쓴맛 마스킹 및 현대적 풍미 구현"],
        ["글로벌", "베트남", "디지털 전환", "배달 플랫폼 최적화 음료 소비", "배달 중 상온 안정성 및 층분리 방지 증점제 설계"]
    ]

def load_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(get_initial_data(), 
                          columns=["Classification", "Category", "Item", "Value_Detail", "RD_Insight"])
        df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
    return pd.read_csv(DB_FILE)

# =================================================================
# 2. AI R&D 엔진
# =================================================================
def generate_beverage_report(row, target, api_key):
    client = openai.OpenAI(api_key=api_key)
    
    prompt = f"""
    당신은 20년 경력의 시니어 식품 공학 전문가입니다. 다음 데이터를 바탕으로 신제품 음료를 설계하세요.
    - 트렌드: {row['Category']} ({row['Item']})
    - 상세내용: {row['Value_Detail']}
    - R&D 가이드: {row['RD_Insight']}
    - 타겟: {target}

    [출력 요구사항]
    1. 제품 컨셉 및 명칭
    2. 표준 배합비 표: [원료명, 배합비(%), 사용 목적, 용도, 용법, 사용주의사항] 포함
    3. 핵심 기술 (공법, 보존성 등)
    4. 마케팅 소구점
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "시니어 식품 기술사로서 답변하십시오."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"연동 에러: {e}"

# =================================================================
# 3. UI 레이아웃
# =================================================================
def main():
    st.set_page_config(page_title="Food Trend Simulator", layout="wide")
    df = load_db()

    # 사이드바
    st.sidebar.title("🛠 R&D Control Center")
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    
    # CSV 다운로드 링크 제공
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 데이터 관리")
    csv_data = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.sidebar.download_button(
        label="트렌드 DB(CSV) 다운로드",
        data=csv_data,
        file_name="food_trend_database.csv",
        mime="text/csv",
        help="현재 시스템이 사용하는 모든 데이터를 CSV로 내려받습니다."
    )

    # 메인 화면
    st.title("🥤 BRK LAB: 신제품 개발 시뮬레이터")
    st.caption("2025-2026 식품외식 트렌드 보고서 기반 인텔리전스 시스템")

    tab1, tab2 = st.tabs(["📊 데이터 센터", "🧪 레시피 시뮬레이터"])

    with tab1:
        st.subheader("데이터베이스 현황")
        st.dataframe(df, use_container_width=True)
        
        # 시각화: 통계 지표 위주
        stats = df[df['Classification'] == '소비자지표'].copy()
        stats['Value'] = stats['Value_Detail'].astype(float)
        fig = px.bar(stats, x='Item', y='Value', color='Item', title="주요 소비자 통계 (비중 %)")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("트렌드 기반 제품 설계")
        c1, c2 = st.columns(2)
        with c1:
            selected_cat = st.selectbox("기반 트렌드 선택", df['Category'].unique())
            target = st.selectbox("타겟 고객층", ["5060 뉴그레이", "MZ세대 1인 가구", "헬스플레저(건강즐거움)"])
        
        with c2:
            row_data = df[df['Category'] == selected_cat].iloc[0]
            st.info(f"**R&D 시사점:** {row_data['RD_Insight']}")

        if st.button("🚀 전문가 배합비 생성"):
            if not api_key:
                st.error("OpenAI API Key를 입력해주세요.")
            else:
                with st.spinner("배합표 및 마케팅 전략 설계 중..."):
                    report = generate_beverage_report(row_data, target, api_key)
                    st.markdown("---")
                    st.markdown(report)

if __name__ == "__main__":
    main()
