# 06 — Presentation Tips: Coaching Guide for Your Two Slots

> **Your Slots:**
> - 11:35–12:10 — LLM Session (35 min)
> - 3:00–3:35 — Live Demo Session (35 min)

---

## SLOT 1: LLM Session (35 minutes) — Complete Verbal Flow

### Minute 0–3: Opening Hook

**Walk up and say:**

> *"Let me ask you something. How many of you have used ChatGPT or some AI chatbot?"*

(Wait for hands.)

> *"Great. Now, how many of you have been frustrated because it made something up? Gave you a confident wrong answer?"*

(Wait for nods.)

> *"That's called hallucination. And it's the biggest problem in AI right now. Today I'm going to show you how we fix it. Not with a better model. Not with more training data. With three simple tools and a pattern called ReAct."*

### Minute 3–10: What Is an LLM? (Concept)

**Key concepts to cover in order:**

1. **LLMs are pattern completion machines** — they predict the next word based on everything they've seen during training. They're incredibly good at understanding language, but they don't have access to your specific data.

2. **The knowledge cutoff problem** — the model we're using (Qwen 3, 32 billion parameters) was trained on data up to a certain date. It doesn't know what phones are in our Amazon database right now.

3. **Temperature = creativity dial** — we set temperature to 0, which means deterministic: same input → same output. In creative tasks you'd turn it up. For database queries, you want zero creativity.

**Say:**
> *"Think of the LLM as a brilliant consultant who's read every textbook ever written — but has never stepped foot in your office. They don't know your databases, your customers, or your inventory. They need a way to look things up."*

### Minute 10–18: Tool Calling (The Bridge)

**Transition:**
> *"So how do we bridge that gap? Tool calling."*

**Cover these points:**

1. **What is a tool?** — A function the LLM can call. It has a name, a description, and parameters. Show the three tools on screen:
   - `get_all_tables` — "List what data is available"
   - `get_table_schema` — "What columns does this table have?"
   - `execute_query` — "Run this SQL and give me the results"

2. **How does the LLM know which tool to use?** — It reads the tool descriptions. The LLM doesn't run code directly — it outputs a structured request saying "I want to call this tool with these parameters." The system executes it and feeds the result back.

3. **Live code walkthrough** — Open `src/analytics_agents/tools/postgres_tool.py` and show:
   ```python
   @property
   def tool_execute_query(self):
       return StructuredTool(
           name="execute_query",
           description="Execute SQL queries against Postgres.",
           func=self.execute_query,
           args_schema=ExecuteQueryInput,
       )
   ```
   > *"That's a tool. Four things: a name, a description, a function, and a schema. The LLM reads the name and description to decide when to use it."*

### Minute 18–28: The ReAct Pattern (The Loop)

**Transition:**
> *"Now here's where it gets interesting. The LLM doesn't just call one tool. It thinks, acts, observes, and repeats. This pattern has a name: ReAct."*

**Cover these points:**

1. **The loop:** Thought → Action → Observation → (repeat) → Answer
   - **Thought:** "I need to know what tables exist"
   - **Action:** Call `get_all_tables()`
   - **Observation:** "brands, cpu_models, operating_systems, phones, phone_specs"
   - (Loop again)
   - **Thought:** "I need the phones schema"
   - **Action:** Call `get_table_schema("phones")`
   - etc.

2. **Show the system prompt** — Open `standalone_text_to_sql_agent.py` and scroll to the `PROMPT_TEMPLATE`. Read out the key section:
   > *"This is what we tell the LLM before every conversation. 'You are an expert Text-to-SQL ReAct Agent. Follow the pattern: Thought, Action, Observation. Do not hallucinate table names. Always run the query.' These are the guardrails."*

3. **Live trace** — Ask a question and narrate the logs in real-time:
   > *"Watch the terminal. There — it's thinking... It called get_all_tables first... Now it's checking the schema... Now it's writing SQL... There's the query executing... And here comes the answer."*

### Minute 28–33: Live Demo

**Run the CLI agent:**
```bash
cd data_bot/analytics_agent
uv run --env-file .env src/main_cli.py
```

