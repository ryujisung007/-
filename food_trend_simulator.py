import streamlit as st
import pandas as pd
import plotly.express as px
import openai
import os

# =================================================================
# 1. 보고서 2종(외식+음료세분화) 통합 데이터베이스
# =================================================================
DB_FILE = "food_trend_database.csv"

def initialize_database():
    """사용자가 제공한 엑셀 양식(5칼럼)에 맞춰 데이터를 정밀 보강합니다."""
    # 시니어 전문가가 분석한 통합 데이터셋
    data = [
        # [분류, 카테고리, 항목, 수치/내용, R&D 인사이트]
        # --- [신규] 가공식품 음료시장 세분화 데이터 반영 ---
        ["음료시장분석", "탄산음료", "제로 시장 비중", "탄산 내 제로 비중 약 25% 돌파(2023)", "대체당(수크랄로스, 아세설팜K) 사용 시 뒷맛 마스킹 및 바디감 보완 필수"],
        ["음료시장분석", "RTD커피", "프리미엄화", "고함량 원두 추출물 및 콜드브루 시장 확대", "살균 시 향 손실 최소화 기술(HTST 등) 및 유지방 분리 방지 유화 설계"],
        ["음료시장분석", "과채음료", "저당/기능성 주스", "100% 주스 감소세 및 당류 저감 주스 급성장", "식이섬유 또는 프로바이오틱스 첨가를 통한 건강기능성 소구점 강화"],
        ["음료시장분석", "기능성음료", "아르기닌/에너지", "아르기닌&비타B 고함량 음료 인기", "고농도 아르기닌 특유의 쓴맛/아린맛 제어를 위한 유기산 및 향료 최적화"],
        ["음료시장분석", "다류(Tea)", "전통차 RTD", "보리차, 옥수수차 등 곡물차 시장 지속 성장", "원물 볶음 공정 표준화를 통한 풍미 일관성 확보 및 침전물 제어"],
        
        # --- 기존 외식 트렌드 및 소비자 데이터 유지/강화 ---
        ["소비자지표", "유통채널", "편의점(CVS) 비중", "음료 구매의 약 45%가 CVS에서 발생", "CVS 특화 소용량(250~350ml) 패키징 및 시인성 높은 라벨 디자인"],
        ["소비자지표", "가구구조", "1인 가구", "36.1%로 국민 2.8명 중 1명 꼴", "개봉 후 보관이 용이한 캡(Cap)형 파우치 및 소분 포장 기술"],
        ["국내트렌드", "마이 헬시", "저속노화", "혈당 스파이크 방지 음료 수요 증가", "알룰로스, 타가토스 등 저혈당 지수(GI) 감미료 배합 연구"],
        ["국내트렌드", "서바이벌", "초가성비", "PB 제품 및 벌크형(1.5L 이상) 선호", "원가 경쟁력 확보를 위한 농축액 직수입 및 공정 자동화"],
        ["글로벌", "미국/중국", "K-음료 수출", "식초 음료 및 전통 발효 음료 수출 증가", "수출국별 첨가물 허용 기준(Codex) 준수 및 유통기한 연장 공법(HPP 등)"],
    ]
    
    df = pd.DataFrame(data, columns=["Classification", "Category", "Item", "Value_Detail", "RD_Insight"])
    # 엑셀 호환을 위해 utf-8-sig 사용
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
    return df

# =================================================================
# 2. AI R&D 전문가 엔진 (gpt-4o-mini)
# =================================================================
def get_ai_response(row, target, api_key):
    client = openai.OpenAI(api_key=api_key)
    
    prompt = f"""
    당신은 20년 경력의 시니어 식품 공학 전문가(박사)입니다. 다음 데이터를 기반으로 신제품 음료를 설계하세요.
    
    [데이터 정보]
    - 분류: {row['Classification']}
    - 카테고리: {row['Category']}
    - 상세지표: {row['Item']} ({row['Value_Detail']})
    - R&D 인사이트: {row['RD_Insight']}
    - 타겟 고객: {target}

    [작성 요구사항]
    1. 제품명 및 컨셉: 트렌드를 관통하는 독창적인 아이디어.
    2. 표준 배합비: [원료명, 배합비(%), 사용 목적, 용도, 용법, 사용주의사항] 표 형식으로 작성.
    3. 식품공학적 가이드: 가공 공정, 유화 안정성, 살균 조건 등 기술적 조언.
    4. 마케팅 포인트: 타겟 계층의 페르소나를 공략할 소구점.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "시니어 식품 기술사 수준의 전문 답변을 제공하십시오."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"연동 실패: {e}"

# =================================================================
# 3. Streamlit UI 및 다운로드 로직
# =================================================================
def main():
    st.set_page_config(page_title="BRK Food R&D Simulator", layout="wide")
    
    # 데이터 초기화 및 로드
    if not os.path.exists(DB_FILE):
        df = initialize_database()
    else:
        df = pd.read_csv(DB_FILE)

    # 사이드바
    st.sidebar.title("🧬 R&D Dashboard")
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    
    # 다운로드 링크 (수정된 데이터를 언제든 다운로드 가능)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 데이터 내보내기")
    csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.sidebar.download_button(
        label="최신 트렌드 DB 다운로드",
        data=csv,
        file_name="food_trend_database.csv",
        mime="text/csv",
        help="정리된 5칼럼 양식의 CSV를 다운로드합니다."
    )

    # 메인 섹션
    st.title("🥤 식품/음료 트렌드 통합 시뮬레이터")
    st.markdown("본 시스템은 **가공식품 음료 세분시장 데이터**와 **2026 외식 트렌드**를 통합하여 분석합니다.")

    tab1, tab2 = st.tabs(["📊 통합 데이터 시트", "👨‍🔬 신제품 기획 시뮬레이터"])

    with tab1:
        st.subheader("5칼럼 통합 트렌드 데이터베이스")
        st.dataframe(df, use_container_width=True)
        
        # 시각적 분포 확인
        st.markdown("---")
        fig = px.sunburst(df, path=['Classification', 'Category'], title="시장 데이터 구조 시각화")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("데이터 기반 신제품 배합 설계")
        c1, c2 = st.columns(2)
        with c1:
            selected_cat = st.selectbox("분석 대상 트렌드/품목 선택", df['Category'].unique())
            target = st.selectbox("타겟 고객층 설정", ["5060 뉴그레이", "MZ세대 헬스플레저", "1인 가구 직장인", "고카페인 수요 수험생"])
        
        with c2:
            current_row = df[df['Category'] == selected_cat].iloc[0]
            st.success(f"📌 **전문가 인사이트:** {current_row['RD_Insight']}")

        if st.button("🚀 신제품 전문가 리포트 생성"):
            if not api_key:
                st.error("API 키를 입력해주세요.")
            else:
                with st.spinner("AI 시니어 연구원이 레시피를 설계 중입니다..."):
                    report = get_ai_response(current_row, target, api_key)
                    st.markdown("---")
                    st.markdown(report)

if __name__ == "__main__":
    main()
