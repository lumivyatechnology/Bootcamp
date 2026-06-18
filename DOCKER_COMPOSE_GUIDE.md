# 🐳 Docker Compose Guide (For First-Time Learners)

This guide explains the [`docker-compose.yaml`](docker-compose.yaml) file in the `Bootcamp`
folder **line by line**, in plain language. By the end you'll understand what it does,
why it's set up this way, and how to run it — even if you've never used Docker before.

---

## 1. What problem does Docker Compose solve?

The Lumivya bootcamp app is made of **two programs that must run together**:

1. **Backend** — a Python AI service (the "brain") that answers questions about phones.
2. **Frontend** — a Next.js web chatbot (the "face") that you open in your browser.

Running these by hand means installing Python, Node.js, all their libraries, setting
environment variables, and starting each one in the right order. That's a lot of steps,
and "it works on my machine" bugs are common.

**Docker** packages each program — plus everything it needs to run — into an isolated box
called a **container**. **Docker Compose** is a tool that lets you describe *all* your
containers in a single file and start them with **one command**.

> 💡 **Analogy:** A `Dockerfile` is a recipe for one dish. `docker-compose.yaml` is the
> menu that says which dishes to cook, how they connect, and the order to serve them.

---

## 2. Key vocabulary

| Term | Meaning |
|------|---------|
| **Image** | A frozen, ready-to-run snapshot of a program (built from a `Dockerfile`). |
| **Container** | A running copy of an image. You can start, stop, and delete it freely. |
| **Service** | A container defined in Compose (here: `backend` and `frontend`). |
| **Port** | A numbered "door" a program listens on (e.g. the web app on `3000`). |
| **Volume** | Storage that survives even after a container is deleted. |
| **Network** | A private virtual LAN so containers can talk to each other by name. |

---

## 3. The file, explained section by section

Here is the full file again for reference — each block is explained below.

### Services

```yaml
services:
```

This is the top-level list of containers we want to run. Everything indented under it is
one service. Our file has two: `backend` and `frontend`.

---

### The `backend` service

```yaml
  backend:
    build: ./backend
    container_name: lumivya-backend
    restart: unless-stopped
```

| Line | What it means |
|------|----------------|
| `build: ./backend` | Don't download a ready-made image — **build** one using the `Dockerfile` inside the `backend/` folder. |
| `container_name: lumivya-backend` | Give the running container a friendly, predictable name instead of a random one. |
| `restart: unless-stopped` | If the container crashes, **automatically restart it** — unless *you* deliberately stopped it. |

```yaml
    env_file:
      - ./backend/.env
    environment:
      - DB_HOST=host.docker.internal
      - DB_PORT=5432
      - DB_NAME=${DB_NAME:-postgres}
      - DB_USER=${DB_USER:-postgres}
      - DB_PASSWORD=${DB_PASSWORD:-postgres}
```

This is how the backend gets its **configuration and secrets**:

- `env_file` loads *all* the variables from `backend/.env` (your Langfuse keys, Groq API
  key, etc.). You create this file yourself by copying `backend/.env.example`.
- `environment` sets a few extra variables directly. These **override** anything with the
  same name from the env file.
- `${DB_NAME:-postgres}` means: *"use the `DB_NAME` value from my shell if it exists,
  otherwise fall back to `postgres`."* The `:-` is a default value.

> ⚠️ **Important — the database lives on YOUR machine, not in Docker.**
> `DB_HOST=host.docker.internal` is a special Docker hostname that means
> *"the host computer running Docker."* This Compose file does **not** start a PostgreSQL
> container — it expects you to already have PostgreSQL running locally on port `5432`.
> (You set this up earlier in the bootcamp during the ETL / data-loading step.)

```yaml
    ports:
      - "3050:3050"
```

This maps a port from inside the container to your computer. The format is
`HOST:CONTAINER`.

- The **right** number (`3050`) is the port *inside* the container where the backend listens.
- The **left** number (`3050`) is the port on *your computer* you use to reach it.

So after starting, you can visit `http://localhost:3050` on your machine.

```yaml
    networks:
      - app-network
```

Connects the backend to a private network named `app-network` (defined at the bottom of
the file). Containers on the same network can find each other **by their service name**.

```yaml
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import urllib.request; urllib.request.urlopen('http://localhost:3050/health')"
        ]
      interval: 10s
      timeout: 5s
      retries: 5
```

A **healthcheck** is how Docker decides whether the backend is *actually ready*, not just
"started." Here it runs a tiny Python script that pings the backend's `/health` endpoint.

- `interval: 10s` → check every 10 seconds.
- `timeout: 5s` → each check must answer within 5 seconds.
- `retries: 5` → only mark the container "unhealthy" after 5 failures in a row.

This matters because of what the frontend does next. 👇

---

### The `frontend` service

```yaml
  frontend:
    build: ./frontend
    container_name: lumivya-frontend
    restart: unless-stopped
    environment:
      - AGENT_URL=http://backend:3050/copilotkit
```

Same ideas as the backend, with one detail worth highlighting:

- `AGENT_URL=http://backend:3050/copilotkit` — notice the hostname is **`backend`**, not
  `localhost`. Because both containers share `app-network`, the frontend can reach the
  backend just by using its service name `backend`. Docker handles the address lookup
  automatically. This is the magic of Compose networking.

