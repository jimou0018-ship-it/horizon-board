FROM python:3.11-slim

WORKDIR /app

# 复制依赖并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制代码
COPY app/ ./app/
COPY web/ ./web/
COPY run.py .

# 数据目录（挂载点）
RUN mkdir -p /app/data
VOLUME ["/app/data"]

ENV HORIZON_DB=/app/data/horizon.db
ENV HORIZON_HOST=0.0.0.0
ENV HORIZON_PORT=8000

EXPOSE 8000

CMD ["python", "run.py"]
