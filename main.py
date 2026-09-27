"""リスト作成ツール：名称リストに電話番号を付けてCSV出力する。

使い方:
    python main.py --input sample_input.csv          # 既存のCSVに電話番号を付ける
    python main.py --scrape --max-pages 5             # 一覧ページから収集して電話番号を付ける
"""
import argparse
import csv
import os
import time

from phone_lookup import get_phone

OUTPUT_HEADER = ["名称", "エリア", "URL", "カテゴリ", "電話番号"]


def load_input(path: str) -> list[list[str]]:
    """入力CSV（名称, エリア, URL, カテゴリ）を読み込む。1行目は見出しとして読み飛ばす。"""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader, None)
        rows = []
        for row in reader:
            if len(row) < 2:
                continue
            rows.append((row + ["", ""])[:4])
        return rows


def dedupe(rows: list[list[str]]) -> list[list[str]]:
    """名称とエリアが同じ行を除外し、名称が空・N/Aの行も除く。"""
    seen = set()
    result = []
    for name, area, url, category in rows:
        name, area = name.strip(), area.strip()
        if not name or name == "N/A":
            continue
        key = (name, area)
        if key in seen:
            continue
        seen.add(key)
        result.append([name, area, url, category])
    return result


def load_completed(path: str) -> set[tuple[str, str]]:
    """出力済みCSVから、処理済みの（名称, エリア）を読み込む。途中再開に使う。"""
    if not os.path.exists(path):
        return set()
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader, None)
        return {(row[0], row[1]) for row in reader if len(row) >= 2}


def main() -> None:
    parser = argparse.ArgumentParser(description="名称リストに電話番号を付けてCSV出力します")
    parser.add_argument("--input", default="sample_input.csv", help="入力CSVのパス")
    parser.add_argument("--output", default="output.csv", help="出力CSVのパス")
    parser.add_argument("--scrape", action="store_true", help="入力CSVの代わりに一覧ページから収集する")
    parser.add_argument("--max-pages", type=int, default=50, help="--scrape 時の最大ページ数")
    args = parser.parse_args()

    if args.scrape:
        from scraper import scrape
        rows = scrape(args.max_pages)
    else:
        rows = load_input(args.input)

    targets = dedupe(rows)
    completed = load_completed(args.output)
    print(f"対象: {len(targets)}件（重複除外後） / 処理済み: {len(completed)}件")

    found = not_found = skipped = 0
    write_header = not os.path.exists(args.output)

    with open(args.output, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(OUTPUT_HEADER)

        for name, area, url, category in targets:
            if (name, area) in completed:
                skipped += 1
                continue

            print(f"取得中: {name}")
            phone = get_phone(name, area)
            writer.writerow([name, area, url, category, phone])
            f.flush()  # 途中で止まっても、そこまでの結果を残す

            if phone:
                found += 1
            else:
                not_found += 1
            time.sleep(1)  # API への負荷を抑える

    print(f"完了: 取得成功 {found}件 / 取得できず {not_found}件 / スキップ {skipped}件")
    print(f"出力ファイル: {args.output}")


if __name__ == "__main__":
    main()
