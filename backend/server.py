from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from insert import InsertMetrics
from summary import CreateSummary
from typing import Optional

app = FastAPI()

# フロントエンドの静的ファイルを使用するためにFastAPIのStaticFilesを設定
app.mount("/frontend/static", StaticFiles(directory="../frontend/static"), name="static")

db = InsertMetrics()
summary_db = CreateSummary()

@app.get("/api/metrics")
def get_metrics(mode: str ="realtime"):
    """生データの取得"""
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


 #get_summary_dataのデータポイント設定
 #cpu_id: int = None = Union[int, None]と同じ意味
 #cpu_idが整数 or Noneであることを示すためのFastAPIの型ヒント、
 #cpu_idの指定がない場合、Noneをデフォルト値として使用、全てのCPUの集計データが返される(interval_typeも同様)
@app.get("/api/summary")
def get_summary_data(start_timestamp: int, end_timestamp: int, 
                     cpu_id: Optional[int] = None, interval_type: Optional[int] = None):
    """集計加工データの取得"""
    print(f"=== API呼び出し ===")
    print(f"interval_type: {interval_type}")
    summary_data = summary_db.get_summary_data(start_timestamp, end_timestamp, cpu_id, interval_type)
    print(f"取得件数: {len(summary_data)}")
    return summary_data

@app.post("/api/summary")
def create_summary(seconds: int = 600, index: int = 0):
    created_count = summary_db.create_summary_data(seconds, index)
    if created_count > 0:
        return {"status": "success", "created": created_count}
    else:
        return {"status": "error", "message": "集計データ作成に失敗しました"} 