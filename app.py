import os, json, warnings
warnings.filterwarnings("ignore")
os.environ["CREWAI_STORAGE_DIR"] = "/tmp"

import streamlit as st

st.set_page_config(
    page_title="Multi-Agent Job Search",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp { background-color: #0d1117; }
.stButton > button {
    background: linear-gradient(135deg, #238636, #2ea043);
    color: white; border: none; border-radius: 8px;
    padding: 0.6rem 2rem; font-weight: bold; width: 100%;
}
div[data-testid="stSidebar"] { background-color: #161b22; }
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
    from langchain_community.tools import DuckDuckGoSearchRun
    from langchain_community.utilities import GoogleSerperAPIWrapper

    class JobSearchTool(BaseTool):
        name: str = "job_search"
        description: str = (
            "Search for real job listings. "
            "Input: job title + location. "
            "Returns current postings with requirements."
        )
        def _run(self, query: str) -> str:
            try:
                s = GoogleSerperAPIWrapper(serper_api_key=serper_key, type="search", k=5)
                r = s.run(query + " job opening site:linkedin.com OR site:indeed.com OR site:glassdoor.com")
                return r or "No results."
            except Exception as e:
                try:
                    return DuckDuckGoSearchRun().run(query + " job posting 2024")
                except Exception:
                    return "Search error: " + str(e)

    class SalaryResearchTool(BaseTool):
        name: str = "salary_research"
        description: str = "Research salary ranges for a role/location."
        def _run(self, query: str) -> str:
            try:
                s = GoogleSerperAPIWrapper(serper_api_key=serper_key, type="search", k=3)
                return s.run(query + " salary range 2024 glassdoor OR levels.fyi")
            except Exception:
                return DuckDuckGoSearchRun().run(query + " average salary 2024")

    class CompanyResearchTool(BaseTool):
        name: str = "company_research"
        description: str = "Research a company culture, mission, and recent news. Input: company name."
        def _run(self, company: str) -> str:
            try:
                s = GoogleSerperAPIWrapper(serper_api_key=serper_key, type="search", k=3)
                return s.run(company + " company culture mission values 2024")
            except Exception:
                return DuckDuckGoSearchRun().run(company + " company overview")

    class SkillGapAnalyzerTool(BaseTool):
        name: str = "skill_gap_analyzer"
        description: str = (
            "Analyze gap between candidate skills and job requirements. "
            "Input JSON: {candidate_skills: [...], job_requirements: [...]}."
        )
        def _run(self, input_str: str) -> str:
            try:
                from sentence_transformers import SentenceTransformer, util
                data  = json.loads(input_str)
                cands = data.get("candidate_skills", [])
                reqs  = data.get("job_requirements", [])
                if not cands or not reqs:
                    return "Provide both lists."
                model = SentenceTransformer("all-MiniLM-L6-v2")
                ce = model.encode(cands, convert_to_tensor=True)
                re = model.encode(reqs,  convert_to_tensor=True)
                matched, missing = [], []
                for i, req in enumerate(reqs):
                    scores = util.cos_sim(re[i], ce)[0]
                    best   = float(scores.max())
                    bm     = cands[int(scores.argmax())]
                    if best >= 0.55:
                        matched.append({"req": req, "skill": bm, "score": round(best, 3)})
                    else:
                        missing.append({"req": req, "closest": bm, "gap": round(1 - best, 3)})
                pct = round(len(matched) / len(reqs) * 100, 1)
                if pct >= 70:
                    rec = "Strong match! Apply immediately."
                elif pct >= 50:
                    rec = "Good match. Highlight transferable skills."
                else:
                    rec = "Consider upskilling before applying."
                return json.dumps({"match_pct": pct, "matched": matched,
                                   "gaps": missing, "recommendation": rec}, indent=2)
            except Exception as e:
                return "Error: " + str(e)

    class InterviewQuestionsTool(BaseTool):
        name: str = "interview_questions"
        description: str = "Fetch interview questions for a role. Input: role name."
        def _run(self, role: str) -> str:
            try:
                s = GoogleSerperAPIWrapper(serper_api_key=serper_key, type="search", k=3)
                return s.run(role + " interview questions 2024 technical behavioral")
            except Exception:
                return DuckDuckGoSearchRun().run(role + " interview questions")

    return (JobSearchTool(), SalaryResearchTool(), CompanyResearchTool(),
            SkillGapAnalyzerTool(), InterviewQuestionsTool())


def build_crew(profile, llm, creative_llm, tools):
    from crewai import Agent, Task, Crew, Process
    job_tool, sal_tool, comp_tool, gap_tool, int_tool = tools
    p = json.dumps(profile, indent=2)
    tr = profile["target_role"]
    nm = profile["name"]
    lo = profile["location"]
    ti = profile["target_industry"]
    se = profile["salary_expectation"]
    cr = profile["current_role"]
    ex = str(profile["experience_years"])
    cg = profile["career_goal"]

    profile_analyst = Agent(
        role="Senior Career Profile Analyst",
        goal="Analyze candidate background, extract skills, identify value propositions.",
        backstory="Veteran career strategist with 15 years at top executive search firms.",
        tools=[gap_tool], llm=llm, verbose=True, allow_delegation=False, max_iter=4
    )
    job_researcher = Agent(
        role="Job Market Intelligence Researcher",
        goal="Find top 5 best-fit job opportunities and evaluate company fit.",
        backstory="Data-driven job market analyst with deep hiring trend expertise.",
        tools=[job_tool, sal_tool, comp_tool], llm=llm, verbose=True,
        allow_delegation=False, max_iter=6
    )
    resume_specialist = Agent(
        role="ATS-Optimized Resume Tailoring Expert",
        goal="Craft highly tailored ATS-optimized resumes with keywords and quantified achievements.",
        backstory="Certified professional resume writer. Resumes achieve 95%+ ATS pass rates.",
        tools=[gap_tool], llm=llm, verbose=True, allow_delegation=False, max_iter=4
    )
    cover_letter_writer = Agent(
        role="Cover Letter Storytelling Expert",
        goal="Write compelling personalized cover letters connecting journey to company mission.",
        backstory="Former journalist turned career coach with 78% interview conversion rate.",
        tools=[comp_tool], llm=creative_llm, verbose=True, allow_delegation=False, max_iter=3
    )
    interview_coach = Agent(
        role="Executive Interview Preparation Coach",
        goal="Prepare candidates with role-specific questions and salary negotiation tactics.",
        backstory="Former FAANG engineering manager who conducted 2000+ interviews.",
        tools=[int_tool, comp_tool], llm=llm, verbose=True, allow_delegation=False, max_iter=4
    )
    report_compiler = Agent(
        role="Strategic Career Action Plan Compiler",
        goal="Synthesize all research into a comprehensive prioritized career action plan.",
        backstory="Strategic consultant specializing in clear data-backed career roadmaps.",
        tools=[], llm=llm, verbose=True, allow_delegation=True, max_iter=3
    )

    t1 = Task(
        description=(
            "Analyze this candidate profile:\n" + p + "\n\n"
            "Include: 1) Executive Summary 2) Top 5 Skills with evidence "
            "3) Unique Value Proposition 4) Transferable Skills "
            "5) Career Positioning Strategy 6) Weaknesses and how to address them "
            "7) Skill Gap Assessment using skill_gap_analyzer for " + tr + " "
            "8) Personal Brand Statement"
        ),
        agent=profile_analyst,
        expected_output="Detailed career profile analysis with all 8 sections. Min 600 words."
    )
    t2 = Task(
        description=(
            "Research job market for " + tr + " for " + nm + " in " + lo + ". "
            "Target industry: " + ti + ". Salary: " + se + ".\n"
            "Use job_search (5+ listings), salary_research, company_research (2+ companies). "
            "For each job: company, role, requirements, match score, salary, pros/cons. "
            "Include market conditions and 30/60/90 day timeline."
        ),
        agent=job_researcher,
        expected_output="Job market report with top 5 ranked opportunities and salary benchmarks."
    )
    t3 = Task(
        description=(
            "Create ATS-optimized resume for " + nm + ".\nProfile:\n" + p + "\n"
            "Include: 1) Professional Summary 2) Technical Skills by category "
            "3) Experience with quantified achievements 4) Top 3 Projects with metrics "
            "5) Education and Certifications 6) ATS Optimization Notes 7) Tailoring Notes. "
            "Use skill_gap_analyzer vs top job requirements."
        ),
        agent=resume_specialist,
        expected_output="Complete ATS-optimized resume with all 7 sections. Min 800 words."
    )
    t4 = Task(
        description=(
            "Write 2 personalized cover letters for " + nm + ".\n"
            "Current: " + cr + " -> Target: " + tr + ".\n"
            "Use company_research for each company. Each letter must have: "
            "compelling hook, connection to company mission, ONE STAR achievement story, "
            "specific company knowledge, enthusiasm, confident CTA. 350-450 words each."
        ),
        agent=cover_letter_writer,
        expected_output="Two complete cover letters (350-450 words each) with strategy notes."
    )
    t5 = Task(
        description=(
            "Create interview prep guide for " + nm + " targeting " + tr + ".\n"
            "Experience: " + ex + " years. Salary target: " + se + ".\n"
            "Use interview_questions and company_research tools. Include: "
            "1) 10 Technical Questions with answers 2) 5 Behavioral Questions with STAR "
            "3) ML System Design Question 4) 5 Smart Questions to Ask "
            "5) Salary Negotiation Script 6) Red Flags to Watch "
            "7) 30-Day Prep Roadmap 8) Interview Day Tips"
        ),
        agent=interview_coach,
        expected_output="Comprehensive interview prep guide with all 8 sections. Min 1000 words."
    )
    t6 = Task(
        description=(
            "Compile a master Career Action Plan for " + nm + ".\n"
            "Structure: Executive Summary | Market Intelligence | Top 5 Jobs (ranked) | "
            "Skills Assessment | Application Checklist | 30/60/90 Day Timeline | "
            "Interview Highlights | Salary Strategy | Success KPIs | Next Actions This Week. "
            "Be specific, data-driven, and immediately actionable."
        ),
        agent=report_compiler,
        expected_output="Master Career Action Plan with all sections. Min 1200 words."
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
    import numpy as np
    from sentence_transformers import SentenceTransformer, util

    JOB_REQS = [
        "Python programming", "Deep learning (PyTorch/TensorFlow)",
        "MLOps and model deployment", "LLM and Transformer models",
        "Cloud platforms (AWS/GCP)", "SQL and data engineering",
        "Distributed computing (Spark)", "CI/CD for ML pipelines",
        "A/B testing and experimentation", "Technical leadership",
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
    ax.axvline(x=0.55, color="#f0e68c", linestyle="--", linewidth=1.5, label="Threshold 0.55")
    ax.set_yticks(range(len(JOB_REQS)))
    ax.set_yticklabels(JOB_REQS, color="white", fontsize=9)
    ax.set_xlabel("Semantic Match Score", color="white")
    ax.set_title("Skill Gap Analysis", color="white", pad=10)
    ax.tick_params(colors="white")
    ax.set_xlim(0, 1)
    for sp in ax.spines.values():
        sp.set_color("#30363d")
    ax.legend(facecolor="#161b22", labelcolor="white", fontsize=8)
    for bar, s in zip(bars, scores):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                str(round(s, 2)), va="center", color="white", fontsize=8)
    overall = sum(scores) / len(scores)
    matched = sum(1 for s in scores if s >= 0.55)
    fig.suptitle(
        "Overall Match: " + str(round(overall * 100, 1)) + "%  |  " +
        str(matched) + "/" + str(len(JOB_REQS)) + " Requirements Met",
        color="#f0e68c", fontsize=11, fontweight="bold"
    )
    plt.tight_layout()
    return fig, overall, matched, len(JOB_REQS)


# ════════════════════════════════════════════
#  STREAMLIT UI
# ════════════════════════════════════════════

st.markdown("""
<div style="text-align:center;padding:1.5rem 0 0.5rem 0;">
<h1>🤖 Multi-Agent Job Search System</h1>
<p style="color:#8b949e;">6 AI Agents &nbsp;·&nbsp; CrewAI &nbsp;·&nbsp; LangChain &nbsp;·&nbsp;
Groq llama-3.3-70b &nbsp;·&nbsp; Real-time Web Search</p>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 API Keys")
    st.markdown("[Get Groq key (free)](https://console.groq.com)")
    st.markdown("[Get Serper key (free)](https://serper.dev)")
    groq_key   = st.text_input("Groq API Key",  type="password", placeholder="gsk_...")
    serper_key = st.text_input("Serper API Key", type="password", placeholder="abc123...")
    st.divider()
    st.markdown("### 🤖 Agents")
    for icon, name, desc in [
        ("🔍", "Profile Analyst",    "Analyzes skills and positioning"),
        ("📊", "Job Researcher",     "Finds matching job listings"),
        ("📄", "Resume Specialist",  "ATS-optimized resume"),
        ("✉️",  "Cover Letter Writer","Personalized cover letters"),
        ("🎤", "Interview Coach",    "Q&A prep and salary negotiation"),
        ("📋", "Report Compiler",    "Master action plan"),
    ]:
        st.markdown(icon + " **" + name + "**  \n" + desc)
    st.divider()
    st.info("Model: llama-3.3-70b-versatile\nProvider: Groq (free)")

# ── Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Candidate Profile", "🚀 Run Agents", "📊 Skill Analysis"])

# ─── TAB 1: PROFILE ─────────────────────────────────────────────────
with tab1:
    st.markdown("### Enter Candidate Information")
    st.info("Fill in your details, then go to the **Run Agents** tab.")

    col1, col2 = st.columns(2)
    with col1:
        name             = st.text_input("Full Name",            value="Alex Johnson")
        location         = st.text_input("Location",             value="San Francisco, CA (Open to Remote)")
        target_role      = st.text_input("Target Role",          value="Senior Machine Learning Engineer")
        target_industry  = st.text_input("Target Industry",      value="AI/ML, FinTech, or HealthTech")
        experience_years = st.number_input("Years of Experience",min_value=0, max_value=40, value=5)
        current_role     = st.text_input("Current Role",         value="ML Engineer at a Series B startup")
    with col2:
        salary_exp   = st.text_input("Salary Expectation", value="$180,000 - $230,000 base + equity")
        work_pref    = st.text_input("Work Preference",    value="Remote-first or hybrid")
        career_goal  = st.text_input("Career Goal",        value="ML Engineering Manager within 2 years")

    st.markdown("#### Technical Skills (one per line)")
    tech_raw = st.text_area("", height=180,
        value="Python\nPyTorch\nTensorFlow\nScikit-learn\nHuggingFace Transformers\n"
              "LLM fine-tuning\nRAG systems\nMLflow\nKubeflow\nApache Spark\n"
              "SQL\nAWS SageMaker\nGCP Vertex AI\nDocker\nKubernetes\nFastAPI")

    st.markdown("#### Soft Skills (one per line)")
    soft_raw = st.text_area("", height=100,
        value="Technical leadership\nCross-functional collaboration\n"
              "Mentoring junior engineers\nStakeholder communication\nAgile Scrum")

    st.markdown("#### Key Projects and Achievements (one per line)")
    proj_raw = st.text_area("", height=120,
        value="Real-time fraud detection model (XGBoost + LSTM) - reduced false positives by 34% saving 2.1M annually\n"
              "RAG-based customer support chatbot using LangChain and GPT-4 - handled 60% of tier-1 tickets\n"
              "MLOps pipeline migration to Kubeflow - cut deployment from 2 weeks to 4 hours\n"
              "Published paper on contrastive learning for NLP at EMNLP 2022")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### Education (one per line)")
        edu_raw = st.text_area("", height=90,
            value="M.S. Computer Science ML focus - Stanford University 2019\n"
                  "B.S. Mathematics and Statistics - UC Berkeley 2017")
    with col4:
        st.markdown("#### Certifications (one per line)")
        cert_raw = st.text_area("", height=90,
            value="AWS Certified Machine Learning Specialty\n"
                  "Google Professional ML Engineer\n"
                  "Deep Learning Specialization deeplearning.ai")

    profile = {
        "name":             name,
        "location":         location,
        "target_role":      target_role,
        "target_industry":  target_industry,
        "experience_years": experience_years,
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
    st.success("Profile ready for " + name + " targeting " + target_role)

# ─── TAB 2: RUN AGENTS ──────────────────────────────────────────────
with tab2:
    st.markdown("### Launch Multi-Agent Crew")
    if not groq_key or not serper_key:
        st.warning("Enter both API keys in the sidebar first.")
    else:
        profile = st.session_state.get("profile", {})
        c1, c2, c3 = st.columns(3)
        c1.metric("Target Role",    str(profile.get("target_role", ""))[:30])
        c2.metric("Experience",     str(profile.get("experience_years", 0)) + " years")
        c3.metric("Salary Target",  str(profile.get("salary_expectation", ""))[:25])
        st.divider()

        if st.button("🚀 Start Multi-Agent Job Search", use_container_width=True):
            st.session_state["results"] = {}

            st.markdown("#### Agent Status")
            scols = st.columns(6)
            phs   = [c.empty() for c in scols]
            anames = ["🔍 Profile", "📊 Jobs", "📄 Resume",
                      "✉️ Cover Letter", "🎤 Interview", "📋 Report"]

            def set_status(idx, state):
                for j, (ph, an) in enumerate(zip(phs, anames)):
                    if j < idx:
                        ph.markdown("<div style='text-align:center;color:#2ea043'>" + an + "<br>✅ Done</div>",
                                    unsafe_allow_html=True)
                    elif j == idx:
                        color = "#f0e68c" if state == "running" else "#2ea043"
                        icon  = "🔄 Running" if state == "running" else "✅ Done"
                        ph.markdown("<div style='text-align:center;color:" + color + "'>" + an + "<br>" + icon + "</div>",
                                    unsafe_allow_html=True)
                    else:
                        ph.markdown("<div style='text-align:center;color:#8b949e'>" + an + "<br>⏳ Wait</div>",
                                    unsafe_allow_html=True)

            bar  = st.progress(0, text="Initializing...")
            info = st.empty()
            task_labels = ["Profile Analysis", "Job Research", "Resume Tailoring",
                           "Cover Letters", "Interview Prep", "Final Action Plan"]

            try:
                with st.spinner("Loading models..."):
                    llm, creative_llm = load_models(groq_key)
                with st.spinner("Setting up tools..."):
                    tools = build_tools(serper_key)

                crew, tasks = build_crew(profile, llm, creative_llm, tools)

                for i in range(6):
                    set_status(i, "running")
                    bar.progress(i / 6, text="Running agent " + str(i+1) + "/6: " + task_labels[i])
                    info.info("Running: " + task_labels[i])

                result = crew.kickoff()

                set_status(5, "done")
                bar.progress(1.0, text="All agents done!")
                info.success("All 6 agents completed successfully!")

                labels = ["Profile Analysis", "Job Research", "Resume",
                          "Cover Letters", "Interview Prep", "Action Plan"]
                outputs = {}
                for label, task in zip(labels, tasks):
                    out = getattr(task, "output", None)
                    outputs[label] = str(out.raw) if out and hasattr(out, "raw") else str(out or "")
                outputs["Final Result"] = str(result)
                st.session_state["results"] = outputs

                st.divider()
                st.markdown("### Results")
                icons2 = ["🔍", "💼", "📄", "✉️", "🎤", "🏆"]
                for icon2, (label, content) in zip(icons2, outputs.items()):
                    if label == "Final Result":
                        continue
                    with st.expander(icon2 + " " + label, expanded=(label == "Action Plan")):
                        st.markdown(content)

                st.divider()
                st.markdown("### Master Career Action Plan")
                st.markdown(outputs.get("Final Result", ""))

                st.divider()
                st.markdown("### Download Results")
                dl1, dl2 = st.columns(2)
                full = "\n\n---\n\n".join(["# " + k + "\n\n" + v for k, v in outputs.items()])
                with dl1:
                    st.download_button(
                        "📥 Download Full Report (.md)", data=full,
                        file_name="career_plan_" + profile.get("name", "candidate").replace(" ", "_") + ".md",
                        mime="text/markdown", use_container_width=True
                    )
                with dl2:
                    st.download_button(
                        "📥 Download Action Plan (.md)",
                        data=outputs.get("Final Result", ""),
                        file_name="master_action_plan.md",
                        mime="text/markdown", use_container_width=True
                    )

            except Exception as e:
                st.error("Error: " + str(e))
                st.markdown("**Troubleshooting:**")
                st.markdown("- Check API keys are correct in the sidebar")
                st.markdown("- Ensure `pydantic==1.10.13` is in `requirements.txt`")
                st.markdown("- Check Streamlit Cloud logs for the full traceback")

        elif st.session_state.get("results"):
            st.success("Results from previous run:")
            for label, content in st.session_state["results"].items():
                if label == "Final Result":
                    continue
                with st.expander("📄 " + label):
                    st.markdown(content)

# ─── TAB 3: SKILL ANALYSIS ──────────────────────────────────────────
with tab3:
    st.markdown("### Skill Gap Analysis")
    st.markdown("Semantic similarity between your skills and typical Senior ML Engineer requirements.")
    profile = st.session_state.get("profile", {})
    if not profile.get("technical_skills"):
        st.warning("Fill in the Candidate Profile tab first.")
    else:
        if st.button("Run Skill Gap Analysis", use_container_width=True):
            with st.spinner("Computing semantic similarity..."):
                try:
                    fig, overall, matched, total = skill_chart(profile)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Overall Match",    str(round(overall * 100, 1)) + "%")
                    m2.metric("Requirements Met", str(matched) + "/" + str(total))
                    m3.metric("Skill Gaps",       str(total - matched) + " to develop")
                    st.pyplot(fig)
                    st.markdown(
                        "**Legend:** Green = requirement met (score >= 0.55) · "
                        "Red = skill gap (score < 0.55)"
                    )
                except Exception as e:
                    st.error("Chart error: " + str(e))
