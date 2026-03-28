# 04 — Web Integration Guide: CopilotKit Frontend

> **Session:** 2:15–3:00 — Web Integration: CopilotKit, connecting systems to web apps

---

## 1. Which Files Make Up the Frontend

The frontend lives in `data_bot/ui/` and is a **Next.js 16** application using the App Router:

| File | Purpose |
|---|---|
| `app/layout.tsx` | Root layout — wraps the entire app in the `<CopilotKit>` provider |
| `app/page.tsx` | Home page — renders the `<CopilotChat>` component (the chat window) |
| `app/api/copilotkit/route.ts` | API route — bridges the frontend UI to the FastAPI backend agent |
| `app/globals.css` | Global styles — Tailwind CSS imports + dark/light mode variables |
| `app/test.tsx` | A simple counter component (not connected to the agent — likely a dev test) |
| `package.json` | Node.js dependencies and scripts |
| `next.config.ts` | Next.js configuration (Turbopack, remote image patterns) |
| `tsconfig.json` | TypeScript configuration |
| `postcss.config.mjs` | PostCSS config (for Tailwind processing) |
| `eslint.config.mjs` | ESLint rules |

### Key Dependencies

```json
{
  "@copilotkit/react-core": "^1.50.0",   // CopilotKit React context provider
  "@copilotkit/react-ui": "^1.50.0",     // Pre-built chat UI components
  "@copilotkit/runtime": "^1.50.0",      // Server-side CopilotKit runtime
  "next": "16.0.10",                      // Next.js framework
  "react": "19.2.1",                      // React UI library
  "react-dom": "19.2.1",                  // React DOM rendering
  "tailwindcss": "^4"                     // Utility-first CSS
}
```

---

## 2. How CopilotKit Is Configured and Connected to the Backend

The connection flows through **three layers**: Provider → Chat Component → API Route → Backend.

### Layer 1: The CopilotKit Provider (`layout.tsx`)

```tsx
import { CopilotKit } from '@copilotkit/react-core';
import '@copilotkit/react-ui/styles.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <CopilotKit runtimeUrl={'/api/copilotkit'} renderToolCalls={[]}>
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
```

**What this does:**
- `<CopilotKit runtimeUrl={'/api/copilotkit'}>` wraps the entire app and configures CopilotKit to send all chat messages to the **Next.js API route** at `/api/copilotkit`
- `renderToolCalls={[]}` — no custom tool call rendering (tool calls are handled transparently)
- Imports CopilotKit's default styles (`@copilotkit/react-ui/styles.css`)

### Layer 2: The Chat Component (`page.tsx`)

```tsx
'use client';

import { CopilotChat } from '@copilotkit/react-ui';

export default function Home() {
  return (
    <main className="h-screen w-full overflow-hidden bg-gray-950 text-white">
      <div className="flex h-full w-full flex-col">
        <CopilotChat
          className="h-full w-full"
          labels={{
            title: 'Copilot',
            initial: 'How can I help you today?',
          }}
        />
      </div>
    </main>
  );
}
```

**What this does:**
- Renders a full-screen dark-themed chat window
- `<CopilotChat>` is a pre-built component from `@copilotkit/react-ui` that handles:
  - Message input field
  - Message history display
  - Streaming response rendering
  - Loading states
- The `labels` prop customizes the title ("Copilot") and the initial welcome message

### Layer 3: The API Route (`app/api/copilotkit/route.ts`)

```typescript
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from '@copilotkit/runtime';
import { LangGraphHttpAgent } from '@copilotkit/runtime/langgraph';
import { NextRequest } from 'next/server';

const serviceAdapter = new ExperimentalEmptyAdapter();

const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphHttpAgent({
      url: process.env.AGENT_URL || 'http://localhost:8123',
    }),
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: '/api/copilotkit',
  });
  return handleRequest(req);
};
```

