# API Usage

R³-DE runs as a standard Apify actor, so it is reachable through any of Apify's client libraries or the raw REST API. This page shows the three most common integration paths.

## 1. Python (apify-client)

```python
from apify_client import ApifyClient

client = ApifyClient("<YOUR_APIFY_TOKEN>")

run = client.actor("gunmetal/r3-de").call(run_input={
    "rawText": "Alice: Let's schedule a meeting tomorrow at 3pm.\nBob: Works for me."
})

for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)
```

## 2. JavaScript / Node (apify-client)

```javascript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: '<YOUR_APIFY_TOKEN>' });

const run = await client.actor('gunmetal/r3-de').call({
    rawText: 'Alice: Let\'s schedule a meeting tomorrow at 3pm.\nBob: Works for me.',
});

const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(items);
```

## 3. Raw REST

```bash
curl -X POST \
  "https://api.apify.com/v2/acts/gunmetal~r3-de/runs?token=<YOUR_APIFY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"rawText": "Alice: Let'\''s schedule a meeting tomorrow at 3pm."}'
```

Poll the run, then fetch the dataset:

```bash
curl "https://api.apify.com/v2/datasets/<DATASET_ID>/items?token=<YOUR_APIFY_TOKEN>"
```

## Synchronous convenience endpoint

For short inputs where waiting for the full run/poll/fetch cycle is unnecessary overhead, use the run-sync-get-dataset-items endpoint:

```bash
curl -X POST \
  "https://api.apify.com/v2/acts/gunmetal~r3-de/run-sync-get-dataset-items?token=<YOUR_APIFY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"rawText": "..."}'
```

This blocks until the run finishes and returns the dataset items directly in the response body, which is convenient for scripting and CI smoke tests but not recommended for large inputs.

## Rate and cost considerations

- Billing is pay-per-result at $0.10 per 1,000 results, so batch related turns into a single `rawText` payload where possible rather than issuing one run per turn.
- Deterministic output means repeated runs on identical input are safe to cache; there is no need to re-run for idempotency.

## Authentication

All calls require an Apify API token, scoped to the account with access to the actor. Store it as a secret in CI and never commit it to the repository — see `.github/workflows/ci.yml` for how the token is injected as an environment variable during automated checks.
