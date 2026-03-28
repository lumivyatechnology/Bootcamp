
run_ui_backend:
	uv run --env-file .env src/main.py

run_mcp:
	uv run --env-file .env src/main_mcp.py

run_summarizer:
	uv run --env-file .env src/text_summarizer.py

mcp_serve:
	uv run --env-file .env src/mcp_server/main.py

mcp_inspector:
	fastmcp dev src/mcp_server/main.py

docker_rm:
	docker rm -f analytics_agent

docker_build:
	docker build -t analytics_agent .

docker_run: docker_build docker_rm
	docker run --env-file .env -p 3050:3050 --name analytics_agent analytics_agent

loadbalance:
	docker compose up --build

loadbalance_rm:
	docker compose down

