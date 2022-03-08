from typing import Dict

import requests
from requests_aws4auth import AWS4Auth


def run_query(endpoint: str, auth: AWS4Auth, query: str) -> Dict:
    response = requests.post(endpoint, json={"query": query}, auth=auth)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.content}")