**What this does:**
- Creates a `CopilotRuntime` that knows about one agent: the `LangGraphHttpAgent`
- `LangGraphHttpAgent` points to the FastAPI backend (default: `http://localhost:8123`, overridable via `AGENT_URL` env var)
- The `POST` handler receives chat messages from the `<CopilotChat>` component and forwards them to the backend
- `ExperimentalEmptyAdapter` is used because the LLM logic lives in the backend, not in CopilotKit itself
- Responses are streamed back using the AG-UI protocol

---

## 3. How the Agent's Responses Flow Back to the UI

```
┌─────────────────────────────────────────────────────────┐
│ BROWSER                                                  │
│                                                          │
│  User types: "What's the cheapest phone?"               │
│       │                                                  │
│       ▼                                                  │
│  <CopilotChat> component sends POST to /api/copilotkit  │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP POST (message payload)
                           ▼
┌─────────────────────────────────────────────────────────┐
│ NEXT.JS API ROUTE (/api/copilotkit)                      │
│                                                          │
│  CopilotRuntime receives the request                    │
│  LangGraphHttpAgent forwards to backend                 │
│       │                                                  │
└───────┼─────────────────────────────────────────────────┘
        │ HTTP POST to AGENT_URL (default: localhost:8123)
        ▼
┌─────────────────────────────────────────────────────────┐
│ FASTAPI BACKEND (:3050)                                  │
│                                                          │
│  /copilotkit endpoint receives message                  │
│  LangGraph agent runs the ReAct loop                    │
│  Agent calls tools → queries PostgreSQL                  │
│  LLM generates final answer                             │
│       │                                                  │
│  Response streamed back via AG-UI protocol              │
└───────┼─────────────────────────────────────────────────┘
        │ Streaming response (token by token)
        ▼
┌─────────────────────────────────────────────────────────┐
│ NEXT.JS API ROUTE                                        │
│  Passes stream through to browser                       │
└───────┼─────────────────────────────────────────────────┘
        │ Streaming response
        ▼
┌─────────────────────────────────────────────────────────┐
│ BROWSER                                                  │
│                                                          │
│  <CopilotChat> renders tokens as they arrive            │
│  User sees answer appearing word by word                │
└─────────────────────────────────────────────────────────┘
```

Key detail: the response is **streamed**, not sent all at once. The user sees the answer appearing word by word, just like ChatGPT. This is handled by the AG-UI protocol between the FastAPI backend and CopilotKit.

---

## 4. What the User Experience Looks Like Step by Step

1. **User opens browser** → navigates to `http://localhost:3000`
2. **Chat window appears** — full screen, dark theme (bg-gray-950), with:
   - Title: "Copilot"
   - Welcome message: "How can I help you today?"
   - Text input at the bottom
3. **User types a question** — e.g., "What Samsung phones are under $500?"
4. **Loading indicator appears** — CopilotKit shows a thinking state
5. **Answer streams in** — word by word, the agent's response appears in the chat bubble
6. **Full response displayed** — includes the phone recommendations with prices
7. **User can ask follow-up questions** — the conversation thread is maintained (InMemorySaver on the backend keeps context)
8. **User can scroll through history** — previous messages and responses are visible

---

## 5. How to Set Up and Run the Frontend

### Step 1: Install Dependencies
```bash
cd data_bot/ui
pnpm install
```

### Step 2: Set Environment Variables

Create `data_bot/ui/.env.local`:
```bash
AGENT_URL=http://localhost:3050
```

**Critical:** The default `AGENT_URL` in the code is `http://localhost:8123`, but the FastAPI backend runs on port `3050`. If you don't set this env var, the frontend will try to connect to port 8123 and fail silently.

### Step 3: Start the Backend First
```bash
cd data_bot/analytics_agent
make run_ui   # Starts FastAPI on :3050
```

### Step 4: Start the Frontend
```bash
cd data_bot/ui
pnpm dev      # Starts Next.js on http://localhost:3000
```

