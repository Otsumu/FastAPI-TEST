from fastapi import FastAPI
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any

app = FastAPI()

class MetricsDatabase:
    def __init__(self, db_path:str="metrics.db"):
        self.db_path = db_path
        self.init_database() #データベースの初期設定
    
    def init_database(self):
        conn = sqlite3.connect('metrics.db')
        cursor = conn.cursor()
        cursor.execute ('''
            CREATE TABLE IF NOT EXISTS cpu_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_name TEXT,
                utilization REAL
            )
       ''')
        conn.commit()
        conn.close()
        print("データベースに接続できました")

    def insert_cpu_utilization(self, json_data: Dict[str, Any]):
        conn = sqlite3.connect('metrics.db')
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

                        # タイムスタンプを変換
                        timestamp_nano = data_point.get('timeUnixNano', 0)
                        if timestamp_nano:
                            timestamp = datetime.fromtimestamp(int(timestamp_nano) / 1000000000).isoformat()
                        
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

    def get_all_metrics(self):
        conn = sqlite3.connect('metrics.db')
        cursor = conn.cursor()    
        try:
            cursor.execute('SELECT * FROM cpu_metrics')
            rows = cursor.fetchall()
            return rows
        except Exception as error:
            print(f"取得エラー: {error}")
            return []
        finally:
            conn.close()    

db = MetricsDatabase()

@app.get("/metrics")
def get_metrics():
    metrics = db.get_all_metrics()
    formatted_metrics = [  
        {
            "id": m[0], 
            "timestamp": m[1],  
            "cpu_name": m[2],
            "utilization": m[3],
        }
        for m in metrics
    ]
    return {"count": len(metrics), "data": formatted_metrics}

@app.post("/metrics")
def post_metrics(json_data: dict):
    print(f"Inserting data: {json_data}")
    result = db.insert_cpu_utilization(json_data)
    if result > 0:
        return {"status": "success", "inserted": result}
    else:
        return {"status": "error", "message": "データ挿入に失敗しました"}