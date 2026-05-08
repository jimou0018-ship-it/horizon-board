"""往运行中的本地服务塞一批示例数据，方便预览看板。"""
import httpx
from datetime import datetime, timedelta
import random

BASE = "http://localhost:8000"

c = httpx.Client(base_url=BASE)
sheets = c.get("/api/sheets").json()
print("Sheets:", [s["name"] for s in sheets])

PLATFORMS = ["抖音", "小红书", "B站", "快手"]
yesterday = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
today = datetime.now().date().strftime("%Y-%m-%d")

samples_yindao = [
    ("舞台名场面｜街舞battle高燃合集", "抖音", 2_300_000, 580),
    ("国风舞蹈《长安》全网热议",       "抖音", 1_580_000, 320),
    ("00后女团出道舞台直拍",           "抖音", 980_000, 210),
    ("男团回归舞台4K直拍",             "抖音", 720_000, 140),
    ("演唱会名场面｜歌迷大合唱",       "小红书", 152_000, 88),
    ("Tiktok热门舞蹈分解教学",         "小红书", 98_000, 67),
    ("跳舞穿搭分享｜显瘦显高",         "小红书", 64_000, 42),
    ("音乐剧《XXX》二刷打卡",          "B站", 320_000, 28),
    ("二次元宅舞翻跳合集",             "B站", 250_000, 56),
    ("乐器演奏神级翻奏",               "B站", 180_000, 33),
    ("土味广场舞挑战",                 "快手", 88_000, 45),
    ("家乡民俗舞蹈展示",               "快手", 56_000, 22),
]
samples_zongyi = [
    ("某综艺重磅嘉宾官宣",             "抖音", 1_900_000, 410),
    ("第二季首播预告 30s 名场面",      "抖音", 1_400_000, 305),
    ("综艺名场面剪辑｜嘉宾互动",       "抖音", 980_000, 220),
    ("选秀复盘｜这一季的最优解",       "小红书", 120_000, 75),
    ("追星实时打卡：录制现场偶遇",     "小红书", 88_000, 58),
    ("综艺二创｜逐字稿+配字幕",        "B站", 410_000, 42),
    ("吐槽大会：本周最炸名场面",       "B站", 290_000, 35),
    ("素人选手家乡 vlog",              "快手", 67_000, 28),
]

def insert(sheet_id, rows):
    for name, plat, likes, vids in rows:
        c.post(
            f"/api/sheets/{sheet_id}/rows",
            json={"data": {
                "热点名称": name,
                "日期": yesterday,
                "平台": plat,
                "点赞": likes,
                "相关视频数量": vids,
                "URL": f"https://example.com/{random.randint(10000,99999)}",
            }},
        )

# 找到对应 sheet
for s in sheets:
    if s["name"] == "音舞热点":
        insert(s["id"], samples_yindao)
    if s["name"] == "综艺热点":
        insert(s["id"], samples_zongyi)

# 也加几条今天的，让筛选今日时也有内容
extra = [
    ("【今日】实时热搜 TOP1", "抖音", 1_100_000, 188),
    ("【今日】小红书种草爆文", "小红书", 78_000, 31),
]
insert(sheets[0]["id"], [(n.replace("【今日】", ""), p, l, v) for n, p, l, v in extra])

print(f"已插入示例数据，日期：{yesterday}（昨日）")