**Ask these questions in order (build complexity):**

1. **Simple:** "How many phones are in the database?"
   > *Narrate: "One tool call — execute_query with a COUNT(*). Simple."*

2. **Medium:** "What is the most expensive phone?"
   > *Narrate: "Notice how it checked the schema first. It needs to know the column name for price."*

3. **Complex:** "Recommend me a Samsung phone under $500 with good specs"
   > *Narrate: "This one is interesting because there's no 'good specs' column. Watch how the LLM interprets that — it'll probably look at RAM and ratings as proxies."*

### Minute 33–35: Closing

**Say:**
> *"So here's the takeaway: an LLM alone is a chatbot. Add tools and the ReAct pattern, and it becomes an agent — something that can reason, act, and deliver real answers from real data. That's the jump from impressive tech demo to useful system."*

---

## SLOT 2: Live Demo Session (35 minutes) — Complete Verbal Flow

### Minute 0–3: Opening Hook

**Say:**
> *"Alright, theory time is over. In the last session I showed you how the LLM works. Now I'm going to show you the whole system running end to end — data, AI, web, all connected. And then we're going to break it."*

### Minute 3–10: Direct Agent Demo (Approach A)

**Step 1:** Show the running FastAPI server
```bash
cd data_bot/analytics_agent
make run_ui
```

**Step 2:** Open the CopilotKit frontend in the browser
- Navigate to `http://localhost:3000`
- Show the chat interface

**Step 3:** Ask a question in the chat:
```
What Samsung phones are available under $500?
```

**Narrate while waiting:**
> *"Right now, the message went from the browser to Next.js, from Next.js to FastAPI, from FastAPI to the LLM. The LLM is running the ReAct loop — checking tables, checking schemas, writing SQL. Watch the backend terminal..."*

Point out the server logs showing tool calls.

**Step 4:** Ask a follow-up:
```
Which one has the best ratings?
```

> *"Notice it remembers the context from the previous question. That's the InMemorySaver — it keeps conversation history so the agent can handle follow-ups."*

### Minute 10–18: MCP Demo (Approach B)

**Transition:**
> *"Now let me show you a different way to build the same system. Instead of hardcoding the tools into the agent, we're going to use the Model Context Protocol — MCP."*

**Step 1:** Open `src/mcp_server/main.py` and show the three `@mcp.tool()` functions
> *"Same three tools — but exposed as a service. Any MCP client can discover and use these tools."*

**Step 2:** Start the MCP server
```bash
make mcp_serve
```

**Step 3:** In a new terminal, start the MCP client
```bash
make run_mcp
```

**Step 4:** Ask the SAME question:
```
What Samsung phones are available under $500?
```

**Narrate the difference:**
> *"Same question. Same answer. But the architecture is completely different. In Approach A, the tools were imported directly. In Approach B, the client discovered them at runtime from the server. If I added a new tool to the server — say, a web search tool — the client would automatically be able to use it without any code changes."*

### Minute 18–22: The Punchline — Why MCP Matters

**Use this analogy:**
> *"Think about your phone. Right now you have apps on it. Each app was individually downloaded and installed. That's Approach A — hardcoded tools.*
>
> *Now imagine if your phone could automatically discover and use any service in the cloud without installing anything. Need a calculator? It finds one. Need a translator? It finds one. That's MCP — plug-and-play tools for AI agents.*
>
> *The difference is: hardcoded means you decide upfront what the agent can do. MCP means the agent discovers what it can do at runtime. That's the difference between a Swiss Army knife and a toolbox."*

### Minute 22–30: Load Balancing / Chaos Engineering Demo

**Transition:**
> *"Now let me show you what happens when real users show up."*

**Step 1:** Stop the MCP demo. Keep the direct agent running.

**Step 2:** Show the load-balanced setup
```bash
make loadbalance
```

> *"I'm starting two identical copies of our agent behind Nginx — a load balancer that distributes requests round-robin."*

**Step 3:** Hit the health endpoint multiple times
```bash
curl http://localhost:3050/health
curl http://localhost:3050/health
```

