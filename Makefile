all : build run
.PHONY : all

build:
	- sudo docker build -f Dockerfile -t quadz-ai-bot:latest .

run:
	- sudo docker run --rm --name quadz-ai-bot --add-host=host.docker.internal:host-gateway -d -p 8501:8501 quadz-ai-bot:latest
