import re
import json


def clean_agents_output(response_text):
    # Extract the JSON string inside the triple backticks
        match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        if not match:
            raise ValueError("No JSON payload found in response text.")
        json_str = match.group(1)
    # Parse the JSON string
        return json.loads(json_str)
