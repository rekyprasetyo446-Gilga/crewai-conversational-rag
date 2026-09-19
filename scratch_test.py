import os
import sys
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"API key loaded: {api_key[:10]}...", flush=True)

from crewai import LLM

for m in ["gemini/gemini-2.0-flash", "gemini/gemini-1.5-flash", "gemini/gemini-2.5-flash", "gemini/gemini-3.6-flash"]:
    print(f"Testing model: {m}...", flush=True)
    try:
        llm = LLM(model=m, api_key=api_key)
        # Test basic call
        response = llm.call(messages=[{"role": "user", "content": "Say hello"}])
        print(f"  -> SUCCESS ({m}): {response[:40]}", flush=True)
    except Exception as e:
        print(f"  -> ERROR ({m}): {type(e).__name__} - {e}", flush=True)
