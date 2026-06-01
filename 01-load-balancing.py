import json
import os
import time

from dotenv import load_dotenv
from openai import APIStatusError, AzureOpenAI

load_dotenv()

GATEWAY_URL = os.environ["APIM_GATEWAY_URL"]
SUBSCRIPTION_KEY = os.environ["APIM_SUBSCRIPTION_KEY"]
INFERENCE_API_PATH = os.environ.get("INFERENCE_API_PATH", "inference")
API_VERSION = os.environ.get("INFERENCE_API_VERSION", "2025-03-01-preview")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4.1-mini")

RUNS = int(os.environ.get("RUNS", "30"))
SLEEP_TIME_MS = int(os.environ.get("SLEEP_TIME_MS", "100"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "50"))

client = AzureOpenAI(
    azure_endpoint=f"{GATEWAY_URL}/{INFERENCE_API_PATH}",
    api_key=SUBSCRIPTION_KEY,
    api_version=API_VERSION,
)

api_runs: list[tuple[float, str]] = []

for i in range(RUNS):
    print(f"Run {i + 1}/{RUNS}:")

    start_time = time.time()
    try:
        raw_response = client.chat.completions.with_raw_response.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": "You are a sarcastic, unhelpful assistant."},
                {"role": "user", "content": "Can you tell me the time, please?"},
            ],
        )
    except APIStatusError as exc:
        # 全バックエンド枯渇時は on-error ポリシーで 503 が返る。記録して継続する。
        response_time = time.time() - start_time
        region = exc.response.headers.get("x-ms-region", "unavailable")
        print(f"  {response_time:.2f} sec / status={exc.status_code} / x-ms-region={region}")
        api_runs.append((response_time, region))
        time.sleep(SLEEP_TIME_MS / 1000)
        continue

    response_time = time.time() - start_time

    region = raw_response.headers.get("x-ms-region", "unknown")
    status = raw_response.http_response.status_code
    print(f"  {response_time:.2f} sec / status={status} / x-ms-region={region}")

    response = raw_response.parse()
    if response.usage:
        print(
            "  tokens: "
            f"total={response.usage.total_tokens} "
            f"prompt={response.usage.prompt_tokens} "
            f"completion={response.usage.completion_tokens}"
        )

    api_runs.append((response_time, region))
    time.sleep(SLEEP_TIME_MS / 1000)

with open("result.json", "w", encoding="utf-8") as f:
    json.dump(api_runs, f, ensure_ascii=False, indent=2)

print(f"\n保存しました: result.json ({len(api_runs)} 件)")

# リージョン別の件数を集計して表示する
counts: dict[str, int] = {}
for _, region in api_runs:
    counts[region] = counts.get(region, 0) + 1
print("リージョン別件数:")
for region, count in sorted(counts.items()):
    print(f"  {region}: {count}")
