import os, json, warnings
warnings.filterwarnings("ignore")
os.environ["CREWAI_STORAGE_DIR"] = "/tmp"
os.environ["OPENAI_API_KEY"] = "NA"

import streamlit as st

st.set_page_config(
    page_title="NEXUS // Job Search AI",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');

:root {
    --neon-cyan: #00f5ff;
    --neon-green: #39ff14;
    --neon-purple: #bf5fff;
    --neon-orange: #ff6b00;
    --dark-bg: #020810;
    --panel-bg: #040d1a;
    --panel-border: #0a2040;
    --grid-line: #071525;
    --text-primary: #c8e8ff;
    --text-secondary: #4a8ab5;
    --text-dim: #1a4060;
}

html, body, .stApp {
    background-color: var(--dark-bg) !important;
    font-family: 'Rajdhani', sans-serif !important;
    color: var(--text-primary) !important;
}
/* Hides Streamlit's top toolbar that was covering the header */
header[data-testid="stHeader"] { display: none !important; }
div[data-testid="stToolbar"]   { display: none !important; }
#MainMenu                       { display: none !important; }
footer                          { display: none !important; }

/* Adds breathing room so your NEXUS header starts from the top */
.block-container { padding-top: 1.5rem !important; }

.stApp {
    background-image:
        linear-gradient(rgba(0,245,255,0.015) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,245,255,0.015) 1px, transparent 1px) !important;
    background-size: 40px 40px !important;
}

.stApp > header { background: transparent !important; }

div[data-testid="stSidebar"] {
    background: var(--panel-bg) !important;
    border-right: 1px solid var(--panel-border) !important;
}

div[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent);
}

.block-container { padding-top: 1rem !important; max-width: 1400px !important; }

h1, h2, h3 {
    font-family: 'Orbitron', monospace !important;
    color: var(--neon-cyan) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
}

p, label, div, span { color: var(--text-primary) !important; }

.stButton > button {
    background: transparent !important;
    border: 1px solid var(--neon-cyan) !important;
    color: var(--neon-cyan) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.5rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
    clip-path: polygon(8px 0%, 100% 0%, calc(100% - 8px) 100%, 0% 100%) !important;
}

.stButton > button:hover {
    background: rgba(0,245,255,0.08) !important;
    box-shadow: 0 0 20px rgba(0,245,255,0.25) !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: rgba(0,20,40,0.8) !important;
    border: 1px solid var(--panel-border) !important;
    border-left: 2px solid var(--neon-cyan) !important;
    color: var(--neon-cyan) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
    border-radius: 0 !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--neon-cyan) !important;
    box-shadow: 0 0 12px rgba(0,245,255,0.15) !important;
}

.stTextInput label, .stTextArea label, .stNumberInput label, .stSelectbox label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.7rem !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}

div[data-testid="stMetric"] {
    background: rgba(0,10,25,0.9) !important;
    border: 1px solid var(--panel-border) !important;
    border-top: 2px solid var(--neon-cyan) !important;
    padding: 1rem !important;
    clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px)) !important;
}

div[data-testid="stMetricLabel"] {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.65rem !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
}

div[data-testid="stMetricValue"] {
    font-family: 'Orbitron', monospace !important;
    font-size: 1.1rem !important;
    color: var(--neon-cyan) !important;
}

div[data-testid="stExpander"] {
    background: var(--panel-bg) !important;
    border: 1px solid var(--panel-border) !important;
    border-radius: 0 !important;
    border-left: 3px solid var(--neon-purple) !important;
}

div[data-testid="stExpander"] summary {
    font-family: 'Share Tech Mono', monospace !important;
    color: var(--neon-purple) !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple)) !important;
}

.stProgress > div > div {
    background: rgba(0,20,40,0.8) !important;
    border: 1px solid var(--panel-border) !important;
    border-radius: 0 !important;
    height: 6px !important;
}

div[data-testid="stTabs"] button {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--text-secondary) !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--neon-cyan) !important;
    border-bottom: 2px solid var(--neon-cyan) !important;
    background: rgba(0,245,255,0.04) !important;
}

.stAlert {
    background: rgba(0,10,25,0.9) !important;
    border-radius: 0 !important;
    border: 1px solid var(--panel-border) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.78rem !important;
}

.stSuccess { border-left: 3px solid var(--neon-green) !important; }
.stInfo    { border-left: 3px solid var(--neon-cyan) !important; }
.stWarning { border-left: 3px solid var(--neon-orange) !important; }
.stError   { border-left: 3px solid #ff003c !important; }

div[data-testid="stMarkdownContainer"] p {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
    color: var(--text-primary) !important;
    line-height: 1.7 !important;
}

div[data-testid="stMarkdownContainer"] code {
    background: rgba(0,245,255,0.07) !important;
    color: var(--neon-cyan) !important;
    font-family: 'Share Tech Mono', monospace !important;
    border: 1px solid rgba(0,245,255,0.15) !important;
    border-radius: 0 !important;
    padding: 1px 5px !important;
}

.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid var(--neon-green) !important;
    color: var(--neon-green) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    border-radius: 0 !important;
}

hr { border-color: var(--panel-border) !important; opacity: 0.5 !important; }

