# Package Server

This directory contains the bootcamp package cache helper.

## What it does

- Exports the backend dependencies from `backend/pyproject.toml`
- Adds repo-specific supplemental packages used by the scraper and notebooks
- Downloads wheels into `package_server/wheelhouse/`
- Serves that wheelhouse over HTTP for offline/local installs
- Seeds a local npm registry cache for the frontend packages
- If internet is unavailable, both scripts keep serving whatever cache already exists

## Build the cache

From the repo root:

```bash
python package_server/bootcamp_package_server.py --no-serve
```

## Serve the cache

From the repo root:

```bash
python package_server/bootcamp_package_server.py
```

To use a different port:

```bash
python package_server/bootcamp_package_server.py --port 8000
```

## Install from the local server

On participant machines:

```bash
PIP_NO_INDEX=1 PIP_FIND_LINKS="http://<server-ip>:8000/" pip install -r package_server/.bootcamp-requirements.txt
```

## Node packages

To cache and serve the frontend packages through a local npm registry:

```bash
python package_server/node_package_server.py --no-serve
python package_server/node_package_server.py
```

On participant machines:

```bash
npm config set registry "http://<server-ip>:4873/"
npm install
```

When you’re done using the local registry, restore the default npm registry with:

```bash
npm config set registry "https://registry.npmjs.org/"
```

If you changed it only for one shell session, remove the temporary setting instead:

```bash
npm config delete registry
```

## Notes

- The script creates a temporary virtual environment for downloads, so it does not depend on the system Python packaging state.
- If you regenerate the cache, the existing `wheelhouse/` contents will be updated in place.
- The npm cache is stored under `package_server/node_registry/`.
- A failed warm-up does not stop the server; it only means the cache may be partial until you rerun it with internet access.
