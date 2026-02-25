"""
🍹 퍼플비타 스파클링 — 배합 최적화 시뮬레이터
실행: pip install streamlit plotly pandas → streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time, copy
from datetime import datetime

st.set_page_config(page_title="퍼플비타 배합 최적화", page_icon="🍹", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#13102A,#1E1345);border-right:1px solid #2D2555}
section[data-testid="stSidebar"] .stSlider label{color:#C4B5FD!important;font-size:13px}
div[data-testid="stMetric"]{background:#13102A;border:1px solid #2D2555;border-radius:12px;padding:12px 16px}
div[data-testid="stMetric"] label{color:#7C6FA8!important}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#E9D5FF!important}
.stTabs [data-baseweb="tab-list"]{gap:4px;background:#13102A;border-radius:10px;padding:4px}
.stTabs [data-baseweb="tab"]{border-radius:8px;color:#7C6FA8;font-weight:600;font-size:13px}
.stTabs [aria-selected="true"]{background:rgba(124,58,237,0.25)!important;color:#C4B5FD!important}
.stButton>button{background:linear-gradient(135deg,#7C3AED,#A855F7)!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:700!important;padding:10px 24px!important}
.stButton>button:hover{opacity:0.9}
</style>""", unsafe_allow_html=True)

# ── 기준값 ──
BASE_F = {"sugar":70,"stevia":0.5,"erythritol":0,"monk":0,"citric":3.0,"citNa":0.5,"malic":0,"vitC":500,"vitD":0,"zinc":0,"fiber":0,"greenTea":0,"color":2.0,"aroma_ml":1.5,"co2":2.75}
BASE_S = {"종합기호도":6.64,"향 기호도":6.63,"단맛 기호도":6.19,"신맛 기호도":6.96,"뒷맛":6.48,"재구매의향":6.73,"시판비교":6.27}
BASE_JAR = {"단맛":56,"신맛":75,"향":62,"청량감":61}

def clamp(v,lo,hi): return max(lo,min(hi,v))

