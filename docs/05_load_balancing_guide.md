# 05 — Load Balancing Guide: Chaos Engineering & Horizontal Scaling

> **Session:** 3:35–4:50 — Load Balancing: Chaos engineering, horizontal scaling demo

---

## 1. How the Load Balancer Is Set Up

### The Architecture

```
                        ┌──────────────────┐
                        │  Client/Browser  │
                        └────────┬─────────┘
                                 │ :3050
                                 ▼
                        ┌──────────────────┐
                        │     Nginx        │
                        │  (Load Balancer) │
                        │   Port 80 → 3050 │
                        └───┬──────────┬───┘
                            │          │
                   Round    │          │   Round
                   Robin    │          │   Robin
                            ▼          ▼
                    ┌────────────┐ ┌────────────┐
                    │  agent_1   │ │  agent_2   │
                    │ FastAPI    │ │ FastAPI    │
                    │  :3050     │ │  :3050     │
                    └──────┬─────┘ └─────┬──────┘
                           │             │
                           └──────┬──────┘
                                  ▼
                        ┌──────────────────┐
                        │   PostgreSQL     │
                        │ (host machine)   │
                        └──────────────────┘
```

### The Files

| File | Purpose |
|---|---|
| `docker-compose.yaml` | Orchestrates 3 containers: agent_1, agent_2, and nginx |
| `Dockerfile` | Builds the agent container image (Python 3.12 + FastAPI) |
| `nginx/nginx.conf` | Nginx configuration — defines the load balancing strategy |
| `nginx/Dockerfile` | Builds the nginx container image |

### Load Balancing Algorithm: Round Robin

The nginx configuration uses **round-robin** — the default and simplest algorithm. Requests are distributed evenly: first request → agent_1, second → agent_2, third → agent_1, and so on.

**`nginx/nginx.conf`** (the complete file):
```nginx
upstream agents {
    server agent_1:3050;
    server agent_2:3050;
}

server {
    listen 80;
    
    include /etc/nginx/mime.types;

    location / {
        proxy_pass http://agents/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**What each part means:**
- `upstream agents { ... }` — defines a pool of backend servers (agent_1 and agent_2, both on port 3050)
- `server { listen 80; }` — nginx listens on port 80 inside the container
- `proxy_pass http://agents/` — forwards incoming requests to the upstream pool
- `proxy_set_header` — passes the real client IP to the backend (useful for logging)

### Docker Compose Configuration

**`docker-compose.yaml`:**
```yaml
version: '3'
services:
  agent_1:
    build: .
    restart: on-failure
    env_file:
      - .env
    environment:
      - PORT=3050
      - POSTGRES_HOST=host.docker.internal
    networks:
      - loadbalancing
    extra_hosts:
      - "host.docker.internal:host-gateway"

  agent_2:
    build: .
    restart: on-failure
    env_file:
      - .env
    environment:
      - PORT=3050
      - POSTGRES_HOST=host.docker.internal
    networks:
      - loadbalancing
    extra_hosts:
      - "host.docker.internal:host-gateway"

  nginx:
    build: ./nginx
    container_name: nginx
    ports:
      - "3050:80"
    networks:
      - loadbalancing
    depends_on:
      - agent_1
      - agent_2

networks:
  loadbalancing:
```

**What each part means:**
- `agent_1` and `agent_2` are **identical FastAPI containers** built from the same Dockerfile
- `restart: on-failure` — if a container crashes, Docker automatically restarts it
- `POSTGRES_HOST=host.docker.internal` — connects to PostgreSQL running on the host machine (not inside Docker)
- `extra_hosts` — resolves `host.docker.internal` to the Docker host's IP
- Nginx exposes port `3050` externally, maps to port `80` internally
- All three containers share the `loadbalancing` Docker network

### The Agent Dockerfile

```dockerfile
FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY Makefile .
COPY pyproject.toml .
RUN uv sync --no-cache
ADD src /app/src

CMD ["uv", "run", "/app/src/main.py"]
```

---

## 2. How to Spin Up the Load-Balanced System

### Start Everything

```bash
cd data_bot/analytics_agent
make loadbalance
```

This runs `docker compose up --build`, which:
1. Builds the agent Docker image (installs Python dependencies)
2. Builds the nginx Docker image
3. Starts agent_1, agent_2, and nginx
4. Nginx begins load-balancing on port 3050

You should see logs from all three containers interleaved in the terminal.

### Verify It's Running

```bash
# Check health of the load-balanced system
curl http://localhost:3050/health
# Should return: {"status": "ok"}

# Run it multiple times — you'll hit different agents each time
curl http://localhost:3050/health
curl http://localhost:3050/health
```

### Stop Everything

```bash
make loadbalance_rm
```

This runs `docker compose down`, stopping and removing all containers.

---

## 3. How to Simulate 100 Concurrent Users and Make the Single Server Fail

