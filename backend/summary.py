import sqlite3
from collections import defaultdict 
from connection import MetricsDatabase as ConnectionDB

class MetricsDatabase:
    #クラス変数の定義
    INTERVAL_TYPE = {
       1: 600,   #10min
       2: 1800,  #30min
       3: 3600,  #1hour
       4: 86400  #1day
    }

    def __init__(self, db_path: str="../data/metrics.db"):
        self.db_path = db_path
        self.CPU_LABELS = {i: f'cpu{i}' for i in range(16)}
        conn_db = ConnectionDB()
    
    def create_summary_data(self, interval_type):
        if interval_type not in MetricsDatabase.INTERVAL_TYPE:
            raise ValueError(f"時間を選択してください: {interval_type}")
        
        seconds = MetricsDatabase.INTERVAL_TYPE[interval_type]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        created_count = 0

        try:
            cursor.execute("""
            SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time
                        FROM cpu_metrics
            """)
            time_range = cursor.fetchone()
            if not time_range or not time_range[0]:
                print("集計データがありません")
                return 0
                
            min_time, max_time = time_range
            current_time = min_time
            while current_time <= max_time:
                next_time = current_time + seconds

            conn.commit()
            print(f"{created_count}件のデータが作成できました")
            return created_count
        
        except Exception as error:
            print(f"予期しないエラー：{error}")
            conn.rollback()
            return 0
        finally:
            conn.close()