def simulate(f):
    b=BASE_F
    base_sw=b["sugar"]+b["stevia"]*300+b["erythritol"]*0.7+b["monk"]*250
    new_sw=f["sugar"]+f["stevia"]*300+f["erythritol"]*0.7+f["monk"]*250
    sw_r=new_sw/max(base_sw,1)
    base_ac=b["citric"]+b["citNa"]*0.3+b["malic"]*0.9
    new_ac=f["citric"]+f["citNa"]*0.3+f["malic"]*0.9
    ac_r=new_ac/max(base_ac,0.1)
    bal_d=abs(new_sw/(max(new_ac,0.1)*100)-base_sw/(base_ac*100))
    func=(0.1 if f["vitC"]>0 else 0)+(0.15 if f["vitD"]>0 else 0)+(0.1 if f["zinc"]>0 else 0)+(0.12 if f["fiber"]>0 else 0)+(0.08 if f["greenTea"]>0 else 0)
    low_s=max(0,(60-f["sugar"])*0.005) if f["sugar"]<=60 else 0
    sw_n=sum([f["sugar"]>0,f["stevia"]>0,f["erythritol"]>0,f["monk"]>0])
    blend=0.25 if sw_n>=3 else (0.1 if sw_n>=2 else 0)
    ac_bl=0.15 if (f["citric"]>0 and f["malic"]>0) else 0
    co2_d=f["co2"]-b["co2"]; co2_b=min(co2_d*0.3,0.5) if co2_d>0 else co2_d*0.4
    bs=BASE_S
    sw_o=max(0,1-((sw_r-1)*2)**2)*0.8+0.2
    sweet=clamp(bs["단맛 기호도"]+(sw_o-0.8)*3+blend+low_s,1,9)
    so_o=max(0,1-((ac_r-0.85)*3)**2)
    sour=clamp(bs["신맛 기호도"]+(so_o-0.5)*1.5+ac_bl,1,9)
    ar_r=f["aroma_ml"]/max(b["aroma_ml"],0.1)
    aroma=clamp(bs["향 기호도"]+(ar_r-1)*0.8-abs(ar_r-1.2)*0.3,1,9)
    ep=max(0,(f["erythritol"]-15)*0.05)
    after=clamp(bs["뒷맛"]+(1-bal_d*0.5)*0.5+blend-ep+ac_bl,1,9)
    overall=clamp(bs["종합기호도"]+(sweet-bs["단맛 기호도"])*0.25+(sour-bs["신맛 기호도"])*0.2+(after-bs["뒷맛"])*0.2+func*0.3+co2_b*0.3+low_s*0.5+blend*0.3,1,9)
    repur=clamp(overall*0.6+sweet*0.15+after*0.15+func*2+low_s*3,1,9)
    market=clamp(overall*0.5+func*3+low_s*2+co2_b*0.5-0.3,1,9)
    scores={"종합기호도":round(overall,2),"향 기호도":round(aroma,2),"단맛 기호도":round(sweet,2),"신맛 기호도":round(sour,2),"뒷맛":round(after,2),"재구매의향":round(repur,2),"시판비교":round(market,2)}
    sj=clamp(round(56+(1-abs(sw_r-1))*30+blend*10),20,95); sl=round((1-sw_r)*50) if sw_r<0.9 else max(3,round((100-sj)*0.35)); sh=100-sj-sl
    oj=clamp(round(75+(1-abs(ac_r-0.85))*20+ac_bl*8),20,95); ol=round((0.85-ac_r)*60) if ac_r<0.7 else max(3,round((100-oj)*0.4)); oh=100-oj-ol
    aj=clamp(round(62+(ar_r-1)*15),20,90); al_=round((1-ar_r)*40) if ar_r<1 else max(5,round((100-aj)*0.5)); ah=100-aj-al_
    fj=clamp(round(61+co2_d*20),20,90); fl_=round((2.75-f["co2"])*30) if f["co2"]<2.5 else max(5,round((100-fj)*0.45)); fh=100-fj-fl_
    jar={"단맛":sj,"신맛":oj,"향":aj,"청량감":fj}
    jd={"단맛":{"약함":sl,"적정":sj,"강함":sh},"신맛":{"약함":ol,"적정":oj,"강함":oh},"향":{"약함":al_,"적정":aj,"강함":ah},"청량감":{"약함":fl_,"적정":fj,"강함":fh}}
    brix=round(f["sugar"]*0.1+f["erythritol"]*0.06+f["fiber"]*0.05,1)
    ph=round(clamp(4.5-f["citric"]*0.35-f["malic"]*0.25+f["citNa"]*0.3,2.5,5.0),1)
    sr=round((1-f["sugar"]/70)*100) if f["sugar"]<70 else 0
    return {"scores":scores,"jar":jar,"jar_detail":jd,"meta":{"brix":brix,"ph":ph,"sugar_reduction":sr,"func":round(func,2)}}

