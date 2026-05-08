# run.py —— 本地直接启动入口
import uvicorn
from app import config

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
    )
