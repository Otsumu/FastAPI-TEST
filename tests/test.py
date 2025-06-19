import requests
import json

server = "http://localhost/api"

print("=== fastAPI-TEST テスト ===")

# GETテスト
print("\n1. GET テスト")
response = requests.get(f"{server}/metrics")
print(f"結果: {response.json()}")

# POSTテスト、JSONファイルを読み込む際に使用するフォーマット
print("\n2. POST テスト（データ挿入）")

with open('../data/metric.jsonl', 'r') as f:
    lines = f.readlines()

total_inserted = 0

for line_num, line in enumerate(lines, 1):
    if line.strip():
        try:
            data = json.loads(line.strip())  # 1行ずつJSONとして読み込み
            response = requests.post(f"{server}/metrics", json=data)
            result = response.json()
            print(f"行{line_num}: {result}")
            
            if result.get("status") == "success":
                total_inserted += result.get("inserted", 0)
        except Exception as e:
            print(f"行{line_num}: エラー - {e}")

print(f"\n合計挿入件数: {total_inserted}")

# メッセージ確認
print("\n3. GET テスト（挿入後確認）")
response = requests.get(f"{server}/metrics")
result = response.json()
print(f"件数: {result['count']}")

print("\n=== テスト完了 ===")