def expert_fb(f,r):
    msgs=[]
    s,j,jd,m=r["scores"],r["jar"],r["jar_detail"],r["meta"]
    if f["sugar"]>70: msgs.append(("⚠️",f"설탕 {f['sugar']}g은 글로벌 저당 트렌드에 역행합니다. 60g 이하로 낮추고 천연 감미료 블렌드를 권장합니다."))
    elif f["sugar"]<=55: msgs.append(("✅",f"설탕 {f['sugar']}g — 저당 포지셔닝 가능. **'당류 {m['sugar_reduction']}% 감축'** 마케팅 가능."))
    sw_n=sum([f["sugar"]>0,f["stevia"]>0,f["erythritol"]>0,f["monk"]>0])
    if sw_n>=3: msgs.append(("✅","감미료 3종+ 블렌드 — 깨끗한 단맛 프로필이 기대됩니다."))
    elif sw_n==1 and f["sugar"]>50: msgs.append(("💡","설탕 단독 감미는 단조롭습니다. 스테비아+에리스리톨 블렌드를 고려하세요."))
    if f["erythritol"]>15: msgs.append(("⚠️",f"에리스리톨 {f['erythritol']}g — 복부 불편감 가능. 12g 이하 권장."))
    if f["citric"]>0 and f["malic"]>0: msgs.append(("✅","구연산+사과산 블렌드 — 부드러운 '클린 산미' 기대."))
    if f["citric"]>3.5: msgs.append(("⚠️",f"구연산 {f['citric']}g 과도 — 단맛 마스킹 위험."))
    if f["citric"]<1.5 and f["malic"]<0.5: msgs.append(("⚠️","산미 부족 — 구연산 2.0g 이상 권장."))
    if f["co2"]>=3.2: msgs.append(("✅",f"CO₂ {f['co2']}GV — 강한 청량감이 저당을 보완합니다."))
    elif f["co2"]<2.5: msgs.append(("💡","CO₂ 부족 — 2.5GV 이상 권장."))
    funcs=[x for x,v in [("비타민D",f["vitD"]),("아연",f["zinc"]),("식이섬유",f["fiber"]),("녹차",f["greenTea"])] if v>0]
    if len(funcs)>=2: msgs.append(("✅",f"기능성 {len(funcs)}종: {', '.join(funcs)} — 기능성 음료 포지셔닝 가능."))
    elif not funcs and f["vitC"]<=0: msgs.append(("💡","기능성 원료 없음 — 글로벌 트렌드에서 기능성은 필수."))
    if j["단맛"]<50:
        if jd["단맛"]["약함"]>jd["단맛"]["강함"]: msgs.append(("💡",f"단맛 JAR {j['단맛']}% — '약하다' 응답 높음. 감미력 강화 필요."))
        else: msgs.append(("💡",f"단맛 JAR {j['단맛']}% — '강하다' 응답 높음. 설탕 감소 필요."))
    if j["청량감"]<55: msgs.append(("💡",f"청량감 JAR {j['청량감']}% — CO₂ 0.3~0.5GV 증량 권장."))
    if s["종합기호도"]>=7.3: msgs.append(("🏆",f"종합기호도 **{s['종합기호도']}** — 우수! 시제품 제조 및 정식 관능평가 진행 권장."))
    elif s["종합기호도"]>=6.8: msgs.append(("📌",f"종합기호도 **{s['종합기호도']}** — 양호. 피드백 반영 시 7.0+ 가능."))
    else: msgs.append(("📌",f"종합기호도 **{s['종합기호도']}** — 개선 필요."))
    return msgs

def expert_suggest(f):
    return {"sugar":round(max(30,f["sugar"]*0.75),1),"stevia":round(max(f["stevia"],1.5),1),"erythritol":round(max(f["erythritol"],10),1),"monk":round(max(f["monk"],0.1),2),"citric":round(clamp(f["citric"]*0.9,1.8,3.0),1),"citNa":round(f["citNa"],1),"malic":round(max(f["malic"],0.6),1),"vitC":max(f["vitC"],500),"vitD":round(max(f["vitD"],10)),"zinc":round(max(f["zinc"],3),1),"fiber":round(max(f["fiber"],3),1),"greenTea":round(max(f["greenTea"],0.3),2),"color":round(max(f["color"],2.0),1),"aroma_ml":round(max(f["aroma_ml"],1.8),1),"co2":round(max(f["co2"],3.2),1)}

# ── 세션 ──
if "f" not in st.session_state: st.session_state.f=copy.deepcopy(BASE_F)
if "hist" not in st.session_state: st.session_state.hist=[]
if "rnd" not in st.session_state: st.session_state.rnd=0

