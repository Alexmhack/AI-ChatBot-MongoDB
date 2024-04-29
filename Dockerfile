# app/Dockerfile

FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    pipx \
    && rm -rf /var/lib/apt/lists/*

RUN pipx install poetry
ENV PATH="${PATH}:/root/.local/bin"

COPY . /app/
WORKDIR /app

RUN poetry install

EXPOSE 8501

# HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["poetry", "run", "streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
