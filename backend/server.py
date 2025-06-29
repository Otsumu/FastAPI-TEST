from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sqlite3
from datetime import datetime
from collections import defaultdict 

app = FastAPI()

# フロントエンドの静的ファイルを提供するためにFastAPIのStaticFilesを使用
app.mount("/frontend/static", StaticFiles(directory="../frontend/static"), name="static")

class MetricsDatabase:
    def __init__(self, db_path: str="../data/metrics.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute ('''
            CREATE TABLE IF NOT EXISTS cpu_metrics (
                id INTEGER PRIMARY KEY,
                timestamp INTEGER,
                cpu_name TEXT,
                utilization REAL
            )
       ''')
        conn.commit()
        conn.close()
        print("データベースに接続できました")
        

    def insert_cpu_utilization(self, json_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        inserted_count = 0
        
        try:    
            all_metrics = []
            for resource_metrics in json_data.get('resourceMetrics',[]):
                for scope_metrics in resource_metrics.get('scopeMetrics',[]):
                    all_metrics.extend(scope_metrics.get('metrics',[]))

            for metric in all_metrics:
                if metric.get('name') == 'system.cpu.utilization':
                    data_points = metric.get('gauge', {}).get('dataPoints', [])
                    #ループの都度初期化
                    for data_point in data_points:
                        cpu_name = ''
                        idle_rate = 0
                        timestamp = ''
                        
                        attributes = data_point.get('attributes', [])
                        for attr in attributes:
                            if attr.get('key') == 'cpu':
                                cpu_name = attr.get('value', {}).get('stringValue', '')
                            if attr.get('key') == 'state':
                                state = attr.get('value', {}).get('stringValue', '')
                                if state == 'idle':
                                    idle_rate = data_point.get('asDouble', 0)

                        # タイムスタンプの取得
                        # timeUnixNanoが存在する場合、ナノ秒単位のタイムスタンプを取得
                        # もしtimeUnixNanoが存在しない場合は、0をデフォルト値として使用
                        # timeUnixNanoはナノ秒単位なので、秒単位に変換する必要がある
                        timestamp_nano = data_point.get('timeUnixNano', 0)
                        if timestamp_nano:
                            #ナノ秒（10⁻⁹秒）を秒単位に変換するため、10億で割る
                            timestamp = datetime.fromtimestamp(int(timestamp_nano) / 1000000000).isoformat()
                        # CPU使用率の計算
                        utilization = (1 - idle_rate) * 100

                        if cpu_name and timestamp:
                            cursor.execute('''
                                INSERT INTO cpu_metrics(timestamp, cpu_name, utilization)
                                VALUES(?, ?, ?)
                            ''', (timestamp, cpu_name, utilization))  
                            inserted_count += 1
            
            conn.commit()
            print(f"{inserted_count}件のデータが挿入されました")
            return inserted_count

        except Exception as error:
            print(f"予期しないエラー：{error}")
            conn.rollback()
            return 0
        finally:
            conn.close()

    def get_metrics(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()    
        try:
            cursor.execute('SELECT timestamp, cpu_name, utilization FROM cpu_metrics ORDER BY timestamp, cpu_name')
            rows = cursor.fetchall()

            series_data = defaultdict(list)
            for timestamp, cpu_name, utilization in rows:
                series_data[cpu_name].append({
                    "timestamp": timestamp,
                    "utilization": utilization
                })
            return dict(series_data)
                   
        except Exception as error:
            print(f"取得エラー: {error}")
            return {}
        finally:
            conn.close()    

db = MetricsDatabase()

@app.get("/api/metrics")
def get_metrics():
    metrics = db.get_metrics()
    return metrics

@app.post("/api/metrics")
def post_metrics(json_data: dict):
    print(f"Inserting data: {json_data}")
    result = db.insert_cpu_utilization(json_data)
    if result > 0:
        return {"status": "success", "inserted": result}
    else:
        return {"status": "error", "message": "データ挿入に失敗しました"}

          