.cyber-panel {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-top: 2px solid var(--neon-cyan);
    padding: 1.2rem 1.5rem;
    margin: 0.5rem 0;
    clip-path: polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 16px 100%, 0 calc(100% - 16px));
    position: relative;
}

.cyber-panel-purple {
    border-top-color: var(--neon-purple);
}

.cyber-panel-green {
    border-top-color: var(--neon-green);
}

.agent-status {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    text-align: center;
    padding: 0.4rem;
    border: 1px solid var(--panel-border);
    background: rgba(0,10,25,0.9);
    clip-path: polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%);
}

.hex-badge {
    display: inline-block;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    padding: 2px 8px;
    border: 1px solid;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.scanline {
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,0,0,0.03) 2px,
        rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def load_models(groq_key):
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1,
                   max_tokens=4096, groq_api_key=groq_key)
    creative_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.6,
                            max_tokens=4096, groq_api_key=groq_key)
    return llm, creative_llm


def build_tools(serper_key):
    from crewai.tools import BaseTool
    from langchain_community.utilities import GoogleSerperAPIWrapper

    class JobSearchTool(BaseTool):
        name: str = "job_search"
        description: str = (
            "Search for real job listings online. "
            "Input: job title and location. "
            "Returns current job postings with requirements."
        )
        def _run(self, query: str) -> str:
            try:
                s = GoogleSerperAPIWrapper(serper_api_key=serper_key, type="search", k=5)
                return s.run(query + " job opening site:linkedin.com OR site:indeed.com OR site:glassdoor.com") or "No results."
            except Exception as e:
                return "Search unavailable: " + str(e)

    class SalaryResearchTool(BaseTool):
        name: str = "salary_research"
        description: str = "Research salary ranges for a given role and location."
        def _run(self, query: str) -> str:
            try:
                s = GoogleSerperAPIWrapper(serper_api_key=serper_key, type="search", k=3)
                return s.run(query + " salary range 2024 glassdoor OR levels.fyi")
            except Exception as e:
                return "Salary search unavailable: " + str(e)

    class CompanyResearchTool(BaseTool):
        name: str = "company_research"
        description: str = "Research a company culture, mission, and news. Input: company name."
        def _run(self, company: str) -> str:
            try:
                s = GoogleSerperAPIWrapper(serper_api_key=serper_key, type="search", k=3)
                return s.run(company + " company culture mission values recent news 2024")
            except Exception as e:
                return "Company research unavailable: " + str(e)

    class SkillGapAnalyzerTool(BaseTool):
        name: str = "skill_gap_analyzer"
        description: str = (
            "Analyze gap between candidate skills and job requirements using semantic similarity. "
            "Input JSON: {candidate_skills: [...], job_requirements: [...]}"
        )
        def _run(self, input_str: str) -> str:
            try:
                from sentence_transformers import SentenceTransformer, util
                data  = json.loads(input_str)
                cands = data.get("candidate_skills", [])
                reqs  = data.get("job_requirements", [])
                if not cands or not reqs:
                    return "Error: provide both lists."
                model = SentenceTransformer("all-MiniLM-L6-v2")
                ce = model.encode(cands, convert_to_tensor=True)
                re = model.encode(reqs,  convert_to_tensor=True)
                matched, missing = [], []
                for i, req in enumerate(reqs):
                    scores = util.cos_sim(re[i], ce)[0]
                    best = float(scores.max())
                    bm   = cands[int(scores.argmax())]
                    if best >= 0.55:
                        matched.append({"requirement": req, "matched_skill": bm, "score": round(best, 3)})
                    else:
                        missing.append({"requirement": req, "closest_skill": bm, "gap_score": round(1 - best, 3)})
                pct = round(len(matched) / len(reqs) * 100, 1)
                rec = ("Strong match! Apply immediately." if pct >= 70
                       else "Good match. Highlight transferable skills." if pct >= 50
                       else "Consider upskilling before applying.")
                return json.dumps({"overall_match_pct": pct, "matched_skills": matched,
                                   "skill_gaps": missing, "recommendation": rec}, indent=2)
            except Exception as e:
                return "Error: " + str(e)

    class InterviewQuestionsTool(BaseTool):
        name: str = "interview_questions"
        description: str = "Fetch interview questions for a specific role. Input: role name."
        def _run(self, role: str) -> str:
            try:
                s = GoogleSerperAPIWrapper(serper_api_key=serper_key, type="search", k=3)
                return s.run(role + " interview questions 2024 technical behavioral")
            except Exception as e:
                return "Unavailable: " + str(e)

    return (JobSearchTool(), SalaryResearchTool(), CompanyResearchTool(),
            SkillGapAnalyzerTool(), InterviewQuestionsTool())


