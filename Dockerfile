# R3 | DE — actor image
# Base: Apify's Python actor image (Playwright not required; this is a pure NLP pipeline)
FROM apify/actor-python:3.11

# System deps for scientific/graph libraries used by the pipeline
# (networkx, scikit-learn/GPR, dowhy, pandas all need a working build toolchain
# for their compiled dependencies on some platforms)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN echo "Python version:" \
    && python --version \
    && echo "Installing dependencies:" \
    && pip install --no-cache-dir -r requirements.txt \
    && echo "All installed Python packages:" \
    && pip freeze

COPY . ./

# Sanity-check the actor's own contracts at build time so a broken schema
# never ships in an image.
RUN python -c "import json; json.load(open('.actor/actor.json'))" \
    && python -c "import json; json.load(open('.actor/input_schema.json'))" \
    && python -c "import json; json.load(open('.actor/dataset_schema.json'))"

CMD ["python3", "-m", "src"]
