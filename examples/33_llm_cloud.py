"""Ray Data LLM — send one small request to a cloud-hosted model."""

import os

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Skipping: set OPENAI_API_KEY to run this cloud LLM example.")
    raise SystemExit(0)

import ray
from ray.data.llm import HttpRequestProcessorConfig, build_processor

from _ray_config import init_ray

init_ray()

dataset = ray.data.from_items(
    [{"prompt": "Reply with exactly these three words: Ray LLM works."}]
)
config = HttpRequestProcessorConfig(
    url="https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    qps=1,
)
processor = build_processor(
    config,
    preprocess=lambda row: {
        "payload": {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": row["prompt"]}],
            "temperature": 0,
            "max_tokens": 8,
        }
    },
    postprocess=lambda row: {
        "response": row["http_response"]["choices"][0]["message"]["content"]
    },
)

result = processor(dataset).take_all()[0]
print("model response:", result["response"], flush=True)
