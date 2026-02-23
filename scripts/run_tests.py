"""
Test Runner — user-based-retrieval endpoint
Reads financial_test_profiles_20.json, hits POST /api/v2/user-based-retrieval/
for each profile, and saves Q&A output to output.txt as JSON.
"""
import json
import time
import asyncio
import httpx
from pathlib import Path

BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/v2/user-based-retrieval/"
INPUT_FILE = Path(__file__).parent.parent / "financial_test_profiles_20.json"
OUTPUT_FILE = Path(__file__).parent.parent / "output.txt"

DELAY_BETWEEN_REQUESTS = 3  # seconds — avoids Gemini rate limits


async def run_tests():
    profiles = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    results = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        for idx, profile in enumerate(profiles, start=1):
            user_name = profile.get("user", {}).get("name", f"User_{idx}")
            query = profile.get("query", "Evaluate my financial profile")

            print(f"[{idx:02d}/{len(profiles)}] {user_name} — {query}")

            # Remove financialHealthScore from payload if score is 0/empty
            # (it's optional — the endpoint accepts it fine either way)
            payload = {k: v for k, v in profile.items() if k != "financialHealthScore"}

            try:
                response = await client.post(
                    f"{BASE_URL}{ENDPOINT}",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                answer = data.get("answer", "")
                results.append({
                    "id": idx,
                    "user": user_name,
                    "question": query,
                    "answer": answer,
                })
                print(f"      ✅ Done ({len(answer)} chars)")
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                print(f"      ❌ Error: {error_msg}")
                results.append({
                    "id": idx,
                    "user": user_name,
                    "question": query,
                    "answer": None,
                    "error": error_msg,
                })
            except Exception as e:
                print(f"      ❌ Exception: {e}")
                results.append({
                    "id": idx,
                    "user": user_name,
                    "question": query,
                    "answer": None,
                    "error": str(e),
                })

            # Rate-limit buffer between calls
            if idx < len(profiles):
                time.sleep(DELAY_BETWEEN_REQUESTS)

    # Write output
    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\n✅ Done! Output saved to: {OUTPUT_FILE}")
    print(f"   Total: {len(results)} | Success: {sum(1 for r in results if r.get('answer'))} | Errors: {sum(1 for r in results if r.get('error'))}")


if __name__ == "__main__":
    asyncio.run(run_tests())
