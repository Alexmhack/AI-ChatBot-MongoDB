all : build run
.PHONY : all

build:
	- sudo docker build -f Dockerfile -t quadz-ai-bot:latest .

run-docker:
	- sudo docker run --name quadz-ai-bot --restart always --network="host" -d -p 8501:8501 quadz-ai-bot:latest

run-app:
	- poetry run streamlit run main.py

run-streamlit:
	- poetry run streamlit run $(file)
