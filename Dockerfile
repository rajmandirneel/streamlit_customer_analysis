FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y build-essential python3-dev ffmpeg \ 
    && pip install --upgrade pip \ 
    && pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]