# ── 사이드바 ──
with st.sidebar:
    st.markdown("### 🧪 배합 조정 (1L)")
    st.caption(f"Round **R{st.session_state.rnd}** | 히스토리 {len(st.session_state.hist)}건")
    st.markdown("---")
    f=st.session_state.f
    st.markdown("##### 🍬 감미료")
    f["sugar"]=st.slider("백설탕 (g)",0.0,120.0,float(f["sugar"]),1.0)
    f["stevia"]=st.slider("스테비아 (g)",0.0,5.0,float(f["stevia"]),0.1)
    f["erythritol"]=st.slider("에리스리톨 (g)",0.0,30.0,float(f["erythritol"]),1.0)
    f["monk"]=st.slider("나한과 (g)",0.0,1.0,float(f["monk"]),0.05)
    st.markdown("##### 🍋 산미료")
    f["citric"]=st.slider("구연산 (g)",0.0,6.0,float(f["citric"]),0.1)
    f["citNa"]=st.slider("구연산Na (g)",0.0,2.0,float(f["citNa"]),0.1)
    f["malic"]=st.slider("사과산 (g)",0.0,3.0,float(f["malic"]),0.1)
    st.markdown("##### 💊 기능성")
    f["vitC"]=st.slider("비타민C (mg)",0,1000,int(f["vitC"]),50)
    f["vitD"]=st.slider("비타민D (μg)",0,25,int(f["vitD"]),1)
    f["zinc"]=st.slider("아연 (mg)",0.0,10.0,float(f["zinc"]),0.5)
    f["fiber"]=st.slider("식이섬유 (g)",0.0,10.0,float(f["fiber"]),0.5)
    f["greenTea"]=st.slider("녹차추출물 (g)",0.0,1.0,float(f["greenTea"]),0.05)
    st.markdown("##### 🎨 기타")
    f["color"]=st.slider("자색고구마색소 (g)",0.0,5.0,float(f["color"]),0.1)
    f["aroma_ml"]=st.slider("천연베리향 (mL)",0.0,5.0,float(f["aroma_ml"]),0.1)
    f["co2"]=st.slider("CO₂ (GV)",1.0,5.0,float(f["co2"]),0.1)

# ── 메인 ──
res=simulate(f)
fb=expert_fb(f,res)

st.markdown("# 🍹 퍼플비타 — 배합 최적화 시뮬레이터")
st.caption("사이드바에서 배합 조정 → 패널조사 실시 → 전문가 피드백 → 반복 개선")

c1,c2,c3,c4,c5=st.columns(5)
c1.metric("종합기호도",f"{res['scores']['종합기호도']}/9")
c2.metric("재구매의향",f"{res['scores']['재구매의향']}/9")
c3.metric("Brix",res["meta"]["brix"])
c4.metric("pH",res["meta"]["ph"])
c5.metric("당 감축",f"{res['meta']['sugar_reduction']}%")

st.markdown("---")
tab1,tab2,tab3,tab4=st.tabs(["📋 소비자 패널조사","👩‍🔬 전문가 피드백","📊 라운드 비교","👤 전문가 프로필"])

