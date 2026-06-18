# 🐳 Docker Concepts — A Complete Beginner's Guide

This guide teaches the **core ideas behind Docker** from zero, then gives you a
**command cheatsheet** you can keep open while you work. Read this first, then read the
[Docker Compose Guide](DOCKER_COMPOSE_GUIDE.md) to see these concepts applied to the
Lumivya bootcamp app.

> 🎯 **Goal:** After this you'll understand *what* an image, container, volume, network,
> and Dockerfile are — *why* they exist — and the exact commands to use them.

---

## 1. The problem Docker solves

Software needs a specific environment to run: a certain OS, language version, libraries,
system packages, environment variables, and config. When that environment differs between
your laptop, a teammate's laptop, and the production server, you get the classic bug:

> *"But it works on my machine!"* 🤷

**Docker fixes this by packaging an app together with its entire environment into one
portable unit.** That unit runs the same way everywhere Docker is installed — your Mac, a
Windows PC, a cloud server.

### Docker vs. Virtual Machines

You may have heard of Virtual Machines (VMs). Both isolate software, but differently:

| | Virtual Machine | Docker Container |
|---|---|---|
| What it virtualizes | A whole computer (its own OS) | Just the app + its dependencies |
| Size | Gigabytes | Megabytes |
| Startup time | Minutes | Seconds (or less) |
| Overhead | Heavy (full guest OS) | Light (shares the host's OS kernel) |

```
   Virtual Machines                     Docker Containers
┌──────┐ ┌──────┐ ┌──────┐          ┌──────┐ ┌──────┐ ┌──────┐
│ App  │ │ App  │ │ App  │          │ App  │ │ App  │ │ App  │
│ Libs │ │ Libs │ │ Libs │          │ Libs │ │ Libs │ │ Libs │
│Guest │ │Guest │ │Guest │          └──────┘ └──────┘ └──────┘
│  OS  │ │  OS  │ │  OS  │          ┌────────────────────────┐
└──────┘ └──────┘ └──────┘          │    Docker Engine       │
┌────────────────────────┐          ├────────────────────────┤
│      Hypervisor         │          │      Host OS           │
├────────────────────────┤          ├────────────────────────┤
│       Host OS           │          │      Hardware          │
└────────────────────────┘          └────────────────────────┘
```

**Key insight:** Containers are lightweight because they *share* the host's OS kernel
instead of each carrying their own operating system.

---

## 2. The three foundational concepts

Everything in Docker builds on these three. Learn them in order.

### 🧊 Image — the blueprint

An **image** is a read-only, frozen snapshot of an app and everything it needs: the code,
the runtime (e.g. Python), libraries, and a default command to run. Think of it as a
**class** in programming, or a **recipe** in a cookbook. You don't run a recipe — you cook
*from* it.

- Images are built in **layers** (each instruction in a Dockerfile adds a layer). Layers
  are cached and reused, which makes rebuilds fast.
- Images have names and **tags**, like `python:3.12-slim` or `node:22-alpine`. The part
  after the colon (`3.12-slim`) is the tag — usually a version.

### 📦 Container — the running instance

A **container** is a **running copy of an image**. If the image is the class, the
container is the **object** (instance). If the image is the recipe, the container is the
**actual dish** you cooked.

- You can start many containers from one image (like making many cookies from one recipe).
- Containers are **disposable** — you can stop, delete, and recreate them freely.
- ⚠️ **Containers are ephemeral:** anything written *inside* a container is **lost** when
  the container is deleted — *unless* you use a **volume** (see below). This is the single
  most important thing beginners forget.

### 📜 Dockerfile — the instructions to build an image

A **Dockerfile** is a plain text file with step-by-step instructions for *building* an
image. It's the recipe written down.

Here's a tiny annotated example:

```dockerfile
# 1. Start FROM an existing base image (Python pre-installed)
FROM python:3.12-slim

# 2. Set the working directory inside the image
WORKDIR /app

# 3. COPY files from your computer into the image
COPY requirements.txt .

# 4. RUN a command at build time (install dependencies)
RUN pip install -r requirements.txt

# 5. COPY the rest of your code in
COPY . .

# 6. Document which PORT the app listens on
EXPOSE 8000

# 7. The default command to run when a container starts
CMD ["python", "main.py"]
```

| Instruction | Purpose |
|-------------|---------|
| `FROM` | The starting base image to build on top of. |
| `WORKDIR` | Sets the current folder inside the image for later commands. |
| `COPY` / `ADD` | Copy files from your machine into the image. (`ADD` can also fetch URLs / unpack archives.) |
| `RUN` | Execute a command **while building** (e.g. install packages). Each `RUN` makes a new layer. |
| `ENV` | Set an environment variable inside the image. |
| `EXPOSE` | Document the port the app uses (informational; doesn't actually publish it). |
| `CMD` | The default command run when the container **starts**. |
| `ENTRYPOINT` | Like `CMD`, but harder to override — used for the "main" executable. |

> 🔁 **The lifecycle:** `Dockerfile` → (build) → `Image` → (run) → `Container`

```
  Dockerfile  ──docker build──▶  Image  ──docker run──▶  Container
  (recipe)                      (frozen)                 (running)
```

---

## 3. Volumes — making data survive 💾

**The problem:** Containers are disposable. Delete the container and any data written
inside it vanishes. That's fine for a stateless web app, but terrible for a **database**,
uploaded files, or logs you want to keep.

**The solution:** A **volume** is storage that lives *outside* the container's own
filesystem and is managed by Docker. It **persists** even after the container is deleted,
and can be shared between containers.

### The two kinds you'll actually use

#### a) Named volumes (Docker-managed)

Docker creates and stores these for you in a special area on disk. Best for databases.

```bash
# Create a named volume
docker volume create my-data

# Use it when running a container (format: VOLUME_NAME:PATH_INSIDE_CONTAINER)
docker run -v my-data:/var/lib/postgresql/data postgres
```

Now even if you `docker rm` the Postgres container, the data in `my-data` is safe. Start a
new container pointing at the same volume and your data is right back.

#### b) Bind mounts (a folder on your computer)

You map a real folder on **your machine** straight into the container. Best for
**development** — edit code locally and see it instantly inside the container.

```bash
# Format: ABSOLUTE_HOST_PATH:PATH_INSIDE_CONTAINER
docker run -v /Users/me/project:/app my-image
```

| | Named Volume | Bind Mount |
|---|---|---|
| Managed by | Docker | You |
| Lives where | Docker's storage area | A folder you choose |
| Best for | Databases, persistent app data | Live-editing source code in dev |
| Portable | Yes | Tied to a specific host path |

> 💡 **Three ways data behaves in a container:**
> 1. **No volume** → data dies with the container.
> 2. **Named volume** → data survives, Docker keeps it safe.
> 3. **Bind mount** → data is just a window into a folder on your computer.

### Volume cheatsheet

```bash
docker volume ls                 # list all volumes
docker volume create NAME        # create a volume
docker volume inspect NAME       # see details (where it's stored, etc.)
docker volume rm NAME            # delete a volume
docker volume prune              # delete ALL unused volumes (frees space)
```

---

## 4. Networks — how containers talk 🌐

**The problem:** By default, each container is isolated. But real apps have multiple
containers that must communicate — a web app talking to a database, a frontend talking to
a backend.

**The solution:** Docker **networks** are private virtual LANs. Containers on the same
network can reach each other **by name**, and Docker runs a tiny built-in DNS so the name
resolves to the right container automatically.

### The most important rule for beginners

> Inside the same Docker network, you reach another container by its **service/container
> name**, NOT by `localhost`.

For example, if a `backend` container and a `frontend` container share a network, the
frontend connects to the backend using the address `http://backend:3050` — not
`http://localhost:3050`. (`localhost` inside a container means *that container itself*.)

### Network types you'll meet

| Driver | What it does | When |
|--------|--------------|------|
| `bridge` | Default. Private network on one host; containers talk to each other, isolated from outside unless you publish ports. | Almost always (single machine). |
| `host` | Container shares the host's network directly (no isolation). | Special performance cases. |
| `none` | No networking at all. | Fully isolated jobs. |
| `overlay` | Network spanning **multiple machines**. | Clusters (Docker Swarm / production scale). |

### Publishing ports vs. internal networking

There are **two different kinds of connectivity** — don't mix them up:

1. **Container ↔ container** (internal): happens automatically over a shared network using
   service names. No port publishing needed.
2. **Your computer ↔ container** (external): you must **publish** a port with `-p`.

```bash
# -p HOST_PORT:CONTAINER_PORT
docker run -p 3000:3000 my-frontend
#            │     └── port inside the container
#            └──────── port on your machine → open http://localhost:3000
```

```
   Your machine                Docker bridge network "app-network"
  ┌────────────┐    -p 3000   ┌──────────┐        ┌──────────┐
  │  Browser   │ ───────────▶ │ frontend │ ─────▶ │ backend  │
  │ localhost  │   published  │  :3000   │  by    │  :3050   │
  │   :3000    │     port     └──────────┘  name  └──────────┘
  └────────────┘
```

### Network cheatsheet

```bash
docker network ls                       # list networks
docker network create NAME              # create a network (bridge by default)
docker network inspect NAME             # see which containers are attached
docker network connect NAME CONTAINER   # attach a running container to a network
docker network rm NAME                  # delete a network
docker network prune                    # delete all unused networks
```

---

## 5. Registries & image tags 🏷️

A **registry** is an online store of images. The default public one is
[Docker Hub](https://hub.docker.com/). When you write `FROM python:3.12-slim`, Docker
*pulls* (downloads) that image from a registry.

- **Pull** = download an image from a registry.
- **Push** = upload your own image to a registry (so a server can pull it).
- **Tag** = the version label after the colon. `myapp:1.0`, `myapp:latest`.

```bash
docker pull nginx:latest          # download an image
docker tag myapp myrepo/myapp:1.0 # give an image a new name/tag
docker push myrepo/myapp:1.0      # upload to a registry (after docker login)
docker login                      # authenticate to a registry
```

> ⚠️ `latest` is **not** magic — it's just a default tag name, not "the newest." Pin real
> versions (e.g. `:1.0`, `:3.12-slim`) for reproducible builds.

---

## 6. Docker Compose — many containers, one file 🎼

Running multi-container apps with long `docker run -p ... -v ... --network ...` commands
gets painful fast. **Docker Compose** lets you describe everything — services, volumes,
networks, env vars — in one `docker-compose.yaml` file and run it with a single command.

```bash
docker compose up --build     # build images & start everything
docker compose down           # stop & remove everything
```

👉 **The Lumivya app uses Compose.** For a full line-by-line walkthrough of *this
project's* setup, read the companion **[Docker Compose Guide](DOCKER_COMPOSE_GUIDE.md)**.

---

## 7. How it all fits together

```
                    ┌─────────────────────────────────────────┐
                    │              REGISTRY (Docker Hub)        │
                    │   stores base images: python, node, ...   │
                    └───────────────────┬─────────────────────-┘
                                        │ pull (FROM ...)
                                        ▼
   Dockerfile ───build──▶  IMAGE ───run──▶  CONTAINER
   (recipe)              (blueprint)        (running app)
                                                │
                          ┌─────────────────────┼──────────────────────┐
                          ▼                     ▼                       ▼
                      VOLUME                NETWORK                  PORTS
                  (data survives)      (containers talk          (your machine
                                        by name)                  reaches it)
```

---

## 8. 🧾 The Master Cheatsheet

Keep this handy. Modern Docker uses `docker compose` (with a space); older installs use
`docker-compose` (with a hyphen) — they're otherwise the same.

### Images

```bash
docker build -t myapp .              # build an image from ./Dockerfile, name it "myapp"
docker build -t myapp:1.0 .          # ...with a version tag
docker images                        # list local images
docker pull node:22-alpine           # download an image
docker rmi myapp                     # remove an image
docker image prune                   # remove dangling (unused) images
docker history myapp                 # show an image's layers
```

### Containers — run & manage

```bash
docker run myapp                     # run a container from an image
docker run -d myapp                  # -d = detached (run in background)
docker run -p 3000:3000 myapp        # publish a port (host:container)
docker run -v mydata:/data myapp     # attach a volume
docker run --name web myapp          # give it a name
docker run --env-file .env myapp     # load environment variables from a file
docker run -e KEY=value myapp        # set one env var
docker run -it ubuntu bash           # interactive shell inside a container
docker run --rm myapp                # auto-delete the container when it exits
```

### Containers — inspect & control

```bash
docker ps                            # list RUNNING containers
docker ps -a                         # list ALL containers (incl. stopped)
docker stop CONTAINER                # gracefully stop
docker start CONTAINER               # start a stopped container
docker restart CONTAINER             # restart
docker rm CONTAINER                  # delete a stopped container
docker rm -f CONTAINER               # force-delete a running container
docker logs CONTAINER                # view its output
docker logs -f CONTAINER             # follow logs live (Ctrl+C to exit)
docker exec -it CONTAINER bash       # open a shell INSIDE a running container
docker exec -it CONTAINER sh         # (use sh if bash isn't installed, e.g. alpine)
docker inspect CONTAINER             # full JSON details
docker stats                         # live CPU / memory usage
```

### Volumes

```bash
docker volume ls                     # list volumes
docker volume create NAME            # create
docker volume inspect NAME           # details
docker volume rm NAME                # delete
docker volume prune                  # delete all unused volumes
```

### Networks

```bash
docker network ls                    # list networks
docker network create NAME           # create
docker network inspect NAME          # details (attached containers)
docker network connect NAME CONT     # attach a container
docker network rm NAME               # delete
docker network prune                 # delete all unused networks
```

### Docker Compose

```bash
docker compose up                    # start all services
docker compose up --build            # rebuild images first, then start
docker compose up -d                 # start in the background
docker compose down                  # stop & remove containers + networks
docker compose down -v               # ...also remove volumes (wipes data!)
docker compose ps                    # list this project's containers
docker compose logs -f               # follow logs from all services
docker compose logs -f backend       # follow logs from one service
docker compose build --no-cache      # rebuild ignoring the cache
docker compose restart               # restart all services
docker compose exec backend sh       # shell into a running service
```

### Cleanup (free up disk space) 🧹

```bash
docker system df                     # show how much space Docker is using
docker container prune               # remove all stopped containers
docker image prune                   # remove dangling images
docker image prune -a                # remove ALL unused images
docker volume prune                  # remove unused volumes
docker network prune                 # remove unused networks
docker system prune                  # remove all unused data (careful!)
docker system prune -a --volumes     # nuke everything unused incl. volumes (very careful!)
```

---

## 9. Mental-model recap

| Concept | One-line meaning | Analogy |
|---------|------------------|---------|
| **Dockerfile** | Instructions to build an image | Recipe |
| **Image** | Frozen, read-only app + environment | The recipe, ready to cook |
| **Container** | A running instance of an image | The cooked dish |
| **Volume** | Storage that outlives the container | A fridge that keeps leftovers |
| **Network** | Private LAN so containers talk by name | A phone line between rooms |
| **Port (`-p`)** | A door from your machine into a container | The serving window |
| **Registry** | Online store of images | An app store |
| **Compose** | Run many containers from one file | A menu / orchestra conductor |

### Golden rules to remember

1. **Containers are disposable** — use a **volume** for anything you want to keep.
2. **Inside a network, use names, not `localhost`** to reach other containers.
3. **`-p host:container`** is how *you* reach a container from your machine.
4. **Rebuild (`--build`) after code changes** or you'll keep running the old image.
5. **`down -v` and `prune --volumes` delete data** — use them deliberately.

---

## 10. Where to go next

- 👉 [Docker Compose Guide](DOCKER_COMPOSE_GUIDE.md) — this project's `docker-compose.yaml`
  explained line by line.
- 📖 [Official Docker docs](https://docs.docker.com/) — the authoritative reference.
- 🧪 [Play with Docker](https://labs.play-with-docker.com/) — a free in-browser sandbox to
  practice these commands without installing anything.

Happy containerizing! 🐳🚀
