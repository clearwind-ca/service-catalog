Health checks are the next step in your organisations readiness. Often we measure the quality of a service by some metrics[^1] or perhaps number of incidents. Incidents tend to be reactive in nature and health checks are intended to provide a more pro-active approach to measuring quality.

A health check is a peice of code, written by the organisation to examine the service in some manner and return a value back to the Service Catalog.

## Health Checks timeline

* A health check is created in the service catalog, with a frequency of how often it should be run.
* When the health check is run, a health check result is created in the catalog, with state of `sent` and `unknown`
* The health check is sent to a repository on GitHub as a [repository_dispatch](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#repository_dispatch) event.
* The GitHub Action runs some code and returns a result to the service catalog.

## Authentication

In order to send a response back to the Service Catalog, you must authenticate with [the API](api.md) and to do that, you will need the API token for a user logged into the Service Catalog. In the following example 👇, it assumes the Secret is called `SERVICE_CATALOG_TOKEN`.

For the Action to report the data back to the Service Catalog, the Action Runner (either [hosted](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners) or [self-hosted](https://docs.github.com/en/actions/hosting-your-own-runners/about-self-hosted-runners)) must have network access to the Service Catalog.

## Example GitHub Action

```
name: Service Catalog Basic Check
run-name: Catalog check ${{ github.event.client_payload.check }} on ${{ github.event.client_payload.service }}
on:
  repository_dispatch:
    types: ["check"]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10' 
    - name: Run check ${{ github.event.client_payload.check }} on ${{ github.event.client_payload.service }}
      env:
        PAYLOAD: ${{ github.event.client_payload.data }}
        SERVICE_CATALOG_TOKEN: ${{ secrets.SERVICE_CATALOG_TOKEN }}
      run: |
        pip install requests
        python calculate-result.py
```

Three key variables are provided in the payload:
* `data`: contains all the objects from the Service Catalog to allow you to do whatever work you'd like and post the information back to the Service Catalog.
* `check`: the `slug` of the check so you can identify and route the health check appropriately.
* `service`: the `slug` of the service so you can identify and rout the health check appropriately.
 
At the end of this workflow we are running a script contained in the repository of the name `calculate-result.py` which is going to process the payload.

## Payload: data

The data is a base64 encoded JSON object. To get access to the data in Python you'd do the following:

```python
import os
import base64
import json

payload = os.getenv("PAYLOAD")
decoded = base64.b64decode(payload).decode('utf-8')
data = json.loads(decoded)
print("Received payload of:", data)
```

### Updating status

The payload contains all the information from the catalog:

* `server`: the URL of the server that sent this message, including the URL to post a response too
* `check`: the health check object
* `result`: the health check result object, that the Action will be updating
* `service`: the service the health check is being called on
* `source`: the source of the service

To post back to the server, call the endpoint with a change to the `status` field, as an example:

```python
import requests

url = payload["server"]["url"] + payload["server"]["endpoint"]
token = os.getenv("SERVICE_CATALOG_TOKEN")
headers = {"Authorization": f"Token {token}"}

data = {"result": "pass"} # Set the health check to pass
res = requests.patch(url, data, headers=headers)
print("Response", res.status_code)
```

## Notes

* Each health check for each service is sent as an individual GitHub Action run.
* If the GitHub Action does not respond in a sufficient time then the check will be timed out.
* Once a result has been sent to the Service Catalog, it cannot be changed. 

---

[^1]: As an example called Service Level Objectives, these are metrics that test the quality and performance of the service being provided.