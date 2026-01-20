import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
import plotly.graph_objects as go
import json
from datetime import datetime
import urllib.parse 

# --- SECURE CONFIGURATION ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key missing! Please add GEMINI_API_KEY in Streamlit Secrets.")

def get_gemini_pro_analysis(resume_text, job_role, prompt_type):
    # Model configuration
    model = genai.GenerativeModel('gemini-2.5-flash') 
    
    prompts = {
        "full_analysis": f"""
            Analyze resume for {job_role}. Output JSON:
            {{
                "score": int,
                "reasoning": "Explain score based on 2026 market trends with examples",
                "summary": "Professional summary",
                "skills_found": [], "skills_missing": [],
                "job_links": [
                    {{ "title": "Exact Role Name", "platform": "LinkedIn" }},
                    {{ "title": "Exact Role Name", "platform": "Indeed" }}
                ],
                "roadmap": [{{ "week": 1, "task": "detailed task", "resources": ["link or name"] }}],
                "projects": ["Idea 1", "Idea 2"]
            }}
            Resume: {resume_text}
        """
    }
    
    try:
        if prompt_type == "analysis":
            response = model.generate_content(prompts["full_analysis"])
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        else:
            response = model.generate_content(f"Career Guide for {job_role}: {resume_text}")
            return response.text
            
    except Exception as e:
        # Check for Resource Exhausted / Rate Limit error
        if "429" in str(e) or "ResourceExhausted" in str(e):
            return "LIMIT_EXHAUSTED"
        else:
            st.error(f"Technical Error: {e}")
            return None

# --- UI Setup ---
st.set_page_config(page_title="CV Sniper | Precision Career Intelligence", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .main { background-color: #F8FAFC; }
    .stTabs [data-baseweb="tab-list"] { background: white; padding: 10px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab"] { font-weight: 600; color: #64748B; }
    .stTabs [aria-selected="true"] { color: #2563EB !important; border-bottom-color: #2563EB !important; }
    .card { background: white; padding: 2rem; border-radius: 1.2rem; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
    .skill-tag { background: #EFF6FF; color: #1E40AF; padding: 5px 12px; border-radius: 20px; font-size: 0.85rem; display: inline-block; margin: 3px; }
    </style>
    """, unsafe_allow_html=True)

if "data" not in st.session_state: st.session_state.data = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.title("CV Sniper Center")
    target_role = st.text_input("Target Job Role", placeholder="e.g. AI Engineer")
    uploaded_file = st.file_uploader("Drop your Resume (PDF)", type=["pdf"])
    
    if st.button("Analyze My Profile", use_container_width=True):
        if uploaded_file and target_role:
            with st.spinner("Sniper is targeting your career gaps..."):
                reader = pdf.PdfReader(uploaded_file)
                text = "".join([page.extract_text() for page in reader.pages])
                
                result = get_gemini_pro_analysis(text, target_role, "analysis")
                
                if result == "LIMIT_EXHAUSTED":
                    st.warning("**Daily Limit Reached!**")
                    st.info(""Daily quota reached! 🚀 My AI engine needs a recharge. Please check back tomorrow for your precision career analysis. 🎯")
                elif result:
                    st.session_state.data = result
                    st.rerun()
        else:
            st.warning("Please provide both Job Role and Resume.")
    
    st.write("---")
    with st.popover("💬 Career Assistant", use_container_width=True):
        st.subheader("Smart Career Bot")
        chat_box = st.container(height=300)
        for m in st.session_state.chat_history:
            chat_box.chat_message(m["role"]).write(m["content"])
        
        if query := st.chat_input("Ask me anything..."):
            st.session_state.chat_history.append({"role": "user", "content": query})
            chat_box.chat_message("user").write(query)
            
            bot_reply = get_gemini_pro_analysis(query, target_role, "chat")
            
            if bot_reply == "LIMIT_EXHAUSTED":
                bot_reply = "Daily quota reached! 🚀 My AI engine needs a recharge. Please check back tomorrow for your precision career analysis. 😴"
                
            st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
            chat_box.chat_message("assistant").write(bot_reply)

if st.session_state.data:
    res = st.session_state.data
    st.title("🎯 CV Sniper Dashboard")
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Profile Match", "📈 Market Analytics", "🔍 Live Jobs", "🛠️ Skill Roadmap"])

    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        col_t, col_d = st.columns([3, 1])
        with col_t:
            st.subheader("Ability Summary")
            st.write(res.get('summary', 'Analysis pending...'))
        with col_d:
            st.download_button("📥 Download Report", str(res), file_name="CV_Sniper_Report.txt", use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Top Strengths**")
            for s in res.get('skills_found', []): st.markdown(f"<span class='skill-tag'>✅ {s}</span>", unsafe_allow_html=True)
        with c2:
            st.markdown("**Gaps to Fill**")
            for s in res.get('skills_missing', []): st.markdown(f"<span class='skill-tag' style='background:#FFF1F2; color:#9F1239;'>❌ {s}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        col_c, col_txt = st.columns([1, 2])
        with col_c:
            score = res.get('score', 0)
            fig = go.Figure(go.Indicator(mode="gauge+number", value=score, title={'text': "ATS Score"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#2563EB"}}))
            fig.update_layout(height=250, margin=dict(t=0, b=0, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
        with col_txt:
            st.subheader("Market Logic")
            st.info(res.get('reasoning', 'Evaluating...'))
            st.write("**Comparison:** Top candidates in this field usually have 85%+ match.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.subheader("🚀 Real-time Direct Job Links")
        for job in res.get('job_links', []):
            job_title = job['title']
            platform = job.get('platform', 'LinkedIn')
            query_encoded = urllib.parse.quote(job_title)
            if platform == "LinkedIn":
                final_link = f"https://www.linkedin.com/jobs/search/?keywords={query_encoded}&f_TPR=r604800"
            elif platform == "Indeed":
                final_link = f"https://www.indeed.com/jobs?q={query_encoded}&fromage=7"
            else:
                final_link = f"https://www.google.com/search?q={query_encoded}+jobs"

            st.markdown(f"""
                <div class='card' style='padding: 1.2rem; border-left: 5px solid #2563EB;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div><h4 style='margin:0;'>{job_title}</h4><p style='margin:0; font-size:0.85rem; color:gray;'>Portal: {platform}</p></div>
                        <a href='{final_link}' target='_blank'><button style='background:#2563EB; color:white; border:none; padding:10px 18px; border-radius:8px; cursor:pointer; font-weight:bold;'>Apply on {platform} ↗</button></a>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with tab4:
        st.subheader("4-Week Mastery Roadmap")
        for step in res.get('roadmap', []):
            with st.expander(f"Week {step['week']}: {step['task'][:50]}..."):
                st.write(f"**Goal:** {step['task']}")
                for r in step['resources']:
                    st.markdown(f"- [Search {r} on YouTube](https://www.youtube.com/results?search_query={r.replace(' ','+')})")

else:
    st.info("👈 Please upload your resume in the sidebar to begin.")
    st.image("https://img.freepik.com/free-vector/modern-dashboard-ui-ux-design_52683-39031.jpg", use_container_width=True)