> *"Both healthy. Nginx is alternating between them."*

**Step 4:** Kill one agent
```bash
docker kill $(docker ps -q --filter name=agent_1 | head -1)
```

> *"I just killed agent_1. Is the system down?"*

```bash
curl http://localhost:3050/health
```

> *"Nope. Still works. Nginx routed to agent_2 automatically. And Docker will restart agent_1 in a few seconds."*

**Step 5:** If time permits, run a basic load test to show the difference.

### Minute 30–33: Tying It All Together

**Say:**
> *"Let me zoom out for a second. Today you've seen the entire journey:*
>
> *1. We scraped real data from Amazon — messy, incomplete, full of noise.*
> *2. We cleaned and normalized it into a proper database — five related tables.*
> *3. We built an AI agent that can reason about that data — not by memorizing it, but by querying it.*
> *4. We connected it to a web frontend so real users can chat with it.*
> *5. We scaled it horizontally and proved it survives server failures.*
>
> *That's a complete, production-ready AI system. Every part connects to the next. Data feeds AI. AI powers the web. Infrastructure keeps it running."*

### Minute 33–35: Closing Line

**Deliver this slowly and deliberately:**

> *"Here's what I want you to remember from today: Data without AI is just a spreadsheet. AI without data is just a hallucination machine. And both without infrastructure are just a demo that breaks in production. It takes all three — data, intelligence, and systems — to build something real. And you just saw all three work together."*

---

## 5 Things That Could Go Wrong During the Live Demo (And How to Recover)

### 1. Backend Crashes at Startup

**What happens:** You run `make run_ui` and get an error about missing environment variables or PostgreSQL connection refused.

**Recovery:**
> *"Looks like our database connection isn't ready. Let me fix that."*

Check `.env` file. If PostgreSQL is down: *"This actually makes my point — this is why we need resilience. Let me restart the database and try again."*

If it's a Pydantic validation error for `LLM_CONFIG`: add `LLM_CONFIG={}` to `.env`.

### 2. LLM Returns an Error or Rate Limit

**What happens:** The agent says something like "Error: Rate limit exceeded" or returns gibberish.

**Recovery:**
> *"We just hit the API rate limit — Groq's free tier has limits on how many requests you can make per minute. In production, you'd use a paid tier or a fallback provider. Let me wait 30 seconds and try again."*

Wait, then retry. If it persists, switch topics: *"Let me show you the code while we wait for the rate limit to reset."*

### 3. Chat UI Shows Nothing / Hangs

**What happens:** You type a question in the CopilotKit chat and nothing comes back.

**Recovery:**
1. Check: Is the backend running? (Look at the terminal)
2. Check: Is `AGENT_URL` set correctly? (Should be `http://localhost:3050`)
3. Fallback: *"The web UI needs a moment. Let me show you the same agent in the terminal instead."* Then use `make run_cli` or `make run_mcp`.

### 4. Docker Build Takes Too Long

**What happens:** `make loadbalance` starts building and the audience watches a progress bar for 3 minutes.

**Recovery:**
Pre-build before the demo: `docker compose build`. Then `make loadbalance` will start instantly.

If you forgot to pre-build: *"Docker is building our containers. While it works, let me show you the docker-compose.yaml and explain what's happening."* Walk through the config on screen.

### 5. The Agent Gives a Wrong Answer

**What happens:** You ask "What's the cheapest phone?" and the agent returns something obviously wrong.

**Recovery:**
> *"Interesting — the agent got this one wrong. Let me trace what happened."*

Look at the server logs and find the SQL it generated. Show the audience:
> *"See — it wrote this SQL, but it missed a condition. This is why testing matters. The agent is only as good as the tools and the prompt we give it. Let me rephrase the question..."*

This is actually a great teaching moment — it shows the system is real, not scripted.

---

## How to Explain Agent vs MCP to a Student Audience With No Prior Knowledge

### The Phone Analogy