Or to make it accessible on your local network (for audience screen sharing):
```bash
pnpm dev:network   # Binds to 0.0.0.0
```

---

## 6. Gotchas and Things That Could Go Wrong During a Live Demo

### Gotcha 1: AGENT_URL Mismatch (Most Common Issue)

**Symptom:** Chat loads, you type a question, but nothing happens. Or you get a vague error.

**Cause:** The default `AGENT_URL` in `route.ts` is `http://localhost:8123`, but the FastAPI backend actually runs on port `3050`.

**Fix:** Set `AGENT_URL=http://localhost:3050` in `data_bot/ui/.env.local` (or `.env`) and restart the Next.js dev server.

### Gotcha 2: CORS Errors

**Symptom:** Browser console shows "CORS policy" errors. Requests are blocked.

**Cause:** The FastAPI backend needs to allow requests from the Next.js frontend origin.

**Fix:** The backend already has CORS middleware configured to allow all origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
If this still fails, check that the backend is actually running.

### Gotcha 3: Backend Not Running

**Symptom:** Chat shows a loading state indefinitely, then errors out.

**Cause:** FastAPI server isn't running, or it crashed during startup.

**Fix:** Check the backend terminal. Look for error messages. Common causes:
- Missing `.env` file
- PostgreSQL not running
- Invalid `GROQ_API_KEY`
- `LLM_CONFIG` env var missing (Pydantic validation fails)

### Gotcha 4: Slow First Response

**Symptom:** First question takes 10-15 seconds. Subsequent ones are faster.

**Cause:** Cold start — the LLM needs to warm up, and the first database connection is established.

**Fix:** Ask a "warm-up" question before the demo starts (e.g., "How many phones are in the database?").

### Gotcha 5: CopilotKit Style Conflicts

**Symptom:** Chat window looks broken — misaligned elements, unstyled components.

**Cause:** Missing CopilotKit CSS or Tailwind conflicts.

**Fix:** Ensure `layout.tsx` imports `@copilotkit/react-ui/styles.css`. If styles are still broken, try clearing the `.next` cache: `rm -rf .next && pnpm dev`.

### Gotcha 6: Node.js Version Too Old

**Symptom:** Next.js 16 won't start, cryptic build errors.

**Cause:** Next.js 16 requires Node.js >= 20.9.0.

**Fix:** `node -v` to check. If too old: `nvm install 20 && nvm use 20`.

### Gotcha 7: pnpm Not Installed

**Symptom:** `pnpm: command not found`.

**Fix:** `npm install -g pnpm` or `corepack enable && corepack prepare pnpm@latest --activate`.

---

## Demo Risk Flags

| Risk | Impact | Mitigation |
|---|---|---|
| **AGENT_URL default is wrong (8123 instead of 3050)** | Frontend silently fails — chat appears to hang | Set `AGENT_URL=http://localhost:3050` in `.env.local` before the demo |
| **Backend crashes mid-demo** | Chat returns errors or hangs | Keep the backend terminal visible. Have a quick restart command ready: `make run_ui` |
| **Audience can't see the chat text (projector quality)** | Dark theme on dark background may wash out | Increase browser zoom to 150%. Consider temporarily switching to a light theme if projector is low-contrast. |
| **Chat doesn't stream (shows full response at once)** | Less impressive demo — streaming looks better | This depends on AG-UI protocol support. If streaming breaks, the response still arrives — just not incrementally. |
| **`test.tsx` shows up or confuses things** | Audience asks about the counter component | It's just a test file. If asked: "That's a simple React test we used during development. The real page is `page.tsx`." |
| **pnpm-lock.yaml out of sync** | Install fails with dependency conflicts | Run `pnpm install --no-frozen-lockfile` to resolve |
| **Port 3000 in use** | Next.js picks a different port (3001, etc.) | Either kill the existing process or tell the audience the new URL |
