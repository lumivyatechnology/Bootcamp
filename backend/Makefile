
run_ui_backend:
	uv run --env-file .env src/main.py

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