> *"Let me use an analogy everyone here can relate to — your phone.*
>
> *Approach A — the Direct Agent — is like having a phone where every app is built in. The calculator, the camera, the messaging — they're all baked into the firmware. You can't add new ones, you can't remove old ones. They work great, but they're rigid.*
>
> *Approach B — the MCP Agent — is like having an app store. The phone itself doesn't have any apps pre-installed. Instead, it can discover apps at runtime: 'What tools are available? A calculator? A translator? A database tool? Great, I'll use those.' And if someone publishes a new app tomorrow, your phone can use it without an update.*
>
> *That's the difference. Hardcoded vs. plug-and-play. Both work. But one scales, and the other doesn't."*

### The Hardcoded vs Plug-and-Play Framing

> *"Let me put it simply:*
>
> *Hardcoded means: 'I know exactly what tools I have, and they never change.'*
> *Plug-and-play means: 'I discover what tools exist, and I can use new ones without changing my code.'*
>
> *In a small project, hardcoded is fine. In a company with 50 AI agents that all need different tools? Plug-and-play wins. That's MCP."*

---

## 3 Questions Students Are Likely to Ask (And Strong Answers)

### Question 1: "Can the agent run any SQL? What stops it from deleting data?"

**Answer:**
> *"Great question. Right now, the agent can run any SQL the database user allows. In production, you'd use a read-only database user — one that can SELECT but not INSERT, UPDATE, or DELETE. You'd also add query validation in the tool: check that the SQL starts with SELECT, reject anything with DROP or DELETE. Our tool also limits results to 100 rows, which prevents the agent from accidentally dumping the entire database. Security is about layering restrictions, not trusting the LLM to be careful."*

### Question 2: "Why not just use ChatGPT/Claude directly? Why build all this?"

**Answer:**
> *"ChatGPT doesn't know about your data. It's trained on the internet, not your Amazon phone database. Even if you paste your data into the chat, you're limited by context windows, you can't handle real-time updates, and you have no security control over what data is shared. This system keeps your data private — the LLM only sees query results, not your entire database. Plus, this system can be deployed as a product — ChatGPT can't run your customer-facing phone recommendation bot."*

### Question 3: "How much does it cost to run this in production?"

**Answer:**
> *"Surprisingly little for a demo like this. Groq has a generous free tier for the Qwen model. PostgreSQL is free and open source. Docker is free. The main production costs are: LLM API calls (typically $0.001-0.01 per request depending on the model), server hosting (a basic cloud VM for $20-50/month can handle this), and PostgreSQL hosting (managed databases start at $10-15/month). For a small-to-medium deployment, you're looking at $50-100/month. That's less than one engineer's daily coffee budget."*

---

## One Powerful Closing Line

Use this at the very end of the day, or at the end of your demo slot. Deliver it slowly, make eye contact with the room:

> *"Data without AI is just a spreadsheet. AI without data is just a hallucination machine. And both without infrastructure are just a demo that breaks in production. It takes all three — data, intelligence, and systems — to build something real. And today, you built all three."*

---

## Demo Risk Flags (Summary of All Risks for Your Slots)

| Risk | Slot | Quick Fix |
|---|---|---|
| `.env` missing or misconfigured | Both | Have a known-good `.env` ready. Copy it fresh before the demo. |
| PostgreSQL not running | Both | Run `pg_isready` before your slot. Keep the DuckDB fallback in mind (uncomment in `dependencies.py`). |
| Groq rate limit | LLM session | Wait 60 seconds. Switch to explaining the code. Have a pre-recorded output video as backup. |
| `LLM_CONFIG` env var missing | Both | Set `LLM_CONFIG={}` in `.env` — even if not using Azure, Pydantic requires it. |
| Frontend AGENT_URL wrong | Live Demo | Set `AGENT_URL=http://localhost:3050` in `ui/.env.local`. |
| Docker not pre-built | Live Demo | Run `docker compose build` before your slot starts. |
| MCP client fails (exit code 2) | Live Demo | This has happened before in the workspace. Test `make mcp_serve` + `make run_mcp` before the demo. If broken, skip to explaining the code visually instead. |
| Projector can't show dark terminal | Both | Increase font size. Use a light terminal theme if needed. Keep browser zoom at 150%+. |
