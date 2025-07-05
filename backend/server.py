from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from insert import InsertMetrics

app = FastAPI()

# フロントエンドの静的ファイルを使用するためにFastAPIのStaticFilesを設定
app.mount("/frontend/static", StaticFiles(directory="../frontend/static"), name="static")

db = InsertMetrics()

@app.get("/api/metrics")
def get_metrics(mode: str ="realtime"):
    metrics = db.get_metrics(mode)
    return metrics

@app.post("/api/metrics")
def post_metrics(json_data: dict):
    print(f"Inserting data: {json_data}")
    result = db.insert_cpu_utilization(json_data)
    if result > 0:
        return {"status": "success", "inserted": result}
    else:
        return {"status": "error", "message": "データ挿入に失敗しました"}
