# config.py
import os

# 数据库文件路径
DB_PATH = os.getenv("HORIZON_DB", "data/horizon.db")

# 服务监听
HOST = os.getenv("HORIZON_HOST", "0.0.0.0")
PORT = int(os.getenv("HORIZON_PORT", "8000"))
