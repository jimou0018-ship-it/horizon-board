"""smoke 测试：直接用 FastAPI TestClient 校验关键流程。"""
import os
import sys
from datetime import datetime, timedelta

# 用临时数据库，避免污染实际数据
TEST_DB = "data/smoke_test.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
os.environ["HORIZON_DB"] = TEST_DB

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    # 1. 列出 sheet
    r = client.get("/api/sheets")
    sheets = r.json()
    assert len(sheets) == 2, sheets
    assert sheets[0]["name"] == "音舞热点"
    assert sheets[1]["name"] == "综艺热点"
    field_names = [f["name"] for f in sheets[0]["fields"]]
    assert field_names == ["热点名称", "日期", "平台", "点赞", "相关视频数量", "URL"], field_names
    print(f"[OK] Sheet 列表: {[s['name'] for s in sheets]}")
    print(f"[OK] 字段: {field_names}")

    sheet_id = sheets[0]["id"]
    yesterday = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")

    # 2. 插入测试数据
    samples = [
        {"热点名称": "舞台名场面 A", "日期": yesterday, "平台": "抖音", "点赞": 1200000, "相关视频数量": 320, "URL": "https://a.com/1"},
        {"热点名称": "舞台名场面 B", "日期": yesterday, "平台": "抖音", "点赞": 800000, "相关视频数量": 200, "URL": "https://a.com/2"},
        {"热点名称": "种草笔记 X", "日期": yesterday, "平台": "小红书", "点赞": 50000, "相关视频数量": 30, "URL": "https://xhs.com/1"},
        {"热点名称": "鬼畜剪辑 Y", "日期": yesterday, "平台": "B站", "点赞": 90000, "相关视频数量": 12, "URL": "https://b.com/1"},
        {"热点名称": "土味搞笑 Z", "日期": yesterday, "平台": "快手", "点赞": 30000, "相关视频数量": 8, "URL": "https://k.com/1"},
        {"热点名称": "上上周的旧热点", "日期": "2026-04-01", "平台": "抖音", "点赞": 99, "相关视频数量": 1, "URL": ""},
    ]
    for s in samples:
        r = client.post(f"/api/sheets/{sheet_id}/rows", json={"data": s})
        assert r.status_code == 200, r.text
    print(f"[OK] 插入 {len(samples)} 行")

    # 3. 列表 + 筛选
    r = client.get(f"/api/sheets/{sheet_id}/rows", params={"platform": "抖音"})
    data = r.json()
    assert data["total"] == 3, data["total"]
    print(f"[OK] 平台筛选 抖音 → {data['total']} 条")

    r = client.get(f"/api/sheets/{sheet_id}/rows", params={"keyword": "种草"})
    assert r.json()["total"] == 1
    print("[OK] 关键字搜索 种草 → 1 条")

    # 4. 看板
    r = client.get("/api/dashboard")
    dash = r.json()
    assert dash["date"] == yesterday
    assert dash["summary"]["total_rows"] == 5
    by_p = {p["platform"]: p for p in dash["platforms"]}
    assert len(by_p["抖音"]["items"]) == 2
    assert by_p["抖音"]["items"][0]["热点名称"] == "舞台名场面 A"
    assert len(by_p["小红书"]["items"]) == 1
    assert len(by_p["B站"]["items"]) == 1
    assert len(by_p["快手"]["items"]) == 1
    print(f"[OK] 看板 / 昨日({yesterday}) / 共 {dash['summary']['total_rows']} 条")
    print(f"     抖音 Top: {by_p['抖音']['items'][0]['热点名称']} ({by_p['抖音']['items'][0]['点赞']})")

    # 5. 更新
    row_id = data["rows"][0]["id"]
    r = client.put(f"/api/sheets/{sheet_id}/rows/{row_id}",
                   json={"data": {**data["rows"][0]["data"], "点赞": 9999}})
    assert r.status_code == 200
    print("[OK] 更新行")

    # 6. 导出
    r = client.get(f"/api/sheets/{sheet_id}/export")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd")
    assert len(r.content) > 100
    print(f"[OK] 导出 xlsx，大小 {len(r.content)} 字节")

    # 7. 导入
    files = {"file": ("test.xlsx", r.content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r2 = client.post(f"/api/sheets/{sheet_id}/import", files=files, data={"mode": "replace"})
    assert r2.status_code == 200, r2.text
    print(f"[OK] 导入 xlsx → 替换 {r2.json()['imported']} 行")

    # 8. 批量删除
    r = client.get(f"/api/sheets/{sheet_id}/rows", params={"platform": "抖音"})
    ids = [row["id"] for row in r.json()["rows"]]
    r = client.post(f"/api/sheets/{sheet_id}/rows/batch_delete", json={"ids": ids})
    assert r.status_code == 200
    print(f"[OK] 批量删除 {r.json()['deleted']} 行")

print("\n=== 全部测试通过 ===")
os.remove(TEST_DB)