def build_crew(profile, llm, creative_llm, tools):
    from crewai import Agent, Task, Crew, Process
    job_tool, sal_tool, comp_tool, gap_tool, int_tool = tools
    p  = json.dumps(profile, indent=2)
    nm = profile["name"]
    tr = profile["target_role"]
    lo = profile["location"]
    ti = profile["target_industry"]
    se = profile["salary_expectation"]
    cr = profile["current_role"]
    ex = str(profile["experience_years"])

    profile_analyst = Agent(
        role="Senior Career Profile Analyst",
        goal="Analyze candidate background, extract key skills, identify unique value propositions.",
        backstory="Veteran career strategist with 15 years at top executive search firms. Helped 5000+ professionals.",
        tools=[gap_tool], llm=llm, verbose=True, allow_delegation=False, max_iter=4
    )
    job_researcher = Agent(
        role="Job Market Intelligence Researcher",
        goal="Find the top 5 best-fit job opportunities and research salary ranges.",
        backstory="Data-driven job market analyst with deep knowledge of hiring trends across tech.",
        tools=[job_tool, sal_tool, comp_tool], llm=llm, verbose=True, allow_delegation=False, max_iter=6
    )
    resume_specialist = Agent(
        role="ATS-Optimized Resume Tailoring Expert",
        goal="Craft a highly tailored ATS-optimized resume with strategic keywords and quantified achievements.",
        backstory="Certified professional resume writer. Resumes achieve 95%+ ATS pass rates.",
        tools=[gap_tool], llm=llm, verbose=True, allow_delegation=False, max_iter=4
    )
    cover_letter_writer = Agent(
        role="Cover Letter Storytelling Expert",
        goal="Write compelling personalized cover letters connecting candidate journey to company mission.",
        backstory="Former journalist turned career coach with 78% interview conversion rate.",
        tools=[comp_tool], llm=creative_llm, verbose=True, allow_delegation=False, max_iter=3
    )
    interview_coach = Agent(
        role="Executive Interview Preparation Coach",
        goal="Prepare candidates with role-specific questions, STAR frameworks, and salary negotiation tactics.",
        backstory="Former FAANG engineering manager who conducted 2000+ interviews.",
        tools=[int_tool, comp_tool], llm=llm, verbose=True, allow_delegation=False, max_iter=4
    )
    report_compiler = Agent(
        role="Strategic Career Action Plan Compiler",
        goal="Synthesize all research into a comprehensive prioritized career action plan.",
        backstory="Strategic consultant turning complex career research into crystal-clear actionable roadmaps.",
        tools=[], llm=llm, verbose=True, allow_delegation=True, max_iter=3
    )

    t1 = Task(
        description=("Analyze this candidate profile:\n" + p + "\n\n"
            "Include: 1) Executive Summary 2) Top 5 Skills with evidence "
            "3) Unique Value Proposition 4) Transferable Skills "
            "5) Career Positioning Strategy 6) Weaknesses and reframing "
            "7) Skill Gap Assessment using skill_gap_analyzer for " + tr + " "
            "8) Personal Brand Statement"),
        agent=profile_analyst,
        expected_output="Detailed profile analysis covering all 8 sections. Min 600 words."
    )
    t2 = Task(
        description=("Research job market for " + tr + " for " + nm + " in " + lo + ". "
            "Industry: " + ti + " | Salary: " + se + "\n"
            "Use job_search (5+ listings), salary_research, company_research (2+ companies). "
            "For each job: company, role, requirements, match score, salary, pros/cons. "
            "Include market conditions and 30/60/90 day timeline."),
        agent=job_researcher,
        expected_output="Job market report with top 5 ranked opportunities and salary benchmarks."
    )
    t3 = Task(
        description=("Create ATS-optimized resume for " + nm + ".\nProfile:\n" + p + "\n"
            "Include: 1) Professional Summary 2) Technical Skills by category "
            "3) Experience with quantified achievements 4) Top 3 Projects with metrics "
            "5) Education and Certifications 6) ATS Optimization Notes 7) Tailoring Notes. "
            "Use skill_gap_analyzer vs top job requirements."),
        agent=resume_specialist,
        expected_output="Complete ATS-optimized resume with all 7 sections. Min 800 words."
    )
    t4 = Task(
        description=("Write 2 personalized cover letters for " + nm + ".\n"
            "Current: " + cr + " -> Target: " + tr + "\n"
            "Use company_research for each company. Each letter: "
            "compelling hook, company mission connection, ONE STAR achievement story, "
            "specific company knowledge, confident CTA. 350-450 words each."),
        agent=cover_letter_writer,
        expected_output="Two complete personalized cover letters (350-450 words each) with strategy notes."
    )
    t5 = Task(
        description=("Create interview prep guide for " + nm + " targeting " + tr + ".\n"
            "Experience: " + ex + " years | Salary target: " + se + "\n"
            "Use interview_questions and company_research. Include: "
            "1) 10 Technical Questions with answers 2) 5 Behavioral Questions STAR "
            "3) ML System Design Question 4) 5 Smart Questions to Ask "
            "5) Salary Negotiation Script 6) Red Flags 7) 30-Day Prep Roadmap 8) Interview Tips"),
        agent=interview_coach,
        expected_output="Comprehensive interview prep guide with all 8 sections. Min 1000 words."
    )
    t6 = Task(
        description=("Compile master Career Action Plan for " + nm + ".\n"
            "Structure: 1) Executive Summary 2) Market Intelligence 3) Top 5 Jobs ranked "
            "4) Skills Assessment 5) Application Checklist 6) 30/60/90 Day Timeline "
            "7) Interview Highlights 8) Salary Strategy 9) Success KPIs 10) Next Actions This Week. "
            "Be specific, data-driven, actionable. Min 1200 words."),
        agent=report_compiler,
        expected_output="Complete Master Career Action Plan with all 10 sections. Min 1200 words."
    )

    crew = Crew(
        agents=[profile_analyst, job_researcher, resume_specialist,
                cover_letter_writer, interview_coach, report_compiler],
        tasks=[t1, t2, t3, t4, t5, t6],
        process=Process.sequential, verbose=True, memory=False, max_rpm=30
    )
    return crew, [t1, t2, t3, t4, t5, t6]


