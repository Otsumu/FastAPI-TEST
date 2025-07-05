import sqlite3

class CreateSummary: #集計処理
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

    def create_summary_data(self, interval_type):
        if interval_type not in CreateSummary.INTERVAL_TYPE:
            raise ValueError(f"時間を選択してください: {interval_type}")
        
        seconds = CreateSummary.INTERVAL_TYPE[interval_type]

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
            
                for cpu_id in self.CPU_LABELS:    
                    cursor.execute("""
                        SELECT
                            AVG(utilization) as avg_util,
                            MAX(utilization) as max_util,
                            MIN(utilization) as min_util,
                            COUNT(*) as sample_count
                        FROM cpu_metrics
                        WHERE timestamp >= ? AND timestamp < ? AND cpu_id = ?
                    """,(current_time, next_time, cpu_id))

                    result = cursor.fetchone()
                    avg_util = int(result[0]) if result[0] is not None else 0
                    max_util = int(result[1]) if result[1] is not None else 1 
                    min_util = int(result[2]) if result[2] is not None else 2
                    sample_count = int(result[3]) if result[3] is not None else 3

                    cursor.execute("""
                    INSERT INTO cpu_metrics_summary(bucket_timestamp, interval_type, cpu_id, avg_utilization, max_utilization, min_utilization, sample_count)
                        VALUES(?, ?, ?, ?, ?, ?, ?)
                    """, (current_time, interval_type, cpu_id , avg_util, max_util, min_util, sample_count))
                    created_count += 1

                current_time += seconds
            
            conn.commit()
            print(f"{created_count}件のデータが作成できました")
            return created_count
        
        except Exception as error:
            print(f"予期しないエラー：{error}")
            conn.rollback()
            return 0
        finally:
            conn.close()