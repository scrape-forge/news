# -*- coding: utf-8 -*-
"""
Groq AI News Tagger Module (Free Tier — Llama-3.1-8b-instant).
Extracts standardized Indonesian news tags from title and summary at zero cost.
"""

import json
import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-8b-instant"


def generate_ai_tags(title: str, summary: str = "") -> list:
    """
    Extracts 2 to 4 standardized Indonesian news tags using Groq's Free Llama-3.1 API.
    Returns a list of clean tag strings (e.g. ['IKN', 'Politik']).
    Returns an empty list if GROQ_API_KEY is not set or network fails.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return []

    system_prompt = (
        "You are an Indonesian news categorization system. "
        "Extract 2 to 4 standardized Indonesian topic tags from the news headline and summary. "
        "Use clean short tags (e.g. 'IKN', 'Pilkada', 'Suku Bunga BI', 'Inflasi', 'Ekonomi', 'Teknologi', 'Politik', 'Otomotif', 'Sepakbola'). "
        "Return ONLY a valid JSON array of string tags. Example output: [\"IKN\", \"Politik\"]"
    )

    user_text = f"Headline: {title}\nSummary: {summary}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content'].strip()
            # Extract JSON array substring if needed
            start_idx = content.find('[')
            end_idx = content.rfind(']')
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx + 1]
                tags = json.loads(content)
                return [str(t).strip().title() for t in tags if isinstance(t, str)]
    except Exception:
        pass

    return []