def skill_chart(profile):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    from sentence_transformers import SentenceTransformer, util

    JOB_REQS = [
        "Python programming",
        "Deep learning PyTorch or TensorFlow",
        "MLOps and model deployment",
        "LLM and Transformer models",
        "Cloud platforms AWS or GCP",
        "SQL and data engineering",
        "Distributed computing Spark",
        "CI/CD for ML pipelines",
        "A/B testing experimentation",
        "Technical leadership",
    ]
    all_skills = profile["technical_skills"] + profile["soft_skills"]
    model = SentenceTransformer("all-MiniLM-L6-v2")
    ce = model.encode(all_skills, convert_to_tensor=True)
    re = model.encode(JOB_REQS,   convert_to_tensor=True)
    scores = [float(util.cos_sim(re[i], ce)[0].max()) for i in range(len(JOB_REQS))]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#020810")
    ax.set_facecolor("#040d1a")

    for y in range(len(JOB_REQS)):
        ax.barh(y, 1.0, color="#071525", height=0.7, zorder=1)

    colors = ["#00f5ff" if s >= 0.55 else "#ff003c" for s in scores]
    bars   = ax.barh(range(len(JOB_REQS)), scores, color=colors, height=0.7, zorder=2, alpha=0.85)

    ax.axvline(x=0.55, color="#bf5fff", linestyle="--", linewidth=1, label="THRESHOLD: 0.55", zorder=3)

    ax.set_yticks(range(len(JOB_REQS)))
    ax.set_yticklabels([">> " + r.upper() for r in JOB_REQS],
                       color="#4a8ab5", fontsize=8, fontfamily="monospace")
    ax.set_xlabel("SEMANTIC MATCH SCORE", color="#4a8ab5", fontsize=8, fontfamily="monospace")
    ax.tick_params(colors="#1a4060", length=0)
    ax.set_xlim(0, 1.05)

    for sp in ax.spines.values():
        sp.set_color("#071525")

    ax.grid(axis="x", color="#071525", linewidth=0.5, zorder=0)

    for bar, s in zip(bars, scores):
        color = "#00f5ff" if s >= 0.55 else "#ff003c"
        ax.text(bar.get_width() + 0.02,
                bar.get_y() + bar.get_height() / 2,
                str(round(s, 2)), va="center", color=color,
                fontsize=8, fontfamily="monospace", fontweight="bold")

    overall = sum(scores) / len(scores)
    matched = sum(1 for s in scores if s >= 0.55)

    fig.suptitle(
        "NEXUS SKILL MATRIX  //  MATCH: " + str(round(overall * 100, 1)) +
        "%  //  " + str(matched) + "/" + str(len(JOB_REQS)) + " ACQUIRED",
        color="#00f5ff", fontsize=10, fontweight="bold", fontfamily="monospace", y=1.01
    )

    legend_elements = [
        mpatches.Patch(color="#00f5ff", label="ACQUIRED"),
        mpatches.Patch(color="#ff003c", label="GAP DETECTED"),
        mpatches.Patch(color="#bf5fff", label="THRESHOLD"),
    ]
    ax.legend(handles=legend_elements, facecolor="#040d1a", edgecolor="#0a2040",
              labelcolor="#4a8ab5", fontsize=8, loc="lower right")

    plt.tight_layout()
    return fig, overall, matched, len(JOB_REQS)


# ════════════════════════════════════════
#  UI LAYOUT
# ════════════════════════════════════════

