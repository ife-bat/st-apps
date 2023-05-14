FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    mdbtools \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app

RUN pip3 install -r requirements.txt

COPY src /app

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]

# Build: docker build -t streamlit-apps .
# Run: docker run -p 8501:8501 streamlit-apps
# Run in background: docker run -d -p 8501:8501 streamlit-apps
# List images: docker images
# List running: docker ps
# Stop: docker stop <container_id>