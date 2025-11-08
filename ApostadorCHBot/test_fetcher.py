#!/usr/bin/env python3
"""Quick test script for SportMonks fetcher.

Usage:
  export SPORTMONKS_API_KEY="your_key"
  python3 test_fetcher.py
"""
import os
import json
import requests
from data_fetcher_sportmonks import get_fixtures, BASE_URL


def main():
    key = os.getenv("SPORTMONKS_API_KEY")
    if not key:
        print("SPORTMONKS_API_KEY não definida. export SPORTMONKS_API_KEY='SUA_CHAVE'")
        return

    try:
        # First do a raw request to show exact URL/response for debugging
        params = {"per_page": 5, "league_id": 71}
        key = os.getenv("SPORTMONKS_API_KEY")
        if key:
            params["api_token"] = key

        url = f"{BASE_URL.rstrip('/')}/fixtures"
        print("Debug: requesting URL:", url)
        print("Debug: params:", params)
        resp = requests.get(url, params=params, timeout=10)
        print(f"Raw response status: {resp.status_code}")
        body = resp.text
        # Print some of the body for inspection (first 2000 chars)
        print(body[:2000])

        # If raw request successful, also use the fetcher wrapper
        if resp.ok:
            fixtures = get_fixtures(league_id=71, per_page=5)
            if not fixtures:
                print("Nenhum fixture retornado (lista vazia) pelo wrapper.")
                return
            print(json.dumps(fixtures[:5], indent=2, ensure_ascii=False))
            print(f"\nTotal fixtures returned: {len(fixtures)}")
        else:
            print("Request failed. Check API key / endpoint / plan. See above raw response.")
    except Exception as e:
        print("Erro ao obter fixtures:", repr(e))


if __name__ == "__main__":
    main()
