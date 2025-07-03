from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sqlite3
from datetime import datetime
from collections import defaultdict 

app = FastAPI()

# フロントエンドの静的ファイルを使用するためにFastAPIのStaticFilesを設定
app.mount("/frontend/static", StaticFiles(directory="../frontend/static"), name="static")

class MetricsDatabase:
    def __init__(self, db_path: str="../data/metrics.db"):
        self.db_path = db_path
        self.CPU_LABELS = {i: f'cpu{i}' for i in range(16)}
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        #生データテーブル
        cursor.execute ('''
            CREATE TABLE IF NOT EXISTS cpu_metrics (
                id INTEGER PRIMARY KEY,
                timestamp INTEGER NOT NULL, --UNIX秒
                cpu_id INTEGER, -- cpu_name → cpu_id に改名
                utilization INTEGER CHECK (utilization BETWEEN 0 AND 7000) -- CPU使用率は0から70の範囲
            )
       ''')
        #集計データテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cpu_metrics_summary (
                id INTEGER PRIMARY KEY,
                bucket_timestamp INTEGER, --バケット開始時刻
                interval_type TEXT, --'10min''1hour'等の時間の間隔指定で利用
                cpu_id INTEGER,
                avg_utilization INTEGER,
                max_utilization INTEGER,
                min_utilization INTEGER
            )                  
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS index_ts_cpuid ON cpu_metrics(timestamp,cpu_id);            
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS index_bucket_type_cpu_id ON cpu_metrics_summary(bucket_timestamp,interval_type,cpu_id);           
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
                        cpu_id = None
                        idle_rate = 0
                        timestamp = None
                        
                        attributes = data_point.get('attributes', [])
                        for attr in attributes:
                            if attr.get('key') == 'cpu':
                                cpu_name = attr.get('value', {}).get('stringValue', '')
                                if cpu_name.startswith('cpu') :
                                    try:
                                        cpu_id = int(cpu_name.replace('cpu',''))
                                    except ValueError:
                                        cpu_id = None
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
                            try:
                            #ナノ秒（10⁻⁹秒）を秒単位に変換するため、10億で割る
                                timestamp_nano_int = int(timestamp_nano)
                                timestamp = timestamp_nano_int // 1000000000
                            except (ValueError,TypeError):
                                timestamp = None
                        # CPU使用率の計算
                        utilization = (1 - idle_rate) * 100
                        utilization_int = int(utilization * 100)

                        if cpu_id is not None and timestamp is not None:
                            cursor.execute('''
                                INSERT INTO cpu_metrics(timestamp, cpu_id, utilization)
                                VALUES(?, ?, ?)
                            ''', (timestamp, cpu_id, utilization))  
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

    def get_metrics(self, mode ="realtime"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()    
        try:
            if mode == "realtime":
                query = """
                    SELECT timestamp, cpu_id, utilization 
                    FROM cpu_metrics 
                    ORDER BY timestamp, cpu_id
                """
            elif mode == "10minutes":
                query = """
                    SELECT strftime('%Y-%m-%d %H:', timestamp, 'unixepoch','localtime') || printf('%02d:00', (CAST(strftime('%M', timestamp, 'unixepoch','localtime') AS INTEGER) / 10) * 10) AS bucket,
                           cpu_id, 
                           AVG(utilization) as avg_value,
                           COUNT(utilization) as count_value
                    FROM cpu_metrics
                    GROUP BY bucket, cpu_id
                    ORDER BY bucket, cpu_id
                """
            elif mode == "1hour":
                query = """
                    SELECT strftime('%Y-%m-%d %H:00:00', timestamp, 'unixepoch','localtime') AS bucket, 
                           cpu_id, 
                           AVG(utilization) as avg_value,
                           COUNT(utilization) as count_value
                    FROM cpu_metrics
                    GROUP BY bucket, cpu_id
                    ORDER BY bucket, cpu_id
                """
            else:
                raise ValueError("いずれかの時間を指定してください")
            
            cursor.execute(query)
            rows = cursor.fetchall()
           
            series_data = defaultdict(list)
            if mode == "realtime":
                for bucket_or_ts, cpu_id, utilization, in rows:
                    label = self.CPU_LABELS.get(cpu_id, f'cpu{cpu_id}')
                    series_data[label].append({
                        "timestamp": bucket_or_ts,
                        "utilization": utilization
                })
            else:
                for bucket_or_ts, cpu_id, utilization, count_value in rows:
                    print(f"COUNT : {count_value}")
                    label = self.CPU_LABELS.get(cpu_id, f'cpu{cpu_id}')
                    series_data[label].append({
                        "timestamp": bucket_or_ts,
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