st.markdown("""
<div style="border-bottom:1px solid #0a2040; padding-bottom:1.2rem; margin-bottom:1.5rem;">
  <div style="display:flex; align-items:center; gap:1rem;">
    <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem; color:#1a4060; line-height:1.4;">
      SYS.BOOT &nbsp;[OK]<br>NET.LINK &nbsp;[OK]<br>AI.CORE &nbsp;[RDY]
    </div>
    <div style="flex:1; text-align:center;">
      <div style="font-family:'Orbitron',monospace; font-size:2rem; font-weight:900;
                  color:#00f5ff; letter-spacing:0.3em; text-shadow:0 0 30px rgba(0,245,255,0.3);">
        &#9729; NEXUS
      </div>
      <div style="font-family:'Share Tech Mono',monospace; font-size:0.7rem;
                  color:#4a8ab5; letter-spacing:0.25em; margin-top:2px;">
        MULTI-AGENT JOB SEARCH SYSTEM &nbsp;//&nbsp; v2.0.77
      </div>
    </div>
    <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem; color:#1a4060; line-height:1.4; text-align:right;">
      AGENTS &nbsp;[06]<br>MODEL &nbsp;&nbsp;[LLM]<br>STATUS [ONL]
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace; font-size:0.6rem;
                color:#1a4060; margin-bottom:1rem; padding-bottom:0.5rem;
                border-bottom:1px solid #0a2040;">
      &#9632; SYSTEM CONFIGURATION
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#4a8ab5;margin-bottom:4px;'>&#9670; AUTH CREDENTIALS</p>", unsafe_allow_html=True)
    groq_key   = st.text_input("GROQ API KEY",   type="password", placeholder="gsk_...")
    serper_key = st.text_input("SERPER API KEY",  type="password", placeholder="abc...")
    st.markdown("<a href='https://console.groq.com' style='font-family:Share Tech Mono,monospace;font-size:0.65rem;color:#4a8ab5;'>&#10095; console.groq.com</a>", unsafe_allow_html=True)
    st.markdown("<a href='https://serper.dev' style='font-family:Share Tech Mono,monospace;font-size:0.65rem;color:#4a8ab5;'>&#10095; serper.dev</a>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#0a2040;margin:1rem 0;'>", unsafe_allow_html=True)

    st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#4a8ab5;margin-bottom:8px;'>&#9670; AGENT REGISTRY</p>", unsafe_allow_html=True)

    agents_data = [
        ("&#9651;", "#00f5ff", "UNIT-01", "PROFILE ANALYST",    "SKILLS EXTRACTION"),
        ("&#9711;", "#bf5fff", "UNIT-02", "JOB RESEARCHER",     "MARKET INTELLIGENCE"),
        ("&#9643;", "#00f5ff", "UNIT-03", "RESUME SPECIALIST",  "ATS OPTIMIZATION"),
        ("&#9670;", "#39ff14", "UNIT-04", "COVER LETTER AI",    "NARRATIVE CRAFT"),
        ("&#9650;", "#ff6b00", "UNIT-05", "INTERVIEW COACH",    "PREP PROTOCOLS"),
        ("&#9632;", "#bf5fff", "UNIT-06", "REPORT COMPILER",    "PLAN SYNTHESIS"),
    ]
    for sym, color, uid, name, role in agents_data:
        st.markdown(
            "<div style='display:flex;align-items:center;gap:6px;margin:4px 0;"
            "padding:5px 8px;border-left:2px solid " + color + ";background:rgba(0,10,25,0.5);'>"
            "<span style='color:" + color + ";font-size:0.75rem;'>" + sym + "</span>"
            "<div>"
            "<div style='font-family:Share Tech Mono,monospace;font-size:0.6rem;color:#1a4060;'>" + uid + "</div>"
            "<div style='font-family:Rajdhani,sans-serif;font-size:0.78rem;color:#c8e8ff;font-weight:600;'>" + name + "</div>"
            "<div style='font-family:Share Tech Mono,monospace;font-size:0.58rem;color:#4a8ab5;'>" + role + "</div>"
            "</div></div>",
            unsafe_allow_html=True
        )

    st.markdown("<hr style='border-color:#0a2040;margin:1rem 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;color:#1a4060;line-height:1.8;">
      LLM &nbsp;&nbsp;&nbsp;: llama-3.3-70b<br>
      PROC &nbsp;&nbsp;: SEQUENTIAL<br>
      AGENTS : 06 ACTIVE<br>
      TOOLS &nbsp;: 05 LOADED
    </div>
    """, unsafe_allow_html=True)


tab1, tab2, tab3 = st.tabs([
    "&#9632;  OPERATIVE PROFILE",
    "&#9650;  EXECUTE MISSION",
    "&#9711;  SKILL MATRIX"
])

