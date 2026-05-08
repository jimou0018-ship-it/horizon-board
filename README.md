# Horizon Board

[![Python](https://img.shields.io/badge/python-3.10+-blue)]() [![License](https://img.shields.io/badge/license-Internal-lightgrey)]()

> 轻量数据看板。多 Sheet 数据表 + Excel 导入导出 + 看板分析。无登录，直接访问。

## 功能

- **多 Sheet 数据表**：仿企微智能表的行内编辑界面
  - 默认 Sheet：`音舞热点`、`综艺热点`
  - 默认字段：`热点名称`、`日期`、`平台`、`点赞`、`相关视频数量`、`URL`
  - 行内编辑、单行/批量删除、关键字搜索、平台与日期筛选、分页
- **Excel 导入 / 导出**：`.xlsx` 一键上传，可追加或覆盖
- **看板**：昨日热点 Top10，按 抖音 / 小红书 / B站 / 快手 拆成四张小表

## 目录结构

```
horizon-board/
├── app/                  # FastAPI 后端
│   ├── main.py           # 路由
│   ├── db.py             # SQLite + 初始 Sheet
│   ├── excel_io.py       # Excel 解析/导出
│   └── config.py
├── web/                  # 前端静态页
│   ├── sheet.html        # 数据表
│   ├── dashboard.html    # 看板
│   ├── common.css
│   └── common.js
├── data/                 # SQLite 数据（运行时生成）
├── requirements.txt
├── run.py                # 本地启动入口
├── Dockerfile
└── docker-compose.yml
```

## 一、本地运行

需要 Python 3.10+。

```bash
cd horizon-board
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

浏览器打开 <http://localhost:8000> 即可使用。

数据保存在 `data/horizon.db`，备份就拷贝这个文件。

## 二、Docker 部署（推荐用于内网/云服务器）

```bash
cd horizon-board
docker compose up -d
```

访问 `http://<服务器IP>:8000`。

## 三、云服务器公网部署

最便宜的方案：腾讯云 / 阿里云 轻量应用服务器（约 ¥30-60/月，2 核 2G 完全够用）。

### 步骤
1. 买一台 Linux 服务器（Ubuntu 22.04 / Debian 12 都行）
2. 安装 Docker：
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
3. 把项目目录上传到服务器（`scp -r` 或 `git clone`）
4. 在控制台**安全组放行 8000 端口**（或你想用的端口）
5. 启动：
   ```bash
   cd horizon-board
   docker compose up -d
   ```
6. 浏览器访问 `http://<服务器公网IP>:8000`

### 想用域名 + HTTPS（可选）
推荐用 Caddy，5 行配置自动 HTTPS：
```caddy
your-domain.com {
    reverse_proxy localhost:8000
}
```
或用 Nginx + Let's Encrypt 也行。

## 安全说明

⚠️ **本服务无登录鉴权，凡能访问到 URL 的人都可读写所有数据。**

适合这些场景：
- 跑在公司内网 / 局域网
- 只把 URL 给信任的同事
- 在云服务器上配置 IP 白名单（云厂商安全组里限定来源 IP）

如果要公网完全开放但又想加点保护，可以前面套一层 Caddy/Nginx 的 Basic Auth，几行配置就行。需要的时候找我加。

## API 速览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET  | `/api/sheets` | 列出所有 Sheet 与字段 |
| GET  | `/api/sheets/{id}/rows?page=&page_size=&keyword=&platform=&date_from=&date_to=` | 查行 |
| POST | `/api/sheets/{id}/rows` | 新增行 |
| PUT  | `/api/sheets/{id}/rows/{row_id}` | 更新行 |
| DELETE | `/api/sheets/{id}/rows/{row_id}` | 删除行 |
| POST | `/api/sheets/{id}/rows/batch_delete` | 批量删除 |
| POST | `/api/sheets/{id}/import` | Excel 导入（multipart） |
| GET  | `/api/sheets/{id}/export` | Excel 导出 |
| GET  | `/api/dashboard?date=&sheet_id=` | 看板数据 |

## 后续修改

> 看板要看什么、表里要加哪些字段，直接告诉我，我改代码、重新部署。

常见的修改点：
- 加字段：`app/db.py` 里 `INITIAL_SHEETS`（首次建表时生效）
- 改看板：`app/main.py` 的 `api_dashboard` + `web/dashboard.html`
- 改首页/导航：`web/common.js` 的 `renderTopbar`