with tab1:
    st.subheader("📋 소비자 패널조사 (100명)")
    if st.button("🔍 이 배합으로 패널조사 실시",use_container_width=True):
        p=st.progress(0,text="패널 조사 진행 중...")
        for i in range(100):
            time.sleep(0.012)
            p.progress(i+1,text=f"패널 조사 진행 중... {i+1}/100명")
        st.session_state.rnd+=1
        st.session_state.hist.append({"round":st.session_state.rnd,"f":copy.deepcopy(f),"r":copy.deepcopy(res),"time":datetime.now().strftime("%H:%M")})
        st.success(f"✅ Round {st.session_state.rnd} 완료!")
        st.rerun()

    cl,cr=st.columns(2)
    with cl:
        st.markdown("#### 기호도 프로필")
        labels=list(res["scores"].keys()); vals=list(res["scores"].values()); bvals=[BASE_S[k] for k in labels]
        fig=go.Figure()
        fig.add_trace(go.Scatterpolar(r=bvals+[bvals[0]],theta=labels+[labels[0]],name="1차(기준)",fill="toself",fillcolor="rgba(216,180,254,0.15)",line=dict(color="#D8B4FE",width=1,dash="dot")))
        fig.add_trace(go.Scatterpolar(r=vals+[vals[0]],theta=labels+[labels[0]],name="현재 배합",fill="toself",fillcolor="rgba(124,58,237,0.2)",line=dict(color="#A855F7",width=2)))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,9],tickfont=dict(size=9,color="#5A5078")),bgcolor="#13102A",angularaxis=dict(tickfont=dict(size=10,color="#C4B5FD"))),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#E0DAF0"),showlegend=True,height=400,legend=dict(font=dict(size=10)),margin=dict(l=40,r=40,t=30,b=30))
        st.plotly_chart(fig,use_container_width=True)
    with cr:
        st.markdown("#### JAR 분포")
        jdf=pd.DataFrame(res["jar_detail"]).T; jdf.columns=["약함","적정","강함"]
        fig2=go.Figure()
        fig2.add_trace(go.Bar(name="약함",x=jdf.index,y=jdf["약함"],marker_color="#3B82F6"))
        fig2.add_trace(go.Bar(name="적정(JAR)",x=jdf.index,y=jdf["적정"],marker_color="#10B981"))
        fig2.add_trace(go.Bar(name="강함",x=jdf.index,y=jdf["강함"],marker_color="#EF4444"))
        fig2.update_layout(barmode="stack",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#13102A",font=dict(color="#E0DAF0"),height=400,xaxis=dict(tickfont=dict(size=12,color="#C4B5FD")),yaxis=dict(title="비율(%)",range=[0,100],gridcolor="#2D2555"),legend=dict(orientation="h",y=-0.15,font=dict(size=11)),margin=dict(l=40,r=20,t=30,b=60))
        st.plotly_chart(fig2,use_container_width=True)

    with st.expander("📊 상세 점수"):
        sdf=pd.DataFrame({"항목":res["scores"].keys(),"현재":res["scores"].values(),"1차기준":BASE_S.values(),"변화":[round(v-BASE_S[k],2) for k,v in res["scores"].items()]})
        st.dataframe(sdf,use_container_width=True,hide_index=True)

with tab2:
    st.subheader("👩‍🔬 Dr. 한서연의 분석")
    st.caption("15년차 음료관능연구원 | 저당 트렌드 전문가")
    for icon,msg in fb:
        if icon=="✅": st.success(f"{icon} {msg}")
        elif icon=="⚠️": st.error(f"{icon} {msg}")
        elif icon=="💡": st.info(f"{icon} {msg}")
        elif icon=="🏆": st.success(f"{icon} {msg}")
        else: st.warning(f"{icon} {msg}")

    st.markdown("---")
    st.markdown("#### 🧪 전문가 추천 배합")
    sug=expert_suggest(f)
    pn={"sugar":"설탕","stevia":"스테비아","erythritol":"에리스리톨","monk":"나한과","citric":"구연산","citNa":"구연산Na","malic":"사과산","vitC":"비타민C","vitD":"비타민D","zinc":"아연","fiber":"식이섬유","greenTea":"녹차","color":"색소","aroma_ml":"향","co2":"CO₂"}
    ch=[{"원료":pn.get(k,k),"현재":f[k],"추천":v} for k,v in sug.items() if v!=f[k]]
    if ch: st.dataframe(pd.DataFrame(ch),use_container_width=True,hide_index=True)
    if st.button("👩‍🔬 전문가 추천 적용",use_container_width=True):
        for k,v in sug.items(): st.session_state.f[k]=v
        st.success("✅ 적용 완료! 사이드바 슬라이더가 업데이트됩니다.")
        st.rerun()

with tab3:
    st.subheader("📊 라운드별 비교")
    if not st.session_state.hist:
        st.info("패널조사를 먼저 실시하세요.")
    else:
        h=st.session_state.hist; rnds=[f"R{x['round']}" for x in h]
        fig3=go.Figure()
        colors=["#A855F7","#10B981","#F59E0B","#3B82F6","#EC4899","#EF4444","#6366F1"]
        for i,k in enumerate(BASE_S.keys()):
            fig3.add_trace(go.Scatter(x=rnds,y=[x["r"]["scores"][k] for x in h],name=k,mode="lines+markers",line=dict(color=colors[i%7],width=2),marker=dict(size=8)))
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#13102A",font=dict(color="#E0DAF0"),height=400,yaxis=dict(title="점수(9점)",range=[1,9],gridcolor="#2D2555"),legend=dict(orientation="h",y=-0.2,font=dict(size=10)),margin=dict(l=40,r=20,t=30,b=80))
        st.plotly_chart(fig3,use_container_width=True)

        fig4=go.Figure()
        jc=["#F59E0B","#10B981","#A855F7","#3B82F6"]
        for i,k in enumerate(BASE_JAR.keys()):
            fig4.add_trace(go.Scatter(x=rnds,y=[x["r"]["jar"][k] for x in h],name=f"{k} 적정률",mode="lines+markers",line=dict(color=jc[i],width=2),marker=dict(size=8)))
        fig4.add_hline(y=70,line_dash="dash",line_color="#10B981",opacity=0.4,annotation_text="목표 70%",annotation_font_color="#10B981")
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#13102A",font=dict(color="#E0DAF0"),height=350,yaxis=dict(title="적정률(%)",range=[0,100],gridcolor="#2D2555"),legend=dict(orientation="h",y=-0.2,font=dict(size=10)),margin=dict(l=40,r=20,t=30,b=80))
        st.plotly_chart(fig4,use_container_width=True)

        with st.expander("📜 전체 히스토리"):
            hd=[]
            for x in h:
                row={"라운드":f"R{x['round']}","시각":x["time"],"설탕":x["f"]["sugar"],"스테비아":x["f"]["stevia"],"에리스리톨":x["f"]["erythritol"],"구연산":x["f"]["citric"],"사과산":x["f"]["malic"],"CO₂":x["f"]["co2"]}
                row.update(x["r"]["scores"])
                hd.append(row)
            st.dataframe(pd.DataFrame(hd),use_container_width=True,hide_index=True)

with tab4:
    st.subheader("👩‍🔬 Dr. 한서연 — 수석 음료관능연구원")
    c1,c2=st.columns([1,2])
    with c1:
        st.markdown("""
#### 기본 정보
- **직위:** 수석 음료관능연구원
- **경력:** 15년차 (식품공학 박사)
- **출근:** 오전 8:00 / 퇴근: 오후 6:30
- **R&D:** 30% / 관능평가: 25%
        """)
    with c2:
        fig5=go.Figure(data=[go.Pie(labels=["연구개발(30%)","관능평가(25%)","회의·문서(25%)","교육·기타(20%)"],values=[30,25,25,20],marker=dict(colors=["#7C3AED","#A855F7","#C4B5FD","#DDD6FE"]),hole=0.5)])
        fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)",font=dict(color="#E0DAF0",size=11),height=250,margin=dict(l=0,r=0,t=10,b=10))
        st.plotly_chart(fig5,use_container_width=True)
    st.markdown("""---
#### 💡 Dr. 한서연의 4원칙
1. **단맛을 올리기 전에 밸런스를 먼저 의심하라**
2. **소비자가 '좋다'고 한 것보다 시장이 원하는 것을 읽어라**
3. **보존성을 포기하면 좋은 맛도 의미 없다**
4. **기능성은 맛의 방해가 아닌 마케팅의 날개**

#### 🎯 의사결정 우선순위
> 글로벌 트렌드 > 기능성·밸런스 > 보존성 > 단순 기호도
    """)

st.markdown("---")
st.caption("🍹 퍼플비타 배합 최적화 시뮬레이터 | 패널 100명 시뮬레이션 | Dr. 한서연 AI 컨설턴트")
