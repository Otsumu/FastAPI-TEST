import sqlite3

DATABASE_PATH = "../data/metrics.db"
CPU_LABELS = {i: f'cpu{i}' for i in range(16)}

class ConnectMetrics: #データベース接続、テーブル設計
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
                bucket_timestamp INTEGER, --バケット開始時刻、集計期間の特定のために設定
                interval_type INTEGER, --'10min''1hour'等の時間の間隔指定で利用
                cpu_id INTEGER,
                avg_utilization INTEGER,
                max_utilization INTEGER,
                min_utilization INTEGER,
                sample_count INTEGER --集計対象データ数
            )                  
        ''')
        #timestampとcpu_idにindexを貼付
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS index_ts_cpuid ON cpu_metrics(timestamp,cpu_id);            
        ''')
        #bucket or timestampとinterval_time、cpu_idにindexを貼付
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS index_bucket_type_cpu_id ON cpu_metrics_summary(bucket_timestamp,interval_type,cpu_id);           
        ''')
    
        conn.commit()
        conn.close()
        print("データベースに接続できました")