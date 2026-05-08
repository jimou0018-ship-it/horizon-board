# main.py
"""Horizon Board —— 数据看板服务入口（无登录版）。"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import io

from . import config, db, excel_io


app = FastAPI(title="Horizon Board")

# 静态前端
STATIC_DIR = Path(__file__).parent.parent / "web"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def _startup():
    db.init_db()


# ---------- 页面 ----------
def _read_html(name: str) -> str:
    return (STATIC_DIR / name).read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def index_page():
    return HTMLResponse(_read_html("dashboard.html"))


@app.get("/sheet", response_class=HTMLResponse)
def sheet_page():
    return HTMLResponse(_read_html("sheet.html"))


# ---------- Sheet ----------
@app.get("/api/sheets")
def api_list_sheets():
    with db.get_conn() as conn:
        sheets = conn.execute(
            "SELECT id, name FROM sheets ORDER BY sort_order, id"
        ).fetchall()
        result = []
        for s in sheets:
            fields = conn.execute(
                "SELECT id, name, type FROM fields WHERE sheet_id = ? ORDER BY sort_order, id",
                (s["id"],),
            ).fetchall()
            result.append(
                {
                    "id": s["id"],
                    "name": s["name"],
                    "fields": [dict(f) for f in fields],
                }
            )
    return result


def _get_sheet(conn, sheet_id: int):
    s = conn.execute("SELECT id, name FROM sheets WHERE id = ?", (sheet_id,)).fetchone()
    if not s:
        raise HTTPException(404, "sheet 不存在")
    fields = conn.execute(
        "SELECT name, type FROM fields WHERE sheet_id = ? ORDER BY sort_order, id",
        (sheet_id,),
    ).fetchall()
    return s, [dict(f) for f in fields]


# ---------- 行 CRUD ----------
@app.get("/api/sheets/{sheet_id}/rows")
def api_list_rows(
    sheet_id: int,
    page: int = 1,
    page_size: int = 50,
    keyword: str = "",
    platform: str = "",
    date_from: str = "",
    date_to: str = "",
):
    page = max(1, page)
    page_size = max(1, min(500, page_size))
    offset = (page - 1) * page_size

    where = ["sheet_id = ?"]
    args: list = [sheet_id]

    if keyword:
        where.append("data LIKE ?")
        args.append(f"%{keyword}%")
    if platform:
        where.append("json_extract(data, '$.\"平台\"') = ?")
        args.append(platform)
    if date_from:
        where.append("json_extract(data, '$.\"日期\"') >= ?")
        args.append(date_from)
    if date_to:
        where.append("json_extract(data, '$.\"日期\"') <= ?")
        args.append(date_to)

    where_sql = " AND ".join(where)

    with db.get_conn() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM rows WHERE {where_sql}", args
        ).fetchone()["c"]
        rows = conn.execute(
            f"SELECT id, data, created_at FROM rows WHERE {where_sql} "
            f"ORDER BY json_extract(data, '$.\"日期\"') DESC, id DESC "
            f"LIMIT ? OFFSET ?",
            args + [page_size, offset],
        ).fetchall()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "rows": [
            {"id": r["id"], "data": json.loads(r["data"]), "created_at": r["created_at"]}
            for r in rows
        ],
    }


@app.post("/api/sheets/{sheet_id}/rows")
def api_create_row(sheet_id: int, payload: dict):
    with db.get_conn() as conn:
        _get_sheet(conn, sheet_id)
        data = payload.get("data") or {}
        cur = conn.execute(
            "INSERT INTO rows(sheet_id, data) VALUES (?, ?)",
            (sheet_id, json.dumps(data, ensure_ascii=False)),
        )
        return {"id": cur.lastrowid}


@app.put("/api/sheets/{sheet_id}/rows/{row_id}")
def api_update_row(sheet_id: int, row_id: int, payload: dict):
    data = payload.get("data") or {}
    with db.get_conn() as conn:
        cur = conn.execute(
            "UPDATE rows SET data = ? WHERE id = ? AND sheet_id = ?",
            (json.dumps(data, ensure_ascii=False), row_id, sheet_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "记录不存在")
    return {"ok": True}


@app.delete("/api/sheets/{sheet_id}/rows/{row_id}")
def api_delete_row(sheet_id: int, row_id: int):
    with db.get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM rows WHERE id = ? AND sheet_id = ?", (row_id, sheet_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "记录不存在")
    return {"ok": True}


@app.post("/api/sheets/{sheet_id}/rows/batch_delete")
def api_batch_delete(sheet_id: int, payload: dict):
    ids = payload.get("ids") or []
    if not ids:
        return {"deleted": 0}
    placeholders = ",".join(["?"] * len(ids))
    with db.get_conn() as conn:
        cur = conn.execute(
            f"DELETE FROM rows WHERE sheet_id = ? AND id IN ({placeholders})",
            [sheet_id] + ids,
        )
        return {"deleted": cur.rowcount}


# ---------- Excel 导入 / 导出 ----------
@app.post("/api/sheets/{sheet_id}/import")
async def api_import(sheet_id: int, file: UploadFile = File(...), mode: str = Form("append")):
    """mode = append (追加) | replace (清空后导入)"""
    content = await file.read()
    with db.get_conn() as conn:
        _, fields = _get_sheet(conn, sheet_id)
        field_names = [f["name"] for f in fields]
        records = excel_io.parse_excel(content, field_names)

        if mode == "replace":
            conn.execute("DELETE FROM rows WHERE sheet_id = ?", (sheet_id,))

        for rec in records:
            conn.execute(
                "INSERT INTO rows(sheet_id, data) VALUES (?, ?)",
                (sheet_id, json.dumps(rec, ensure_ascii=False)),
            )
    return {"imported": len(records)}


@app.get("/api/sheets/{sheet_id}/export")
def api_export(sheet_id: int):
    with db.get_conn() as conn:
        s, fields = _get_sheet(conn, sheet_id)
        field_names = [f["name"] for f in fields]
        rows = conn.execute(
            "SELECT data FROM rows WHERE sheet_id = ? "
            "ORDER BY json_extract(data, '$.\"日期\"') DESC, id DESC",
            (sheet_id,),
        ).fetchall()
        records = [json.loads(r["data"]) for r in rows]

    blob = excel_io.build_excel(field_names, records)
    filename = f"{s['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    quoted = quote(filename)
    return StreamingResponse(
        io.BytesIO(blob),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=\"{quoted}\"; filename*=UTF-8''{quoted}"
        },
    )


# ---------- 看板 ----------
PLATFORMS = ["抖音", "小红书", "B站", "快手"]


@app.get("/api/dashboard")
def api_dashboard(date: str = "", sheet_id: int | None = None):
    """
    返回昨日热点 Top10（按平台分四组）。
    - date：传 YYYY-MM-DD 可指定日期；缺省 = 昨天
    - sheet_id：可选，限定某一个 sheet；缺省 = 所有 sheet 合并
    """
    if not date:
        date = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")

    args: list = [date]
    sheet_filter = ""
    if sheet_id:
        sheet_filter = " AND sheet_id = ?"
        args.append(sheet_id)

    with db.get_conn() as conn:
        sheets = conn.execute(
            "SELECT id, name FROM sheets ORDER BY sort_order, id"
        ).fetchall()
        sheet_map = {s["id"]: s["name"] for s in sheets}

        rows = conn.execute(
            f"""
            SELECT id, sheet_id, data FROM rows
            WHERE json_extract(data, '$."日期"') = ?{sheet_filter}
            """,
            args,
        ).fetchall()

    by_platform: dict[str, list] = {p: [] for p in PLATFORMS}
    other_bucket: list = []
    for r in rows:
        d = json.loads(r["data"])
        plat = (d.get("平台") or "").strip()
        item = {
            "id": r["id"],
            "sheet_id": r["sheet_id"],
            "sheet_name": sheet_map.get(r["sheet_id"], ""),
            "热点名称": d.get("热点名称", ""),
            "日期": d.get("日期", ""),
            "平台": plat,
            "点赞": _to_int(d.get("点赞")),
            "相关视频数量": _to_int(d.get("相关视频数量")),
            "URL": d.get("URL", ""),
        }
        if plat in by_platform:
            by_platform[plat].append(item)
        else:
            other_bucket.append(item)

    result = []
    for p in PLATFORMS:
        items = sorted(by_platform[p], key=lambda x: x["点赞"], reverse=True)[:10]
        result.append({"platform": p, "items": items, "total": len(by_platform[p])})

    return {
        "date": date,
        "sheet_id": sheet_id,
        "platforms": result,
        "summary": {
            "total_rows": len(rows),
            "by_platform_count": {p: len(by_platform[p]) for p in PLATFORMS},
            "other_count": len(other_bucket),
        },
    }


def _to_int(v) -> int:
    try:
        if v is None or v == "":
            return 0
        return int(float(v))
    except (ValueError, TypeError):
        return 0
