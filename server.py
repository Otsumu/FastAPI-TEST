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
        # attributes TEXT,はJSON形式で{"cpu":"cpu0","state":"user"}のようなデータを保存
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY,
            metric_name TEXT NOT NULL,
            description TEXT,
            unit TEXT,
            attributes TEXT,  
            startTimeUnixNano TEXT,
            timeUnixNano TEXT, 
            value REAL,     
            created_at TEXT DEFAULT (datetime('now', '+9 hours'))
            )
        ''')
        conn.commit()
        conn.close()
        print("データベースとテーブルが作成されました")

    def insert_opentelemetry_data(self,otel_data:Dict[str,Any]):
        conn = sqlite3.connect('metrics.db')
        cursor = conn.cursor()

        inserted_count = 0
    
        #.get()でJSONに直接アクセスするのでrm,smの定義は不要！！
        all_metrics = []
        for resource_metrics in otel_data.get('resourceMetrics',[]):
            for scope_metrics in resource_metrics.get('scopeMetrics',[]):
                all_metrics.extend(scope_metrics.get('metrics',[]))

        try:
            for metric in all_metrics:
                metric_name = metric.get('name','')
                description = metric.get('description','')
                unit = metric.get('unit','') 
                #複雑なattributes配列 → シンプルなJSON文字列に変換
                data_points = []
                if 'sum' in metric:
                    data_points = metric['sum'].get('dataPoints',[])
                elif 'gauge'in metric:
                    data_points = metric['gauge'].get('dataPoints',[])
 
                for data_point in data_points:
                    value = data_point.get('asDouble','0')
                    timeUnixNano = data_point.get('timeUnixNano','')
                    startTimeUnixNano = data_point.get('startTimeUnixNano','')

                    attributes_array = data_point.get('attributes',[])
                    attributes_dict = {}
 
                    for attr in attributes_array:
                        attr_key = attr.get('key','')
                        #ネストしているので2段階でアクセス！
                        attr_value_obj = attr.get('value',{})
                        attr_stringValue = attr_value_obj.get('stringValue','')
                        #辞書の[キー]にアクセス、変数に文字を代入(cpu0 userなど)
                        attributes_dict[attr_key] = attr_stringValue

                    #Python辞書をJSON文字列に変換
                    attributes = json.dumps(attributes_dict)
                    #プレースホルダーを使用してのDBの挿入
                    cursor.execute('''
                        INSERT INTO metrics(metric_name,description,unit,attributes,startTimeUnixNano,timeUnixNano,value)
                        VALUES(?,?,?,?,?,?,?)         
                    ''',(metric_name,description,unit,attributes,startTimeUnixNano,timeUnixNano,value))
        
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
        #全てのメトリクスを取得する
        conn = sqlite3.connect('metrics.db')
        cursor = conn.cursor()    
        try:
            cursor.execute('SELECT * FROM metrics')
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
    formated_metrics = [
        {
            "id":m[0], 
            "metric_name":m[1], 
            "description":m[2],
            "unit":m[3],
            "attributes":m[4],
            "startTimeUnixNano": m[5],
            "timeUnixNano": m[6],
            "value": m[7],
            "created_at": m[8]
        }
        for m in metrics
    ]
    return {"count": len(metrics), "data": formated_metrics}

@app.post("/metrics")
def post_metrics(otel_data: dict):
    print(f"Inserting data: {otel_data}")
    result = db.insert_opentelemetry_data(otel_data)
    if result > 0:
        return {"status": "success", "inserted": result}
    else:
        return {"status": "error", "message": "データ挿入に失敗しました"}