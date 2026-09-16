# R³-DE: Rich Recursive Reasoning & Dialogue Extraction

R³-DE is a multi-layer Natural Language Understanding (NLU) pipeline that transforms raw text or web-scraped content into structured, training-ready datasets. It extracts semantic, causal, and probabilistic signals from unstructured language and produces deterministic outputs suitable for machine learning, analytics, and safety-critical systems.

>Visit R3 | DE Official Page: [@R³-DE](https://apify.com/gunmetal/r3-de)

---

## Overview

R³-DE converts unstructured inputs such as conversations, logs, transcripts, and articles into structured records containing:

* Speakers
* Entities
* Actions (triggers)
* States
* Intent classification
* Sentiment polarity
* Temporal signals
* Semantic clusters
* Causal relationships
* Confidence and uncertainty scores
* Prompt–completion pairs

The system is designed for reproducibility, interpretability, and downstream AI integration. ([Apify][1])

---

## Architecture

### High-Level Pipeline

```
                ┌──────────────────────────────┐
                │        Input Layer           │
                │  (Raw Text / URL Scraping)   │
                └────────────┬─────────────────┘
                             │
                             ▼
                ┌──────────────────────────────┐
                │      Perception Layer        │
                │  NLP Parsing (spaCy, NER)    │
                └────────────┬─────────────────┘
                             │
                             ▼
                ┌──────────────────────────────┐
                │  Semantic Structuring Layer  │
                │  Embeddings + Clustering     │
                └────────────┬─────────────────┘
                             │
                             ▼
                ┌──────────────────────────────┐
                │     Causality Layer          │
                │  DoWhy + Graph Modeling      │
                └────────────┬─────────────────┘
                             │
                             ▼
                ┌──────────────────────────────┐
                │    Uncertainty Layer         │
                │  Gaussian Process (GPR)      │
                └────────────┬─────────────────┘
                             │
                             ▼
                ┌──────────────────────────────┐
                │     Output Layer             │
                │  JSON / Dataset / Graphs     │
                └──────────────────────────────┘
```

---

## Key Features

* Speaker-aware dialogue extraction
* Entity, action, and state modeling
* Intent and sentiment inference
* Semantic clustering of utterances
* Causal inference (trigger → state relationships)
* Confidence scoring using probabilistic models
* Knowledge graph generation (NetworkX)
* Prompt–completion dataset generation
* Deterministic inference (no randomness)
* Schema-locked outputs for reproducibility ([Apify][1])

---

## Project Structure

```
r3-de/
│
├── src/
│   ├── input_layer.py
│   ├── perception.py
│   ├── semantic.py
│   ├── causality.py
│   ├── uncertainty.py
│   └── synthesis.py
│
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Installation

### Prerequisites

* Python 3.10+
* Node.js (optional for Apify CLI)
* Docker (recommended)

---

### Local Setup

```bash
git clone 'https://github.com/SakaethRam/Agentic-R3-DE.git'
cd agentic-r3-de

pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## Running Locally

```bash
python main.py
```

Input can be provided as:

```json
{
  "rawText": "Alice: Schedule meeting tomorrow at 3pm."
}
```

---

## Docker Setup

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

CMD ["python", "main.py"]
```

---

### docker-compose.yml

```yaml
version: "3.8"

services:
  r3de:
    build: .
    container_name: r3de_pipeline
    ports:
      - "8000:8000"
    environment:
      - APIFY_TOKEN=${APIFY_TOKEN}
```

---

### Run with Docker

```bash
docker build -t r3de .
docker run -it r3de
```

---

## Apify Integration

R³-DE runs as an Apify Actor and can be triggered via API.

### Run Actor (HTTP)

```bash
curl "https://api.apify.com/v2/acts/gunmetal~r3-de/runs?token=YOUR_API_TOKEN" \
  -X POST \
  -d @input.json \
  -H 'Content-Type: application/json'
```

### Sync Run (Get Output)

```bash
https://api.apify.com/v2/acts/gunmetal~r3-de/run-sync-get-dataset-items
```

The API requires an Apify token and supports JSON input payloads. ([Apify][2])

---

## Example Output

```json
{
  "speaker": "Alice",
  "entity": "meeting tomorrow",
  "state": "schedule meeting tomorrow at 3pm",
  "trigger": "schedule",
  "intent": "command",
  "sentiment": 0.0,
  "confidence": 0.92
}
```

---

## Use Cases

### 1. Training AI Models

* Intent classification
* Dialogue modeling
* Sequence prediction

### 2. AI System Evaluation

* Detect hallucinations
* Validate agent behavior
* Benchmark LLM outputs

### 3. Synthetic Dataset Generation

* Safe, reproducible training data
* Controlled experimentation

### 4. Security & Monitoring

* Event chain reconstruction
* Behavioral anomaly detection

### 5. Knowledge Graph Construction

* Speaker → action → outcome mapping

---

## Design Principles

* Deterministic inference (no randomness)
* Schema-locked outputs
* Domain-agnostic processing
* Zero manual annotation
* Explainable reasoning pipeline ([Apify][1])

---

## API Clients

### Python

```bash
pip install apify-client
```

### JavaScript

```bash
npm install apify-client
```

Supports:

* HTTP
* CLI
* OpenAPI
* MCP server integration ([Apify][2])

---

## Scaling

R³-DE is designed for horizontal scalability via:

* Apify Actor infrastructure
* Containerized deployment
* Dataset-based storage
* Stateless processing pipeline

---

## Roadmap

* Real-time streaming ingestion
* Transformer-based embeddings
* Advanced causal inference (graph-based)
* Multi-modal support (audio/video)
* Reinforcement learning integration

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Submit a pull request

---

## Summary

R³-DE transforms raw language into structured, causally-aware, uncertainty-quantified intelligence. It bridges the gap between unstructured text and decision-ready data pipelines, making it a foundational system for next-generation AI applications.

---

[1]: https://apify.com/gunmetal/r3-de?utm_source=chatgpt.com "R3 | DE · Apify"
[2]: https://apify.com/gunmetal/r3-de/api?utm_source=chatgpt.com "R3 | DE API · Apify"
