# llm_utils.py

import os
import re
import json
import requests
from dotenv import load_dotenv
from requests.exceptions import Timeout, HTTPError, RequestException
from chunking_prompt import SYSTEM_CHUNK_PROMPT

# Load your OpenAI API key from .env
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"   # or whichever model you prefer

# Common headers for OpenAI
HEADERS = {
    "Authorization": f"Bearer {OPENAI_KEY}",
    "Content-Type": "application/json"
}

def chunk_review_with_llm(review_text: str, timeout: int = 30) -> dict:
    """
    Split a single hospital review into 의미 범주별 chunks via LLM.
    
    :param review_text: The raw review string.
    :param timeout: HTTP timeout for the OpenAI request.
    :return: A dict mapping each category to a list of sentences.
    """
    # Build the messages payload
    messages = {
        "role": "user",
        "content": f"리뷰:\n```\n{review_text}\n```\n위 규칙에 따라 의미 범주별로 JSON을 만들어 주세요."
    }
    payload = {
        "model": MODEL,
        "messages": [SYSTEM_CHUNK_PROMPT, messages],
        "temperature": 0.0
    }

    url = "https://api.openai.com/v1/chat/completions"
    try:
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=timeout)
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]

        # Extract the first JSON object from the LLM's reply
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise RuntimeError(f"No JSON object found in LLM response:\n{text}")

        chunk_dict = json.loads(match.group(0))
        return chunk_dict

    except Timeout:
        raise RuntimeError(f"LLM request timed out after {timeout}s")
    except HTTPError as he:
        code = he.response.status_code if he.response else "?"
        body = he.response.text[:200] if he.response else ""
        raise RuntimeError(f"LLM HTTP {code} error: {body}") from he
    except RequestException as re_err:
        raise RuntimeError(f"LLM request failed: {re_err}") from re_err
    except json.JSONDecodeError as je:
        raise RuntimeError(f"Failed to parse JSON from LLM response: {je}")

# Example usage:
if __name__ == "__main__":
    sample = "병원에 MRI 장비가 있지만 예약이 너무 오래 걸렸습니다. 의사 선생님이 친절했어요. 주차 공간은 협소합니다."
    chunks = chunk_review_with_llm(sample)
    print(json.dumps(chunks, ensure_ascii=False, indent=2))