```yaml
    ports:
      - "3000:3000"
```

Exposes the web app on `http://localhost:3000` — this is the page **you** open in your
browser.

```yaml
    depends_on:
      backend:
        condition: service_healthy
```

This is the **startup order** rule:

> *"Do not start the frontend until the backend reports it is **healthy**."*

This is why the healthcheck above exists. Without it, the frontend might launch before the
AI service is ready and immediately fail when a user sends a message.

```yaml
    networks:
      - app-network
```

Puts the frontend on the same private network as the backend so the two can talk.

---

### Volumes

```yaml
volumes:
  postgres_data:
    driver: local
```

A **volume** is persistent storage. This declares one named `postgres_data` stored on your
local disk.

> 📝 **Note:** In this particular file the volume is *declared but not actually attached*
> to any service (because the database runs on the host, not in a container). It's left
> here as a placeholder for setups that do run PostgreSQL inside Docker. You can safely
> ignore it for now.

---

### Networks

```yaml
networks:
  app-network:
    driver: bridge
```

This creates the private network the two services use. `bridge` is the standard Docker
network type for letting containers on one host communicate while staying isolated from
the outside world.

---

## 4. How the whole thing fits together

```
        Your Browser
             │  http://localhost:3000
             ▼
   ┌───────────────────┐        app-network         ┌───────────────────┐
   │     frontend      │  ───────────────────────▶  │      backend      │
   │  (Next.js, :3000) │   http://backend:3050      │  (Python AI,:3050)│
   └───────────────────┘                            └─────────┬─────────┘
                                                              │ host.docker.internal:5432
                                                              ▼
                                                    ┌───────────────────┐
                                                    │   PostgreSQL      │
                                                    │  (on YOUR machine)│
                                                    └───────────────────┘
```

1. Docker builds and starts the **backend** and waits for it to become **healthy**.
2. Once healthy, the **frontend** starts.
3. You open `http://localhost:3000`, type a question.
4. The frontend forwards it to the backend over the private `app-network`.
5. The backend queries the **PostgreSQL database running on your own computer** and replies.

---

## 5. Running it — step by step

### Before you start (one-time setup)

1. **Install Docker Desktop** — <https://www.docker.com/products/docker-desktop/> and make
   sure it's running.
2. **Have PostgreSQL running locally** on port `5432` with your phone data loaded
   (done during the ETL step — see the main [`README.md`](README.md)).
3. **Create the backend env file:**
   ```bash
   cd backend
   cp .env.example .env
   # then open .env and fill in your GROQ_API_KEY, Langfuse keys, and DB credentials
   cd ..
   ```

### Start everything

From inside the `Bootcamp` folder:

```bash
docker compose up --build
```

- `up` → create and start the containers.
- `--build` → (re)build the images first. Use this the first time, or after you change code.

The first run takes a few minutes (it's downloading base images and installing
dependencies). You'll see logs from both services stream into your terminal.

When it's ready, open **<http://localhost:3000>** in your browser. 🎉

### Useful everyday commands

| Goal | Command |
|------|---------|
| Start in the background (detached) | `docker compose up --build -d` |
| See running containers | `docker compose ps` |
| Watch the logs | `docker compose logs -f` |
| Watch only the backend logs | `docker compose logs -f backend` |
| Stop the containers | `docker compose down` |
| Stop **and** remove volumes | `docker compose down -v` |
| Rebuild from scratch (ignore cache) | `docker compose build --no-cache` |

> 💡 To stop a foreground (`up` without `-d`) session, press **Ctrl + C** in the terminal.

---

## 6. Windows users

There is a sibling file, [`docker-compose-windows.yml`](docker-compose-windows.yml).
In this repo it is currently identical to `docker-compose.yaml`, so you can use either
file. To run a specific file by name:

```bash
docker compose -f docker-compose-windows.yml up --build
```

The `host.docker.internal` hostname (used for the database) works the same on Windows and
Mac with Docker Desktop.

---

## 7. Common problems & fixes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Frontend never starts | Backend isn't becoming healthy | Check `docker compose logs backend` — usually a bad API key or the DB isn't reachable. |
| Backend can't connect to the database | PostgreSQL isn't running on the host, or wrong credentials | Confirm Postgres is up on port `5432`; verify `DB_*` values in `backend/.env`. |
| `port is already allocated` | Something else uses `3000` or `3050` | Stop the other program, or change the **left** number in the `ports:` mapping. |
| Changes to code don't appear | Image wasn't rebuilt | Re-run with `docker compose up --build`. |
| `Cannot connect to the Docker daemon` | Docker Desktop isn't running | Start Docker Desktop and wait until it says "running." |

---

## 8. Quick recap

- **Compose = one file, one command** to run multi-container apps.
- This app has a **frontend** (port `3000`) and a **backend** (port `3050`).
- The frontend **waits for the backend to be healthy** before starting.
- Containers talk to each other by **service name** over a private network.
- The **database lives on your host machine**, not in a container.
- Start it all with `docker compose up --build`, stop it with `docker compose down`.

Happy building! 🚀
