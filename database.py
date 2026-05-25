import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
class MYSQLDB:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASS")
        self.database = os.getenv("DB_NAME")

        self.url = (
            "mysql+pymysql://star:Zth123456jkl!"
            "@rm-bp1ouw9pejr3ub4rcso.mysql.rds.aliyuncs.com/star"
        )

        # 🚀 关键优化：连接池 + 性能参数
        self.engine = create_engine(
            self.url,

            pool_size=10,  # 常驻连接
            max_overflow=20,  # 峰值连接
            pool_recycle=3600,  # 1小时回收
            pool_pre_ping=True,  # 自动检测断线

            future=True,  # SQLAlchemy 2.0 风格
            echo=False  # 生产关闭日志
        )

    # ---------------- 批量写入（优化版） ----------------
    def insert_many(self, data_list, batch_size=1000):

        if not data_list:
            return

        sql = text("""

        INSERT INTO market_bar(

            exchange,
            symbol,
            open_time,
            open,
            high,
            low,
            close,
            volume,
            oi

        )

        VALUES (

            :exchange,
            :symbol,
            :open_time,
            :open,
            :high,
            :low,
            :close,
            :volume,
            :oi
        )

        ON DUPLICATE KEY UPDATE
            open = VALUES(open),
            high = VALUES(high),
            low = VALUES(low),
            close = VALUES(close),
            volume = VALUES(volume),
            oi = VALUES(oi)
        """)

        try:

            with self.engine.begin() as conn:

                for i in range(0, len(data_list), batch_size):
                    batch = data_list[i:i + batch_size]

                    conn.execute(sql, batch)

        except Exception as e:

            print("INSERT MANY ERROR:", e)
