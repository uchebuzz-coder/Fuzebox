# Upwork Screening Questions & Evaluation Rubric

## Pre-Interview Screening Questions

Send these with the job invite or as initial chat messages:

---

### Question 1: Portfolio (Required)
> Share a link to a deployed Streamlit application you've built. Briefly describe what it does and any technical challenges you solved.

**What to look for:** Working URL, clean UI, evidence they understand Streamlit's execution model (caching, session state, reruns).

---

### Question 2: Quick Assessment Task (Required)
> Clone the repo (link provided after NDA/invite), run it locally, and send me:
> 1. A screenshot of the dashboard running with demo data loaded
> 2. How long it took you from clone to running
> 3. One thing you'd improve about the code or UI

**What to look for:**
- Got it running in < 30 minutes = strong candidate
- Identifies a real improvement (not just cosmetic) = thinks critically
- Clear communication = good to work with async

---

### Question 3: Agent/LLM Familiarity
> Have you worked with any AI agent frameworks (CrewAI, LangGraph, AutoGen, LangChain agents, or similar)? If yes, describe the project. If no, how would you approach learning one in 1-2 days?

**What to look for:** Direct experience is ideal, but a developer who can articulate a learning plan and has general API integration experience can ramp fast.

---

### Question 4: Observability Understanding
> In 2-3 sentences, explain what OpenTelemetry traces and spans are, and why they'd be useful for monitoring AI agent workflows.

**What to look for:** Understands parent-child span relationships, traces as end-to-end request tracking. Bonus: mentions distributed tracing challenges specific to async/multi-agent systems.

---

### Question 5: Working Style
> This project requires fast iteration with real-time feedback. How do you prefer to work — async (Slack/Loom) or sync (Zoom)? What's your typical response time during working hours?

**What to look for:** Response time < 2 hours during their working hours. Comfortable with either async or sync. Flexible timezone overlap.

---

## Evaluation Rubric

Score each candidate 1-5 on these dimensions:

| Dimension | Weight | 1 (Poor) | 3 (Adequate) | 5 (Excellent) |
|-----------|--------|-----------|---------------|----------------|
| **Streamlit skill** | 30% | No portfolio | Has a basic app | Deployed, polished app with caching/state |
| **Setup speed** | 20% | Couldn't run it | Ran in 30-60 min | Ran in < 15 min, found issues |
| **AI/Agent knowledge** | 20% | No exposure | Read docs, conceptual | Built agent workflows in production |
| **Communication** | 15% | Slow, vague | Clear, responsive | Proactive, asks good questions |
| **Code quality sense** | 15% | No improvement ideas | Cosmetic suggestions | Identifies architectural improvements |

**Hire threshold:** Weighted score >= 3.5

---

## Interview Flow (15-minute Zoom)

If a candidate passes screening:

1. **(2 min)** Show them the dashboard running, walk through the 6 pages
2. **(3 min)** Ask: "If you had to connect this to a real CrewAI workflow and show live data flowing in, how would you approach it?"
3. **(3 min)** Ask: "The POV needs to impress non-technical executives. What would you change about the current UI?"
4. **(3 min)** Ask: "Walk me through how you'd add a PDF export of the scorecard page"
5. **(2 min)** Discuss availability, rate, and start date
6. **(2 min)** Questions from them

---

## Red Flags

- Can't get the repo running without hand-holding
- Only suggests visual changes, no architectural thinking
- Response time > 24 hours during screening
- No experience with data visualization or dashboards
- Uncomfortable with ambiguity ("I need a complete spec before starting")

## Green Flags

- Asks clarifying questions about the business goals of the POV
- Suggests improvements you hadn't thought of
- Has deployed Streamlit apps with real data pipelines
- Mentions caching strategies, session state management
- Proactively shares progress updates without being asked

---

## Contract Structure Recommendation

1. **Phase 1 — Ramp & Polish (hourly, 5-10 hrs)**
   - Get running, deploy to Streamlit Cloud, UI polish
   - Milestone: Dashboard accessible via public URL

2. **Phase 2 — Live Integration (hourly, 10-15 hrs)**
   - Connect to a real agent framework (CrewAI/LangGraph)
   - Add scenario builder UI
   - Milestone: Live demo with real agent telemetry flowing

3. **Phase 3 — POV Delivery (fixed price)**
   - Export/reporting features
   - Presentation mode
   - Final polish and stakeholder walkthrough prep
   - Milestone: POV deck + live demo ready for decision-makers

Total estimated budget: **$1,000 - $2,500** depending on depth of live integration.