### Step 1: First, Show the Single Server Working

Start just ONE agent (no load balancer):
```bash
make docker_run
# This builds and runs a single container on port 3050
```

Test it works:
```bash
curl http://localhost:3050/health
# Returns: {"status": "ok"}
```

### Step 2: Bombard It with Concurrent Requests

Use `ab` (Apache Bench), `hey`, or a simple script to send many concurrent requests:

**Option A: Using Apache Bench (ab)**
```bash
# Install if needed: sudo apt install apache2-utils
# Send 100 requests, 50 at a time (concurrent)
ab -n 100 -c 50 http://localhost:3050/health
```

**Option B: Using `hey` (Go-based HTTP load tool)**
```bash
# Install: go install github.com/rakyll/hey@latest
# Send 200 requests, 100 concurrent
hey -n 200 -c 100 http://localhost:3050/health
```

**Option C: Using a simple bash script**
```bash
# Fire 100 requests in parallel
for i in $(seq 1 100); do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3050/health &
done
wait
```

**Option D: Using Python (most versatile for demo)**
```python
import asyncio
import aiohttp
import time

async def make_request(session, url, request_id):
    try:
        start = time.time()
        async with session.get(url) as response:
            elapsed = time.time() - start
            return request_id, response.status, elapsed
    except Exception as e:
        return request_id, "FAILED", str(e)

async def main():
    url = "http://localhost:3050/health"
    n_requests = 100
    
    async with aiohttp.ClientSession() as session:
        tasks = [make_request(session, url, i) for i in range(n_requests)]
        start = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start
    
    successes = sum(1 for _, status, _ in results if status == 200)
    failures = sum(1 for _, status, _ in results if status != 200)
    
    print(f"Total time: {total_time:.2f}s")
    print(f"Successes: {successes}/{n_requests}")
    print(f"Failures: {failures}/{n_requests}")
    
    if failures > 0:
        print("SINGLE SERVER CANNOT HANDLE THE LOAD!")

asyncio.run(main())
```

### Step 3: Show the Failure (Chaos Engineering)

For the most dramatic demo, go beyond the health endpoint and hit the actual agent with real questions. This is where a single server truly struggles:

```bash
# Send many concurrent LLM requests (these are expensive)
for i in $(seq 1 20); do
  curl -s -X POST http://localhost:3050/copilotkit \
    -H "Content-Type: application/json" \
    -d '{"messages": [{"role": "user", "content": "What is the cheapest phone?"}]}' &
done
wait
```

With a single server, you'll see:
- Responses taking 10-30+ seconds (normally 2-3 seconds)
- Some requests timing out
- The server becoming unresponsive
- Possible 503 errors or connection resets

**Alternative: Kill one of the agents to simulate failure**

```bash
# With load balancing running, kill one agent
docker stop $(docker ps -q --filter name=agent_1)

# The system should still work because agent_2 is alive
curl http://localhost:3050/health
# Still returns: {"status": "ok"} (handled by agent_2)

# Docker will automatically restart agent_1 (restart: on-failure)
# After a few seconds, both agents are back
```

---

## 4. What the Failure Looks Like and How to Narrate It

### Narration Script: The Breaking Point

> *"Right now we have a single server handling all requests. Let me show you what happens when real users show up."*

Run the load test.

> *"I just sent 100 concurrent requests to our agent. Watch the response times... See how they're climbing? 5 seconds... 10 seconds... some are timing out entirely. That's because one server can only handle so many connections at once. Each LLM call takes 2-3 seconds of processing, and they're all fighting for the same CPU and memory."*

Show the terminal output:
> *"Look — we got failures. [X] out of 100 requests failed. In production, that means [X] users see an error screen instead of an answer. That's not acceptable."*

### Narration Script: The Fix

> *"Now let me show you horizontal scaling. Same code, same database, same everything — but two copies of the server behind a load balancer."*

Start the load-balanced setup:
```bash
make loadbalance
```

> *"I'm starting two identical agent servers behind Nginx. Nginx uses round-robin — first request goes to server 1, second goes to server 2, alternating back and forth."*

Run the same load test again:

> *"Same 100 requests. Watch the difference... All requests completing. No timeouts. No failures. That's because each server is only handling half the load. If we needed more capacity, we'd just add agent_3, agent_4 — same Dockerfile, just add another line to the nginx config."*

### Narration Script: Chaos Engineering

> *"But here's the real magic — fault tolerance. Let me kill one of the servers while requests are flowing."*

```bash
docker stop $(docker ps -q --filter name=agent_1)
```

> *"I just killed agent_1. Is the system down? Let's check..."*

```bash
curl http://localhost:3050/health
```

> *"Still working. Nginx detected that agent_1 is gone and routes everything to agent_2. And in a few seconds, Docker will restart agent_1 automatically because we set `restart: on-failure`. This is what production resilience looks like."*

---

