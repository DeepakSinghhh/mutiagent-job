import os, json, warnings
warnings.filterwarnings("ignore")
os.environ["CREWAI_STORAGE_DIR"] = "/tmp"
os.environ["OPENAI_API_KEY"] = "NA"          # CrewAI requires this env var even if unused

import streamlit as st

st.set_page_config(
    page_title="Multi-Agent Job Search",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp { background-color: #0d1117; color: #c9d1d9; }
.stButton > button {
    background: linear-gradient(135deg, #238636, #2ea043);
    color: white; border: none; border-radius: 8px;
    padding: 0.6rem 2rem; font-weight: bold; width: 100%;
}
div[data-testid="stSidebar"] { background-color: #161b22; }
h1, h2, h3 { color: #f0f6fc !important; }
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #161b22 !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
}
</style>
""", unsafe_allow_html=True)


# ── Cache LLM loading ────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_models(groq_key):
    from langchain_groq import ChatGroq
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=4096,
        groq_api_key=groq_key
    )
    creative_llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.6,
        max_tokens=4096,
        groq_api_key=groq_key
    )
    return llm, creative_llm


# ── Tools ────────────────────────────────────────────────────────────
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
                s = GoogleSerperAPIWrapper(
                    serper_api_key=serper_key, type="search", k=5)
                return s.run(
                    query + " job opening site:linkedin.com OR site:indeed.com OR site:glassdoor.com"
                ) or "No results found."
            except Exception as e:
                return "Search unavailable: " + str(e)

    class SalaryResearchTool(BaseTool):
        name: str = "salary_research"
        description: str = "Research salary ranges for a given role and location."
        def _run(self, query: str) -> str:
            try:
                s = GoogleSerperAPIWrapper(
                    serper_api_key=serper_key, type="search", k=3)
                return s.run(query + " salary range 2024 glassdoor OR levels.fyi")
            except Exception as e:
                return "Salary search unavailable: " + str(e)

    class CompanyResearchTool(BaseTool):
        name: str = "company_research"
        description: str = "Research a company culture, mission, and news. Input: company name."
        def _run(self, company: str) -> str:
            try:
                s = GoogleSerperAPIWrapper(
                    serper_api_key=serper_key, type="search", k=3)
                return s.run(company + " company culture mission values recent news 2024")
            except Exception as e:
                return "Company research unavailable: " + str(e)

    class SkillGapAnalyzerTool(BaseTool):
        name: str = "skill_gap_analyzer"
        description: str = (
            "Analyze gap between candidate skills and job requirements using semantic similarity. "
            "Input must be JSON string: "
            "{candidate_skills: [list of skills], job_requirements: [list of requirements]}"
        )
        def _run(self, input_str: str) -> str:
            try:
                from sentence_transformers import SentenceTransformer, util
                data  = json.loads(input_str)
                cands = data.get("candidate_skills", [])
                reqs  = data.get("job_requirements", [])
                if not cands or not reqs:
                    return "Error: provide both candidate_skills and job_requirements."
                model = SentenceTransformer("all-MiniLM-L6-v2")
                ce = model.encode(cands, convert_to_tensor=True)
                re = model.encode(reqs,  convert_to_tensor=True)
                matched, missing = [], []
                for i, req in enumerate(reqs):
                    scores = util.cos_sim(re[i], ce)[0]
                    best   = float(scores.max())
                    bm     = cands[int(scores.argmax())]
                    if best >= 0.55:
                        matched.append({"requirement": req, "matched_skill": bm,
                                        "score": round(best, 3)})
                    else:
                        missing.append({"requirement": req, "closest_skill": bm,
                                        "gap_score": round(1 - best, 3)})
                pct = round(len(matched) / len(reqs) * 100, 1)
                if pct >= 70:
                    rec = "Strong match! Apply immediately."
                elif pct >= 50:
                    rec = "Good match. Highlight transferable skills."
                else:
                    rec = "Consider upskilling before applying."
                return json.dumps({
                    "overall_match_pct": pct,
                    "matched_skills": matched,
                    "skill_gaps": missing,
                    "recommendation": rec
                }, indent=2)
            except json.JSONDecodeError:
                return "Error: input must be valid JSON."
            except Exception as e:
                return "Skill gap error: " + str(e)

    class InterviewQuestionsTool(BaseTool):
        name: str = "interview_questions"
        description: str = "Fetch interview questions for a specific role. Input: role name."
        def _run(self, role: str) -> str:
            try:
                s = GoogleSerperAPIWrapper(
                    serper_api_key=serper_key, type="search", k=3)
                return s.run(role + " interview questions 2024 technical behavioral")
            except Exception as e:
                return "Interview questions unavailable: " + str(e)

    return (
        JobSearchTool(),
        SalaryResearchTool(),
        CompanyResearchTool(),
        SkillGapAnalyzerTool(),
        InterviewQuestionsTool()
    )


# ── Crew builder ─────────────────────────────────────────────────────
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

    # ── Agents ────────────────────────────────────────────────────────
    profile_analyst = Agent(
        role="Senior Career Profile Analyst",
        goal="Analyze candidate background, extract key skills, identify unique value propositions.",
        backstory=(
            "Veteran career strategist with 15 years at top executive search firms. "
            "Helped 5000+ professionals land their dream jobs."
        ),
        tools=[gap_tool], llm=llm, verbose=True,
        allow_delegation=False, max_iter=4
    )
    job_researcher = Agent(
        role="Job Market Intelligence Researcher",
        goal="Find the top 5 best-fit job opportunities and research salary ranges.",
        backstory=(
            "Data-driven job market analyst combining real-time web intelligence "
            "with deep knowledge of hiring trends across the tech industry."
        ),
        tools=[job_tool, sal_tool, comp_tool], llm=llm, verbose=True,
        allow_delegation=False, max_iter=6
    )
    resume_specialist = Agent(
        role="ATS-Optimized Resume Tailoring Expert",
        goal="Craft a highly tailored ATS-optimized resume with strategic keywords and quantified achievements.",
        backstory=(
            "Certified professional resume writer (CPRW) who has reverse-engineered "
            "200+ ATS systems. Resumes achieve 95%+ ATS pass rates."
        ),
        tools=[gap_tool], llm=llm, verbose=True,
        allow_delegation=False, max_iter=4
    )
    cover_letter_writer = Agent(
        role="Cover Letter Storytelling Expert",
        goal="Write compelling personalized cover letters connecting candidate journey to company mission.",
        backstory=(
            "Former journalist turned career coach with a 78% interview conversion rate. "
            "Expert at narrative-driven professional communication."
        ),
        tools=[comp_tool], llm=creative_llm, verbose=True,
        allow_delegation=False, max_iter=3
    )
    interview_coach = Agent(
        role="Executive Interview Preparation Coach",
        goal="Prepare candidates with role-specific questions, STAR frameworks, and salary negotiation tactics.",
        backstory=(
            "Former FAANG engineering manager who has conducted 2000+ interviews "
            "and coached 800+ candidates to success."
        ),
        tools=[int_tool, comp_tool], llm=llm, verbose=True,
        allow_delegation=False, max_iter=4
    )
    report_compiler = Agent(
        role="Strategic Career Action Plan Compiler",
        goal="Synthesize all research and coaching insights into a comprehensive prioritized action plan.",
        backstory=(
            "Strategic consultant specializing in turning complex career research "
            "into crystal-clear, immediately actionable roadmaps."
        ),
        tools=[], llm=llm, verbose=True,
        allow_delegation=True, max_iter=3
    )

    # ── Tasks ─────────────────────────────────────────────────────────
    t1 = Task(
        description=(
            "Analyze this candidate profile in detail:\n" + p + "\n\n"
            "Provide: 1) Executive Summary 2) Top 5 Strongest Skills with evidence "
            "3) Unique Value Proposition 4) Transferable Skills "
            "5) Career Positioning Strategy 6) Potential Weaknesses and how to reframe them "
            "7) Skill Gap Assessment using skill_gap_analyzer tool for role: " + tr + " "
            "8) Personal Brand Statement (2-3 sentences)"
        ),
        agent=profile_analyst,
        expected_output="Detailed profile analysis covering all 8 sections. Minimum 600 words."
    )
    t2 = Task(
        description=(
            "Research the job market for " + tr + " for candidate " + nm + ".\n"
            "Location: " + lo + " | Industry: " + ti + " | Salary: " + se + "\n"
            "Actions: Use job_search tool (find 5+ real listings), "
            "salary_research tool (benchmark pay), "
            "company_research tool (profile 2+ companies).\n"
            "For each job provide: company name, role, key requirements, "
            "match score 0-100%, salary estimate, pros and cons for this candidate.\n"
            "Also include: overall market conditions and 30/60/90 day application timeline."
        ),
        agent=job_researcher,
        expected_output="Job market report with top 5 ranked opportunities, salary benchmarks, company profiles."
    )
    t3 = Task(
        description=(
            "Create a complete ATS-optimized resume for " + nm + ".\n"
            "Profile data:\n" + p + "\n"
            "Sections required: 1) Professional Summary (keyword-rich, 3-4 lines) "
            "2) Technical Skills organized by category "
            "3) Work Experience with quantified achievements and strong action verbs "
            "4) Key Projects (top 3) with impact metrics "
            "5) Education and Certifications "
            "6) ATS Optimization Notes explaining keyword choices "
            "7) Tailoring Notes for the top job opportunity.\n"
            "Also run skill_gap_analyzer to identify any gaps vs top job requirements."
        ),
        agent=resume_specialist,
        expected_output="Complete ATS-optimized resume with all 7 sections and tailoring notes. Min 800 words."
    )
    t4 = Task(
        description=(
            "Write 2 personalized cover letters for " + nm + ".\n"
            "Current role: " + cr + " | Target role: " + tr + "\n"
            "Use company_research tool to personalize each letter.\n"
            "Each letter must: open with a compelling hook (not I am applying for), "
            "connect candidate experience to company mission, "
            "include one STAR-method achievement story, "
            "demonstrate specific company knowledge, "
            "close with a confident call-to-action.\n"
            "Length: 350-450 words each. Tone: professional but personable."
        ),
        agent=cover_letter_writer,
        expected_output="Two complete personalized cover letters (350-450 words each) with strategy notes."
    )
    t5 = Task(
        description=(
            "Create a comprehensive interview preparation guide for " + nm + ".\n"
            "Target role: " + tr + " | Experience: " + ex + " years | Salary target: " + se + "\n"
            "Use interview_questions and company_research tools.\n"
            "Include: 1) 10 Technical Questions with detailed model answers "
            "2) 5 Behavioral Questions with STAR-method answer frameworks "
            "3) One ML System Design Question with solution approach "
            "4) 5 Smart Questions to Ask Interviewers "
            "5) Salary Negotiation Script "
            "6) Red Flags to Watch For in the role or company "
            "7) 30-Day Interview Prep Roadmap "
            "8) Interview Day Mindset and Performance Tips"
        ),
        agent=interview_coach,
        expected_output="Comprehensive interview prep guide with all 8 sections. Min 1000 words."
    )
    t6 = Task(
        description=(
            "Compile a master Career Action Plan for " + nm + " synthesizing all previous outputs.\n"
            "Structure the plan with these sections:\n"
            "1) Executive Career Summary\n"
            "2) Market Intelligence Summary\n"
            "3) Top 5 Job Opportunities ranked by fit score\n"
            "4) Skills Assessment and Gap Analysis\n"
            "5) Application Materials Checklist\n"
            "6) 30/60/90 Day Job Search Timeline\n"
            "7) Interview Preparation Highlights\n"
            "8) Salary Negotiation Strategy\n"
            "9) Success Metrics and KPIs\n"
            "10) Immediate Next Actions This Week\n"
            "Be specific, data-driven, and immediately actionable. Min 1200 words."
        ),
        agent=report_compiler,
        expected_output="Complete Master Career Action Plan with all 10 sections. Min 1200 words."
    )

    crew = Crew(
        agents=[profile_analyst, job_researcher, resume_specialist,
                cover_letter_writer, interview_coach, report_compiler],
        tasks=[t1, t2, t3, t4, t5, t6],
        process=Process.sequential,
        verbose=True,
        memory=False,
        max_rpm=30
    )
    return crew, [t1, t2, t3, t4, t5, t6]


# ── Skill Gap Chart ──────────────────────────────────────────────────
def skill_chart(profile):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
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
        "A/B testing and experimentation",
        "Technical leadership and mentoring",
    ]
    all_skills = profile["technical_skills"] + profile["soft_skills"]
    model = SentenceTransformer("all-MiniLM-L6-v2")
    ce = model.encode(all_skills, convert_to_tensor=True)
    re = model.encode(JOB_REQS,   convert_to_tensor=True)
    scores = [float(util.cos_sim(re[i], ce)[0].max()) for i in range(len(JOB_REQS))]

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#161b22")
    colors = ["#2ea043" if s >= 0.55 else "#f78166" for s in scores]
    bars   = ax.barh(range(len(JOB_REQS)), scores, color=colors, height=0.65)
    ax.axvline(x=0.55, color="#f0e68c", linestyle="--", linewidth=1.5, label="Match Threshold 0.55")
    ax.set_yticks(range(len(JOB_REQS)))
    ax.set_yticklabels(JOB_REQS, color="white", fontsize=9)
    ax.set_xlabel("Semantic Match Score", color="white")
    ax.set_title("Skill Gap Analysis vs Senior ML Engineer Requirements",
                 color="white", pad=10)
    ax.tick_params(colors="white")
    ax.set_xlim(0, 1)
    for sp in ax.spines.values():
        sp.set_color("#30363d")
    ax.legend(facecolor="#161b22", labelcolor="white", fontsize=8)
    for bar, s in zip(bars, scores):
        ax.text(bar.get_width() + 0.01,
                bar.get_y() + bar.get_height() / 2,
                str(round(s, 2)), va="center", color="white", fontsize=8)
    overall = sum(scores) / len(scores)
    matched = sum(1 for s in scores if s >= 0.55)
    fig.suptitle(
        "Overall: " + str(round(overall * 100, 1)) + "%  |  " +
        str(matched) + " / " + str(len(JOB_REQS)) + " requirements met",
        color="#f0e68c", fontsize=11, fontweight="bold"
    )
    plt.tight_layout()
    return fig, overall, matched, len(JOB_REQS)


# ════════════════════════════════════════════════════════════════════
#  UI
# ════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="text-align:center; padding:1.5rem 0 0.5rem 0;">
  <h1 style="font-size:2.2rem; margin-bottom:0.3rem;">🤖 Multi-Agent Job Search System</h1>
  <p style="color:#8b949e; font-size:1rem;">
    6 AI Agents &nbsp;·&nbsp; CrewAI &nbsp;·&nbsp; LangChain &nbsp;·&nbsp;
    Groq llama-3.3-70b &nbsp;·&nbsp; Real-time Web Search
  </p>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 API Keys")
    st.markdown("[Get Groq key (free)](https://console.groq.com)")
    st.markdown("[Get Serper key (free)](https://serper.dev)")
    groq_key   = st.text_input("Groq API Key",   type="password", placeholder="gsk_...")
    serper_key = st.text_input("Serper API Key",  type="password", placeholder="abc123...")
    st.divider()
    st.markdown("### 🤖 Agent Pipeline")
    agents_info = [
        ("🔍", "Profile Analyst",    "Analyzes skills and positioning"),
        ("📊", "Job Researcher",     "Finds matching job listings"),
        ("📄", "Resume Specialist",  "ATS-optimized resume"),
        ("✉️",  "Cover Letter Writer","Personalized cover letters"),
        ("🎤", "Interview Coach",    "Q&A prep and salary negotiation"),
        ("📋", "Report Compiler",    "Master career action plan"),
    ]
    for icon, aname, desc in agents_info:
        st.markdown(icon + " **" + aname + "**")
        st.caption(desc)
    st.divider()
    st.info("Model: llama-3.3-70b-versatile\nProvider: Groq (free tier)")

# ── Tabs ──────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Candidate Profile", "🚀 Run Agents", "📊 Skill Analysis"])

# ═══════════════ TAB 1: PROFILE ══════════════════════════════════════
with tab1:
    st.markdown("### Enter Your Information")
    st.info("Complete the form below, then go to the **Run Agents** tab.")

    col1, col2 = st.columns(2)
    with col1:
        name             = st.text_input("Full Name",            value="Alex Johnson")
        location         = st.text_input("Location",             value="San Francisco, CA (Open to Remote)")
        target_role      = st.text_input("Target Role",          value="Senior Machine Learning Engineer")
        target_industry  = st.text_input("Target Industry",      value="AI/ML, FinTech, or HealthTech")
        experience_years = st.number_input("Years of Experience",
                                           min_value=0, max_value=40, value=5)
        current_role     = st.text_input("Current Role",         value="ML Engineer at a Series B startup")
    with col2:
        salary_exp  = st.text_input("Salary Expectation",
                                    value="$180,000 - $230,000 base + equity")
        work_pref   = st.text_input("Work Preference",    value="Remote-first or hybrid")
        career_goal = st.text_input("Career Goal",
                                    value="ML Engineering Manager within 2 years")

    st.markdown("#### Technical Skills (one per line)")
    tech_raw = st.text_area("tech_skills", label_visibility="collapsed", height=170,
        value="Python\nPyTorch\nTensorFlow\nScikit-learn\nHuggingFace Transformers\n"
              "LLM fine-tuning\nRAG systems\nMLflow\nKubeflow\nApache Spark\n"
              "SQL\nAWS SageMaker\nGCP Vertex AI\nDocker\nKubernetes\nFastAPI")

    st.markdown("#### Soft Skills (one per line)")
    soft_raw = st.text_area("soft_skills", label_visibility="collapsed", height=100,
        value="Technical leadership\nCross-functional collaboration\n"
              "Mentoring junior engineers\nStakeholder communication\nAgile Scrum")

    st.markdown("#### Key Projects and Achievements (one per line)")
    proj_raw = st.text_area("projects", label_visibility="collapsed", height=115,
        value="Real-time fraud detection model XGBoost LSTM - reduced false positives 34% saving 2.1M\n"
              "RAG-based customer support chatbot LangChain GPT-4 - handled 60% tier-1 tickets\n"
              "MLOps migration to Kubeflow - cut deployment from 2 weeks to 4 hours\n"
              "Published paper contrastive learning NLP at EMNLP 2022")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### Education (one per line)")
        edu_raw = st.text_area("education", label_visibility="collapsed", height=85,
            value="M.S. Computer Science ML focus - Stanford 2019\n"
                  "B.S. Mathematics Statistics - UC Berkeley 2017")
    with col4:
        st.markdown("#### Certifications (one per line)")
        cert_raw = st.text_area("certifications", label_visibility="collapsed", height=85,
            value="AWS Certified Machine Learning Specialty\n"
                  "Google Professional ML Engineer\n"
                  "Deep Learning Specialization deeplearning.ai")

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
    st.success("Profile ready: " + name + " targeting " + target_role)

# ═══════════════ TAB 2: RUN ══════════════════════════════════════════
with tab2:
    st.markdown("### Launch the 6-Agent Crew")

    if not groq_key or not serper_key:
        st.warning("Please enter both API keys in the sidebar before running.")
    else:
        profile = st.session_state.get("profile", {})
        if not profile:
            st.warning("Fill in the Candidate Profile tab first.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Candidate",   profile.get("name", ""))
            c2.metric("Target Role", profile.get("target_role", "")[:28])
            c3.metric("Experience",  str(profile.get("experience_years", 0)) + " yrs")
            st.divider()

            if st.button("🚀 Start Multi-Agent Job Search", use_container_width=True):
                st.session_state["results"] = {}

                # Status row
                st.markdown("#### Agent Execution Status")
                scols = st.columns(6)
                phs   = [c.empty() for c in scols]
                anames = ["🔍 Profile", "📊 Jobs", "📄 Resume",
                          "✉️ Cover", "🎤 Interview", "📋 Report"]

                def set_status(current_idx):
                    for j, (ph, an) in enumerate(zip(phs, anames)):
                        if j < current_idx:
                            ph.markdown(
                                "<div style='text-align:center;color:#2ea043'>"
                                + an + "<br>✅ Done</div>",
                                unsafe_allow_html=True)
                        elif j == current_idx:
                            ph.markdown(
                                "<div style='text-align:center;color:#f0e68c'>"
                                + an + "<br>🔄 Running</div>",
                                unsafe_allow_html=True)
                        else:
                            ph.markdown(
                                "<div style='text-align:center;color:#8b949e'>"
                                + an + "<br>⏳ Waiting</div>",
                                unsafe_allow_html=True)

                bar  = st.progress(0, text="Initializing...")
                info = st.empty()
                task_labels = ["Profile Analysis", "Job Research", "Resume Tailoring",
                               "Cover Letters", "Interview Prep", "Final Action Plan"]

                try:
                    with st.spinner("Loading LLM models (cached after first run)..."):
                        llm, creative_llm = load_models(groq_key)

                    with st.spinner("Initializing tools..."):
                        tools = build_tools(serper_key)

                    crew, tasks = build_crew(profile, llm, creative_llm, tools)

                    # Show each agent running
                    for i in range(6):
                        set_status(i)
                        bar.progress(i / 6, text="Agent " + str(i+1) + "/6: " + task_labels[i])
                        info.info("Currently running: " + task_labels[i] + "...")

                    result = crew.kickoff()

                    # All done
                    for ph, an in zip(phs, anames):
                        ph.markdown(
                            "<div style='text-align:center;color:#2ea043'>"
                            + an + "<br>✅ Done</div>",
                            unsafe_allow_html=True)
                    bar.progress(1.0, text="All 6 agents completed!")
                    info.success("All agents finished successfully!")

                    # Collect outputs
                    labels = ["Profile Analysis", "Job Research", "Resume",
                              "Cover Letters", "Interview Prep", "Action Plan"]
                    outputs = {}
                    for label, task in zip(labels, tasks):
                        out = getattr(task, "output", None)
                        if out and hasattr(out, "raw"):
                            outputs[label] = str(out.raw)
                        else:
                            outputs[label] = str(out) if out else ""
                    outputs["Final Result"] = str(result)
                    st.session_state["results"] = outputs

                    # Display
                    st.divider()
                    st.markdown("### Results")
                    icons2 = ["🔍", "💼", "📄", "✉️", "🎤", "🏆"]
                    for icon2, (label, content) in zip(icons2, list(outputs.items())[:-1]):
                        with st.expander(icon2 + " " + label,
                                         expanded=(label == "Action Plan")):
                            st.markdown(content)

                    st.divider()
                    st.markdown("### 🏆 Master Career Action Plan")
                    st.markdown(outputs.get("Final Result", ""))

                    # Downloads
                    st.divider()
                    st.markdown("### Download")
                    dl1, dl2 = st.columns(2)
                    full_txt = "\n\n---\n\n".join(
                        ["# " + k + "\n\n" + v for k, v in outputs.items()])
                    cname = profile.get("name", "candidate").replace(" ", "_")
                    with dl1:
                        st.download_button(
                            "📥 Full Report (.md)", data=full_txt,
                            file_name="career_plan_" + cname + ".md",
                            mime="text/markdown", use_container_width=True)
                    with dl2:
                        st.download_button(
                            "📥 Action Plan Only (.md)",
                            data=outputs.get("Final Result", ""),
                            file_name="action_plan_" + cname + ".md",
                            mime="text/markdown", use_container_width=True)

                except Exception as e:
                    st.error("Error: " + str(e))
                    with st.expander("Troubleshooting"):
                        st.markdown("1. Check your Groq and Serper API keys are correct")
                        st.markdown("2. Make sure `runtime.txt` contains `python-3.10`")
                        st.markdown("3. Check Streamlit Cloud logs for the full traceback")
                        st.code(str(e))

            elif st.session_state.get("results"):
                st.success("Previous results available:")
                for label, content in st.session_state["results"].items():
                    if label == "Final Result":
                        continue
                    with st.expander("📄 " + label):
                        st.markdown(content)

# ═══════════════ TAB 3: SKILL CHART ══════════════════════════════════
with tab3:
    st.markdown("### Skill Gap Analysis")
    st.markdown(
        "Computes semantic similarity between your skills and "
        "10 core Senior ML Engineer requirements using sentence-transformers.")
    profile = st.session_state.get("profile", {})
    if not profile.get("technical_skills"):
        st.warning("Complete the Candidate Profile tab first.")
    else:
        if st.button("Run Skill Gap Analysis", use_container_width=True):
            with st.spinner("Computing semantic similarity scores..."):
                try:
                    fig, overall, matched, total = skill_chart(profile)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Overall Match",   str(round(overall * 100, 1)) + "%")
                    m2.metric("Requirements Met", str(matched) + " / " + str(total))
                    m3.metric("Skill Gaps",       str(total - matched) + " areas to develop")
                    st.pyplot(fig)
                    st.caption(
                        "Green bar = requirement met (score >= 0.55). "
                        "Red bar = skill gap (score < 0.55).")
                except Exception as e:
                    st.error("Chart error: " + str(e))