# ═══ TAB 1 ════════════════════════════════
with tab1:
    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
                color:#4a8ab5;margin-bottom:1rem;padding:8px 12px;
                border:1px solid #0a2040;background:rgba(0,245,255,0.03);">
      &#9670; OPERATIVE DATA ENTRY &nbsp;//&nbsp; ALL FIELDS REQUIRED FOR MISSION EXECUTION
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        name             = st.text_input("&#9671; OPERATIVE NAME",       value="Alex Johnson")
        location         = st.text_input("&#9671; BASE LOCATION",        value="San Francisco, CA (Open to Remote)")
        target_role      = st.text_input("&#9671; TARGET DESIGNATION",   value="Senior Machine Learning Engineer")
        target_industry  = st.text_input("&#9671; TARGET SECTOR",        value="AI/ML, FinTech, or HealthTech")
        experience_years = st.number_input("&#9671; YEARS IN FIELD",     min_value=0, max_value=40, value=5)
        current_role     = st.text_input("&#9671; CURRENT ASSIGNMENT",   value="ML Engineer at a Series B startup")
    with col2:
        salary_exp  = st.text_input("&#9671; COMPENSATION TARGET", value="$180,000 - $230,000 + equity")
        work_pref   = st.text_input("&#9671; OPS PREFERENCE",      value="Remote-first or hybrid")
        career_goal = st.text_input("&#9671; MISSION OBJECTIVE",   value="ML Engineering Manager within 2 years")

    st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#4a8ab5;margin:1rem 0 4px;'>&#9670; TECHNICAL ARSENAL // ONE PER LINE</p>", unsafe_allow_html=True)
    tech_raw = st.text_area("tech", label_visibility="collapsed", height=150,
        value="Python\nPyTorch\nTensorFlow\nScikit-learn\nHuggingFace Transformers\n"
              "LLM fine-tuning\nRAG systems\nMLflow\nKubeflow\nApache Spark\n"
              "SQL\nAWS SageMaker\nGCP Vertex AI\nDocker\nKubernetes\nFastAPI")

    st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#4a8ab5;margin:1rem 0 4px;'>&#9670; SOFT CAPABILITIES // ONE PER LINE</p>", unsafe_allow_html=True)
    soft_raw = st.text_area("soft", label_visibility="collapsed", height=90,
        value="Technical leadership\nCross-functional collaboration\n"
              "Mentoring junior engineers\nStakeholder communication\nAgile Scrum")

    st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#4a8ab5;margin:1rem 0 4px;'>&#9670; MISSION LOG // KEY ACHIEVEMENTS, ONE PER LINE</p>", unsafe_allow_html=True)
    proj_raw = st.text_area("proj", label_visibility="collapsed", height=110,
        value="Real-time fraud detection model XGBoost LSTM - reduced false positives 34% saving 2.1M\n"
              "RAG-based customer support chatbot LangChain GPT-4 - handled 60% tier-1 tickets\n"
              "MLOps migration to Kubeflow - cut deployment from 2 weeks to 4 hours\n"
              "Published paper contrastive learning NLP at EMNLP 2022")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#4a8ab5;margin:1rem 0 4px;'>&#9670; TRAINING RECORDS</p>", unsafe_allow_html=True)
        edu_raw = st.text_area("edu", label_visibility="collapsed", height=80,
            value="M.S. Computer Science ML focus - Stanford 2019\nB.S. Mathematics Statistics - UC Berkeley 2017")
    with col4:
        st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#4a8ab5;margin:1rem 0 4px;'>&#9670; CLEARANCE CERTS</p>", unsafe_allow_html=True)
        cert_raw = st.text_area("cert", label_visibility="collapsed", height=80,
            value="AWS Certified Machine Learning Specialty\nGoogle Professional ML Engineer\nDeep Learning Specialization")

    profile = {
        "name":             name,
        "location":         location,
        "target_role":      target_role,
        "target_industry":  target_industry,
        "experience_years": int(experience_years),
        "current_role":     current_role,
        "salary_expectation": salary_exp,
        "work_preference":  work_pref,
        "career_goal":      career_goal,
        "technical_skills": [s.strip() for s in tech_raw.splitlines() if s.strip()],
        "soft_skills":      [s.strip() for s in soft_raw.splitlines() if s.strip()],
        "key_projects":     [s.strip() for s in proj_raw.splitlines() if s.strip()],
        "education":        [s.strip() for s in edu_raw.splitlines() if s.strip()],
        "certifications":   [s.strip() for s in cert_raw.splitlines() if s.strip()],
    }
    st.session_state["profile"] = profile

    st.markdown("""
    <div style="margin-top:1rem;padding:8px 16px;border:1px solid #39ff14;
                background:rgba(57,255,20,0.04);font-family:'Share Tech Mono',monospace;
                font-size:0.72rem;color:#39ff14;">
      &#9646; OPERATIVE PROFILE LOADED &nbsp;//&nbsp; READY FOR MISSION EXECUTION
    </div>
    """, unsafe_allow_html=True)

