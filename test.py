import requests
import json

server = "http://localhost:8000"

print("=== fastAPI-TEST テスト ===")

# GETテスト
print("\n1. GET テスト")
response = requests.get(f"{server}/metrics")
print(f"結果: {response.json()}")

# POSTテスト、JSONファイルを読み込む際に使用するフォーマット
print("\n2. POST テスト（データ挿入）")
with open('host_metric.json', 'r') as f:
    data = json.load(f)
# {server}/metricsにPOSTメソッドで送った戻り値をresponseに代入する
response = requests.post(f"{server}/metrics", json=data)
print(f"結果: {response.json()}")

# メッセージ確認
print("\n3. GET テスト（挿入後確認）")
response = requests.get(f"{server}/metrics")
result = response.json()
print(f"件数: {result['count']}")

print("\n=== テスト完了 ===")

