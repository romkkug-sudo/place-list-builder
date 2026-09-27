"""Google Places API (Text Search) を使って、名称とエリアから電話番号を取得する。"""
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = "places.displayName,places.formattedAddress,places.nationalPhoneNumber"


def _get_api_key() -> str:
    """APIキーは .env（環境変数）から読み込む。コードには直接書かない。"""
    key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "環境変数 GOOGLE_MAPS_API_KEY が設定されていません。"
            ".env.example をコピーして .env を作成し、APIキーを設定してください。"
        )
    return key


def get_phone(name: str, area: str, retries: int = 3, wait: float = 2.0) -> str:
    """名称とエリアで検索し、電話番号を返す。見つからない場合は空文字を返す。

    - 通信エラー・APIエラー時は最大 retries 回までリトライする
    - 検索結果の住所に area が含まれない場合は、別の場所の誤取得とみなして採用しない
    """
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": _get_api_key(),
        "X-Goog-FieldMask": FIELD_MASK,
    }
    payload = {
        "textQuery": f"{name} {area}",
        "languageCode": "ja",
        "regionCode": "JP",
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        except requests.RequestException as e:
            print(f"  通信エラー（{attempt}/{retries}回目）: {e}")
            time.sleep(wait)
            continue

        if response.status_code != 200:
            print(f"  APIエラー（{attempt}/{retries}回目）: ステータス {response.status_code}")
            time.sleep(wait)
            continue

        places = response.json().get("places", [])
        if not places:
            return ""

        place = places[0]
        found_address = place.get("formattedAddress", "")

        # 誤取得防止：エリアが一致しない結果は採用しない
        if area and area not in found_address:
            print(f"  エリア不一致のためスキップ: {found_address}")
            return ""

        return place.get("nationalPhoneNumber", "")

    return ""