# ═══ TAB 2 ════════════════════════════════
with tab2:
    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
                color:#4a8ab5;margin-bottom:1rem;padding:8px 12px;
                border:1px solid #0a2040;background:rgba(0,245,255,0.03);">
      &#9670; MISSION CONTROL &nbsp;//&nbsp; INITIATE MULTI-AGENT DEPLOYMENT
    </div>
    """, unsafe_allow_html=True)

    if not groq_key or not serper_key:
        st.markdown("""
        <div style="padding:12px 16px;border:1px solid #ff6b00;border-left:3px solid #ff6b00;
                    background:rgba(255,107,0,0.05);font-family:'Share Tech Mono',monospace;
                    font-size:0.75rem;color:#ff6b00;">
          &#9888; AUTH REQUIRED // ENTER API CREDENTIALS IN SIDEBAR TO PROCEED
        </div>
        """, unsafe_allow_html=True)
    else:
        profile = st.session_state.get("profile", {})
        if not profile:
            st.markdown("""
            <div style="padding:12px;border:1px solid #ff6b00;font-family:'Share Tech Mono',
                        monospace;font-size:0.75rem;color:#ff6b00;">
              &#9888; OPERATIVE PROFILE NOT FOUND // COMPLETE PROFILE TAB FIRST
            </div>
            """, unsafe_allow_html=True)
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("OPERATIVE",    profile.get("name", ""))
            c2.metric("TARGET ROLE",  profile.get("target_role", "")[:25])
            c3.metric("FIELD EXP",    str(profile.get("experience_years", 0)) + " YRS")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            if st.button("&#9650;  INITIATE MISSION  //  DEPLOY ALL 6 AGENTS", use_container_width=True):
                st.session_state["results"] = {}

                st.markdown("""
                <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                            color:#4a8ab5;margin:1rem 0 0.5rem;">
                  &#9670; AGENT DEPLOYMENT STATUS
                </div>
                """, unsafe_allow_html=True)

                scols = st.columns(6)
                phs   = [c.empty() for c in scols]
                anames = ["UNIT-01\nPROFILE", "UNIT-02\nJOBS", "UNIT-03\nRESUME",
                          "UNIT-04\nCOVER", "UNIT-05\nINTERVIEW", "UNIT-06\nREPORT"]
                acolors = ["#00f5ff", "#bf5fff", "#00f5ff", "#39ff14", "#ff6b00", "#bf5fff"]

                def set_status(idx):
                    for j, (ph, an, ac) in enumerate(zip(phs, anames, acolors)):
                        parts = an.split("\n")
                        if j < idx:
                            ph.markdown(
                                "<div style='text-align:center;padding:6px 2px;border:1px solid #0a2040;"
                                "background:rgba(57,255,20,0.05);font-family:Share Tech Mono,monospace;font-size:0.6rem;'>"
                                "<div style='color:#39ff14;'>" + parts[0] + "</div>"
                                "<div style='color:#1a4060;font-size:0.55rem;'>" + parts[1] + "</div>"
                                "<div style='color:#39ff14;'>&#10003; DONE</div></div>",
                                unsafe_allow_html=True)
                        elif j == idx:
                            ph.markdown(
                                "<div style='text-align:center;padding:6px 2px;border:1px solid " + ac + ";"
                                "background:rgba(0,245,255,0.04);font-family:Share Tech Mono,monospace;font-size:0.6rem;'>"
                                "<div style='color:" + ac + ";'>" + parts[0] + "</div>"
                                "<div style='color:#4a8ab5;font-size:0.55rem;'>" + parts[1] + "</div>"
                                "<div style='color:" + ac + ";'>&#9654; ACTIVE</div></div>",
                                unsafe_allow_html=True)
                        else:
                            ph.markdown(
                                "<div style='text-align:center;padding:6px 2px;border:1px solid #071525;"
                                "background:rgba(0,10,25,0.5);font-family:Share Tech Mono,monospace;font-size:0.6rem;'>"
                                "<div style='color:#1a4060;'>" + parts[0] + "</div>"
                                "<div style='color:#1a4060;font-size:0.55rem;'>" + parts[1] + "</div>"
                                "<div style='color:#1a4060;'>&#9646; STANDBY</div></div>",
                                unsafe_allow_html=True)

                bar  = st.progress(0, text="INITIALIZING AGENT NETWORK...")
                info = st.empty()
                task_labels = ["PROFILE ANALYSIS", "JOB RESEARCH", "RESUME TAILORING",
                               "COVER LETTERS", "INTERVIEW PREP", "ACTION PLAN COMPILATION"]

                try:
                    with st.spinner("LOADING NEURAL MODELS..."):
                        llm, creative_llm = load_models(groq_key)
                    with st.spinner("ACTIVATING TOOL NETWORK..."):
                        tools = build_tools(serper_key)

                    crew, tasks = build_crew(profile, llm, creative_llm, tools)

                    for i in range(6):
                        set_status(i)
                        bar.progress(i / 6, text="EXECUTING: " + task_labels[i] + "...")
                        info.markdown(
                            "<div style='padding:8px 12px;border:1px solid #0a2040;border-left:3px solid #00f5ff;"
                            "background:rgba(0,245,255,0.03);font-family:Share Tech Mono,monospace;font-size:0.72rem;color:#4a8ab5;'>"
                            "&#9654; AGENT " + str(i+1) + "/6 ACTIVE &nbsp;//&nbsp; " + task_labels[i] +
                            "</div>",
                            unsafe_allow_html=True)

                    result = crew.kickoff()

                    for ph, an, ac in zip(phs, anames, acolors):
                        parts = an.split("\n")
                        ph.markdown(
                            "<div style='text-align:center;padding:6px 2px;border:1px solid #39ff14;"
                            "background:rgba(57,255,20,0.05);font-family:Share Tech Mono,monospace;font-size:0.6rem;'>"
                            "<div style='color:#39ff14;'>" + parts[0] + "</div>"
                            "<div style='color:#1a4060;font-size:0.55rem;'>" + parts[1] + "</div>"
                            "<div style='color:#39ff14;'>&#10003; DONE</div></div>",
                            unsafe_allow_html=True)

                    bar.progress(1.0, text="MISSION COMPLETE // ALL AGENTS RETURNED")
                    info.markdown(
                        "<div style='padding:8px 12px;border:1px solid #39ff14;border-left:3px solid #39ff14;"
                        "background:rgba(57,255,20,0.04);font-family:Share Tech Mono,monospace;font-size:0.72rem;color:#39ff14;'>"
                        "&#10003; MISSION COMPLETE &nbsp;//&nbsp; ALL 6 AGENTS EXECUTED SUCCESSFULLY"
                        "</div>",
                        unsafe_allow_html=True)

                    labels = ["Profile Analysis", "Job Research", "Resume",
                              "Cover Letters", "Interview Prep", "Action Plan"]
                    outputs = {}
                    for label, task in zip(labels, tasks):
                        out = getattr(task, "output", None)
                        outputs[label] = str(out.raw) if out and hasattr(out, "raw") else str(out or "")
                    outputs["Final Result"] = str(result)
                    st.session_state["results"] = outputs

                    st.markdown("<hr style='border-color:#0a2040;margin:1.5rem 0;'>", unsafe_allow_html=True)
                    st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#4a8ab5;'>&#9670; MISSION DATA // AGENT OUTPUTS</p>", unsafe_allow_html=True)

                    exp_icons = [
                        ("&#9651;", "#00f5ff", "PROFILE ANALYSIS"),
                        ("&#9711;", "#bf5fff", "JOB RESEARCH"),
                        ("&#9643;", "#00f5ff", "TAILORED RESUME"),
                        ("&#9670;", "#39ff14", "COVER LETTERS"),
                        ("&#9650;", "#ff6b00", "INTERVIEW PREP"),
                        ("&#9632;", "#bf5fff", "ACTION PLAN"),
                    ]
                    for (sym, col, label2), (k, v) in zip(exp_icons, list(outputs.items())[:-1]):
                        with st.expander(sym + "  " + label2):
                            st.markdown(v)

                    st.markdown("<hr style='border-color:#0a2040;margin:1.5rem 0;'>", unsafe_allow_html=True)
                    st.markdown("<p style='font-family:Orbitron,monospace;font-size:0.85rem;color:#00f5ff;letter-spacing:0.15em;'>&#9632; MASTER CAREER ACTION PLAN</p>", unsafe_allow_html=True)
                    st.markdown(outputs.get("Final Result", ""))

                    st.markdown("<hr style='border-color:#0a2040;margin:1.5rem 0;'>", unsafe_allow_html=True)
                    st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#4a8ab5;'>&#9670; EXTRACT MISSION DATA</p>", unsafe_allow_html=True)
                    dl1, dl2 = st.columns(2)
                    full_txt = "\n\n---\n\n".join(["# " + k + "\n\n" + v for k, v in outputs.items()])
                    cname = profile.get("name", "operative").replace(" ", "_")
                    with dl1:
                        st.download_button("&#9660;  FULL REPORT (.MD)", data=full_txt,
                            file_name="nexus_full_" + cname + ".md",
                            mime="text/markdown", use_container_width=True)
                    with dl2:
                        st.download_button("&#9660;  ACTION PLAN (.MD)",
                            data=outputs.get("Final Result", ""),
                            file_name="nexus_plan_" + cname + ".md",
                            mime="text/markdown", use_container_width=True)

                except Exception as e:
                    st.markdown(
                        "<div style='padding:12px;border:1px solid #ff003c;border-left:3px solid #ff003c;"
                        "background:rgba(255,0,60,0.05);font-family:Share Tech Mono,monospace;"
                        "font-size:0.75rem;color:#ff003c;'>"
                        "&#9888; MISSION FAILURE &nbsp;//&nbsp; " + str(e)[:200] +
                        "</div>",
                        unsafe_allow_html=True)
                    with st.expander("&#9670; DIAGNOSTIC LOG"):
                        st.code(str(e))
                        st.markdown("- Verify API keys are correct")
                        st.markdown("- Confirm `runtime.txt` contains `python-3.10`")
                        st.markdown("- Check Streamlit Cloud logs for full traceback")

            elif st.session_state.get("results"):
                st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:0.7rem;color:#39ff14;'>&#9646; PREVIOUS MISSION DATA AVAILABLE</p>", unsafe_allow_html=True)
                for label, content in st.session_state["results"].items():
                    if label == "Final Result":
                        continue
                    with st.expander("&#9671; " + label.upper()):
                        st.markdown(content)

# ═══ TAB 3 ════════════════════════════════
with tab3:
    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
                color:#4a8ab5;margin-bottom:1rem;padding:8px 12px;
                border:1px solid #0a2040;background:rgba(0,245,255,0.03);">
      &#9670; SKILL MATRIX SCANNER &nbsp;//&nbsp; SEMANTIC SIMILARITY ANALYSIS
    </div>
    """, unsafe_allow_html=True)

    profile = st.session_state.get("profile", {})
    if not profile.get("technical_skills"):
        st.markdown("""
        <div style="padding:12px;border:1px solid #ff6b00;font-family:'Share Tech Mono',
                    monospace;font-size:0.75rem;color:#ff6b00;">
          &#9888; NO OPERATIVE PROFILE DETECTED // COMPLETE PROFILE TAB FIRST
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.button("&#9711;  RUN SKILL MATRIX SCAN", use_container_width=True):
            with st.spinner("RUNNING SEMANTIC ANALYSIS..."):
                try:
                    fig, overall, matched, total = skill_chart(profile)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("MATCH INDEX",      str(round(overall * 100, 1)) + "%")
                    m2.metric("SKILLS ACQUIRED",  str(matched) + " / " + str(total))
                    m3.metric("GAPS DETECTED",    str(total - matched))
                    st.pyplot(fig)
                    st.markdown(
                        "<div style='font-family:Share Tech Mono,monospace;font-size:0.65rem;"
                        "color:#4a8ab5;margin-top:0.5rem;'>"
                        "&#9670; CYAN = SKILL ACQUIRED (score &gt;= 0.55) &nbsp;//&nbsp; "
                        "RED = GAP DETECTED (score &lt; 0.55) &nbsp;//&nbsp; "
                        "PURPLE = MATCH THRESHOLD"
                        "</div>",
                        unsafe_allow_html=True)
                except Exception as e:
                    st.error("SCAN ERROR: " + str(e))
