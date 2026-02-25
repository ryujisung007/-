# 🧪 Food R&D Platform

식품 R&D 교육용 멀티페이지 Streamlit 앱

## 실행 방법

```bash
cd food_rd_app
pip install -r requirements.txt
streamlit run app.py
```

## 폴더 구조

```
food_rd_app/
├── app.py                     ← 메인 대시보드
├── requirements.txt
├── data/
│   ├── __init__.py
│   └── common.py              ← 공통 데이터 & 유틸리티
├── pages/
│   ├── 1_📈_매출추이.py       ← 유형별 매출 트렌드
│   ├── 2_🏷️_브랜드분석.py     ← 브랜드별 연도 비교
│   ├── 3_🤖_AI제품카드.py     ← AI 배합비 생성
│   ├── 4_⚗️_배합비설계.py     ← 배합비 상세 뷰
│   ├── 5_🏭_공정리스크.py     ← 제조공정 & HACCP
│   ├── 6_📋_규제서류.py       ← 품목제조보고서
│   └── 7_✏️_배합연습.py       ← CSV 배합비 연습
└── saved/                     ← 학생 배합비 저장 폴더
```

## Streamlit Cloud 배포

1. GitHub에 이 폴더를 push
2. https://share.streamlit.io 에서 새 앱 생성
3. Main file path: `food_rd_app/app.py`
4. 배포 완료 → 여러 학생이 동시 접속 가능

## 동시 접속

- Streamlit은 **각 사용자별 세션이 자동 분리**됩니다
- 학생 A가 선택한 제품과 학생 B가 선택한 제품은 서로 독립
- 배합비 저장은 서버 `saved/` 폴더에 JSON으로 저장 (학생 이름 포함)
