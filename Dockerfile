FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

CMD ["python", "main.py"]