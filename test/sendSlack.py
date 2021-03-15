import json
import requests
from slacker import Slacker

slack_webhook_url = "https://hooks.slack.com/services/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"
headers = {"Content-type": "application/json"}
data = {"text": "Hello, World!"}
res = requests.post(slack_webhook_url, headers=headers, data=json.dumps(data))
print(res.status_code)