## 5. How the Load Balancer Fixes It — Step by Step

### Without Load Balancer (Single Server)

```
100 requests → 1 server (3050)
         │
         ▼
Server: "I can handle ~10 concurrent requests comfortably"
Requests 1-10: ✅ ~2-3 seconds
Requests 11-30: ⚠️ ~5-10 seconds (queuing)
Requests 31-60: 😰 ~15-30 seconds (severe queuing)
Requests 61-100: ❌ Timeouts, 503 errors, connection resets
```

### With Load Balancer (Two Servers)

```
100 requests → Nginx (3050)
         │
    ┌────┴────┐
    ▼         ▼
agent_1    agent_2
(50 req)   (50 req)
    │         │
    ▼         ▼
Server 1: handles 50    Server 2: handles 50
Requests: ✅ ~2-5 sec   Requests: ✅ ~2-5 sec
```

### Why This Works

1. **Request Distribution** — Nginx splits traffic evenly (round-robin), so each server handles half the load
2. **Independent Processing** — Each agent runs in its own container with its own CPU/memory allocation
3. **Shared Database** — Both agents connect to the same PostgreSQL instance, so they always return consistent data
4. **Automatic Recovery** — `restart: on-failure` means Docker restarts crashed containers
5. **Health Checking** — Nginx can detect when an upstream server is down and stop sending it traffic

---

## 6. Key Talking Points

### Talking Point 1: Why This Matters for AI Systems

> "LLM calls are expensive — each request takes 2-5 seconds of processing. Unlike a simple web page that returns in 50ms, an AI agent might need to make 3-4 LLM calls before answering. That means each user request holds a server connection for 10-15 seconds. Load balancing isn't optional for production AI — it's essential."

### Talking Point 2: Horizontal vs Vertical Scaling

> "Vertical scaling means getting a bigger server. Horizontal scaling means getting more servers. Vertical has a ceiling — you can only make one machine so big. Horizontal has no ceiling — you can keep adding servers. Our Docker Compose approach is horizontal scaling: same container, duplicated."

### Talking Point 3: The Cost of Downtime

> "Every request that fails is a user who doesn't get their answer. If you're running a phone recommendation agent for a business, each failed request is potentially a lost sale. The load balancer isn't just about performance — it's about reliability."

### Talking Point 4: Infrastructure as Code

> "Notice how our entire load balancing setup is defined in code: `docker-compose.yaml` and `nginx.conf`. We can version it, review it, test it, and deploy it reproducibly. That's infrastructure as code."

### Talking Point 5: Chaos Engineering Philosophy

> "Netflix invented chaos engineering — they literally kill random servers in production to test resilience. We're doing the same thing: kill an agent, watch the system survive. If your system can't handle a server dying, it's not production-ready."

---

## Demo Risk Flags

| Risk | Impact | Mitigation |
|---|---|---|
| **Docker not installed** | Entire demo section fails | Verify before the bootcamp: `docker --version && docker compose version` |
| **Docker Compose build takes too long** | Audience waits 2-5 minutes watching a build | Pre-build the images before the demo: `docker compose build` (without `up`). Then `make loadbalance` will start instantly. |
| **PostgreSQL not accessible from Docker** | Agents start but can't connect to database | The `host.docker.internal` hostname is used. On Linux, `extra_hosts` must be set (it already is in `docker-compose.yaml`). Test: start one agent container and check it can reach PostgreSQL. |
| **Port 3050 already in use** | Nginx can't bind to it | Stop any existing agent before running `make loadbalance`. Run `docker stop $(docker ps -q)` to stop all containers. |
| **Load test tool not installed** | Can't demonstrate the failure | Install before demo: `sudo apt install apache2-utils` (for `ab`). Or use the bash `curl` loop as a fallback. |
| **Single server doesn't visibly fail** | The "before load balancing" demo is underwhelming | Use real agent queries (POST to `/copilotkit`), not just health checks. LLM calls are much heavier than health checks. Send at least 20 concurrent requests. |
| **Docker pulls images slowly on conference WiFi** | Build takes forever | Pre-pull base images: `docker pull python:3.12-slim-trixie && docker pull nginx:stable-alpine` |
| **Both agents crash at the same time** | Nginx returns 502 Bad Gateway | This is unlikely but possible if both run out of memory. Monitor with `docker stats`. |
| **`restart: on-failure` doesn't work as expected** | Killed container doesn't come back automatically | `docker stop` sends SIGTERM which is a clean exit, not a failure. Use `docker kill` for a harder kill that triggers the restart policy. Or just restart manually: `docker start <container>`. |
| **Audience asks about other algorithms** | You need more than round-robin to explain | Nginx supports `least_conn` (route to the server with fewest active connections), `ip_hash` (sticky sessions), and `weighted` (route more traffic to stronger servers). Mention these as "advanced options" but keep the demo on round-robin for simplicity. |
