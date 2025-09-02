# Python Code Executor

A Flask API that runs Python scripts safely. Built for a coding challenge.

**Live URL:** https://flask-api-715530681393.us-central1.run.app

## How it works

Send a POST request to `/execute` with Python code that has a `main()` function. It returns whatever the function returns.

```bash
curl -X POST https://flask-api-715530681393.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    return {\"hello\": \"world\"}"}'
```

Returns:
```json
{
  "result": {"hello": "world"},
  "stdout": ""
}
```

## Examples

Basic math:
```bash
curl -X POST https://flask-api-715530681393.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    return {\"answer\": 2 + 2}"}'
```

With pandas:
```bash
curl -X POST https://flask-api-715530681393.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "import pandas as pd\n\ndef main():\n    df = pd.DataFrame({\"values\": [1, 2, 3]})\n    return {\"sum\": int(df.sum())}"}'
```

Print statements show up in stdout:
```bash
curl -X POST https://flask-api-715530681393.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    print(\"Debug info\")\n    return {\"done\": True}"}'
```

## What's blocked

For security, these imports don't work:
- `os`, `subprocess` (system access)
- `socket`, `urllib`, `requests` (network)
- `open`, `file` (file system)

## Requirements

- Script must have a `main()` function
- Function must return something JSON can handle
- 10KB script size limit
- 30 second timeout

## Run locally

```bash
docker build -t flask-api .
docker run -p 8080:8080 flask-api
```

## Tech stack

- Flask + gunicorn
- Docker
- Google Cloud Run
- Basic sandboxing with timeout/ulimits
- pandas 2.1.1, numpy 1.24.3

Built in about 2 hours for a take-home challenge.