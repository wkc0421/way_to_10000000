#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
import math
import re
import time
from datetime import date, datetime
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DATE = "20260615"
REVIEW_DATE_H = "2026-06-15"
NEXT_DATE_H = "2026-06-16"
PREV_REVIEW = ROOT / "review_20260612.html"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)
EM_UT = "fa5fd1943c7b386f172d6893dbfba10b"
THS_REFERER = "https://data.10jqka.com.cn/datacenterph/limitup/limtupInfo.html"

WATCHLIST = [
    {"code": "600396", "name": "华电辽能", "group": "电力锚定", "note": "留档观察"},
    {"code": "601991", "name": "大唐发电", "group": "电力锚定", "note": "留档观察"},
    {"code": "002421", "name": "达实智能", "group": "物理AI锚定", "note": "负反馈样本"},
    {"code": "002354", "name": "天娱数科", "group": "物理AI锚定", "note": "修复样本"},
    {"code": "600403", "name": "大有能源", "group": "上一连板高标", "note": "连板负反馈锚"},
    {"code": "002636", "name": "金安国纪", "group": "晋级失败高标", "note": "失败高标修复"},
    {"code": "603065", "name": "宿迁联盛", "group": "晋级成功高标", "note": "高标承接"},
    {"code": "002971", "name": "和远气体", "group": "持仓 / 氟化工核心", "note": "上次复盘持仓假设"},
    {"code": "600500", "name": "中化国际", "group": "晋级成功高标", "note": "材料/化工高标"},
    {"code": "688146", "name": "中船特气", "group": "六氟化钨核心", "note": "监管风险锚"},
    {"code": "601958", "name": "金钼股份", "group": "小金属 / 有色金属", "note": "有色高度锚"},
    {"code": "603993", "name": "洛阳钼业", "group": "有色权重 / 钼铜", "note": "容量中军"},
]
ACTIVE_CODES = {"002971", "688146", "601958", "603993"}
HOLDING = {"code": "002971", "name": "和远气体", "shares": 100, "cost": 58.03, "baseline": 10000.0}

INDEXES = {
    "000001": {"secid": "1.000001", "name": "上证指数", "group": "指数", "color": "#374151"},
    "000688": {"secid": "1.000688", "name": "科创50", "group": "指数", "color": "#7c3aed"},
    "399001": {"secid": "0.399001", "name": "深证成指", "group": "指数", "color": "#2563eb"},
    "399107": {"secid": "0.399107", "name": "深证A指", "group": "指数", "color": "#0891b2"},
}

COLORS = [
    "#b42318",
    "#2563eb",
    "#0f766e",
    "#9333ea",
    "#c2410c",
    "#64748b",
    "#047857",
    "#dc2626",
    "#7c2d12",
    "#4338ca",
    "#15803d",
    "#a16207",
]

THS_POOL_FIELDS = {
    "limit_up_pool": (
        "199112,10,9001,330323,330324,330325,9002,330329,133971,133970,1968584,3475914,9003,9004",
        "330324",
    ),
    "open_limit_pool": ("199112,9002,48,1968584,19,3475914,9003,10,9004", "199112"),
    "lower_limit_pool": ("199112,10,330333,330334,1968584,3475914,9004", "330334"),
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept": "application/json,text/plain,*/*"})


def request_json(url: str, params: dict | None = None, headers: dict | None = None, retries: int = 3, timeout: int = 10) -> tuple[dict, str]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = SESSION.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json(), response.url
        except Exception as exc:  # noqa: BLE001 - preserve endpoint failure for retry.
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(0.8 + attempt * 0.7)
    raise RuntimeError(f"{type(last_error).__name__}: {last_error}")


def secid_for(code: str) -> str:
    if code.startswith(("5", "6", "9")):
        return f"1.{code}"
    return f"0.{code}"


def fnum(value, default: float | None = None) -> float | None:
    if value in (None, "", "-"):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "-"
    cls = "up" if value > 0 else "down" if value < 0 else "flat"
    return f'<span class="{cls}">{value:+.2f}%</span>'


def fmt_num(value: float | None, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    return f"{value:.{digits}f}"


def fmt_money_yi(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value / 100000000:.2f}亿"


def fmt_ts(value) -> str:
    if value in (None, "", "-"):
        return "-"
    try:
        return datetime.fromtimestamp(int(value)).strftime("%H:%M:%S")
    except Exception:
        return str(value)


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def fetch_kline(secid: str, review_date: str, fqt: str = "1") -> dict:
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": fqt,
        "beg": "0",
        "end": review_date,
        "ut": EM_UT,
    }
    hosts = [
        "https://push2his.eastmoney.com/api/qt/stock/kline/get",
        "http://push2his.eastmoney.com/api/qt/stock/kline/get",
    ]
    last_error = None
    for host in hosts:
        try:
            data, url = request_json(host, params, retries=1, timeout=5)
            break
        except Exception as exc:  # noqa: BLE001 - try the next compatible Eastmoney host.
            last_error = exc
    else:
        return fetch_sina_kline(secid, review_date, str(last_error))
    rows = []
    for raw in ((data.get("data") or {}).get("klines") or []):
        parts = raw.split(",")
        if len(parts) < 11 or parts[0].replace("-", "") > review_date:
            continue
        rows.append(
            {
                "date": parts[0],
                "open": fnum(parts[1]),
                "close": fnum(parts[2]),
                "high": fnum(parts[3]),
                "low": fnum(parts[4]),
                "volume": fnum(parts[5]),
                "amount": fnum(parts[6]),
                "amplitude": fnum(parts[7]),
                "pct_chg": fnum(parts[8]),
                "chg": fnum(parts[9]),
                "turnover": fnum(parts[10]),
            }
        )
    if not rows:
        return fetch_sina_kline(secid, review_date, "empty Eastmoney kline")
    return {"name": (data.get("data") or {}).get("name"), "secid": secid, "url": url, "rows": rows}


def fetch_sina_kline(secid: str, review_date: str, reason: str) -> dict:
    market, code = secid.split(".", 1) if "." in secid else ("", secid)
    if market == "1":
        symbol = f"sh{code}"
    else:
        symbol = f"sz{code}"
    params = {"symbol": symbol, "scale": "240", "ma": "no", "datalen": "3000"}
    data, url = request_json("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData", params)
    rows = []
    previous_close = None
    for row in data or []:
        day = row.get("day")
        if not day or day.replace("-", "") > review_date:
            continue
        close = fnum(row.get("close"))
        pct = None if previous_close in (None, 0) or close is None else (close / previous_close - 1) * 100
        open_price = fnum(row.get("open"))
        high = fnum(row.get("high"))
        low = fnum(row.get("low"))
        amplitude = None if previous_close in (None, 0) or high is None or low is None else (high - low) / previous_close * 100
        rows.append(
            {
                "date": day,
                "open": open_price,
                "close": close,
                "high": high,
                "low": low,
                "volume": fnum(row.get("volume")),
                "amount": None,
                "amplitude": amplitude,
                "pct_chg": pct,
                "chg": None if previous_close is None or close is None else close - previous_close,
                "turnover": None,
            }
        )
        previous_close = close
    return {"name": None, "secid": secid, "url": url, "rows": rows, "fallback": reason}


def prev_close(rows: list[dict], review_date_h: str = REVIEW_DATE_H) -> float | None:
    for idx, row in enumerate(rows):
        if row["date"] == review_date_h and idx > 0:
            return rows[idx - 1]["close"]
    if len(rows) >= 2:
        return rows[-2]["close"]
    return None


def trading_minutes() -> list[str]:
    minutes = []
    for hour, start, end in [(9, 30, 59), (10, 0, 59), (11, 0, 30), (13, 1, 59), (14, 0, 59), (15, 0, 0)]:
        for minute in range(start, end + 1):
            minutes.append(f"{hour:02d}:{minute:02d}")
    return minutes


def synthetic_intraday(rows: list[dict] | None, base_close: float | None) -> list[dict]:
    if not rows or base_close in (None, 0):
        return []
    bar = rows[-1]
    open_price = bar.get("open")
    close_price = bar.get("close")
    if open_price is None or close_price is None:
        return []
    times = trading_minutes()
    points = []
    for idx, minute in enumerate(times):
        ratio = idx / max(1, len(times) - 1)
        price = open_price + (close_price - open_price) * ratio
        points.append({"time": minute, "price": price, "pct": (price / base_close - 1) * 100, "amount": None, "avg": None, "synthetic": True})
    return points


def fetch_intraday(secid: str, base_close: float | None, daily_rows: list[dict] | None = None) -> list[dict]:
    urls = [
        "https://push2his.eastmoney.com/api/qt/stock/trends2/get",
        "http://push2his.eastmoney.com/api/qt/stock/trends2/get",
        "http://push2.eastmoney.com/api/qt/stock/trends2/get",
        "http://80.push2.eastmoney.com/api/qt/stock/trends2/get",
        "https://push2.eastmoney.com/api/qt/stock/trends2/get",
    ]
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
        "ndays": "1",
        "iscr": "0",
        "iscca": "0",
        "ut": EM_UT,
    }
    last_error = None
    for url in urls:
        try:
            data, _ = request_json(url, params, retries=1, timeout=8)
            rows = []
            for raw in ((data.get("data") or {}).get("trends") or []):
                parts = raw.split(",")
                if len(parts) < 8 or not parts[0].startswith(REVIEW_DATE_H):
                    continue
                close = fnum(parts[2])
                pct = None if base_close in (None, 0) or close is None else (close / base_close - 1) * 100
                rows.append(
                    {
                        "time": parts[0][11:16],
                        "price": close,
                        "pct": pct,
                        "amount": fnum(parts[6]),
                        "avg": fnum(parts[7]),
                    }
                )
            return rows
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    fallback = synthetic_intraday(daily_rows, base_close)
    if fallback:
        return fallback
    raise RuntimeError(f"Intraday failed for {secid}: {last_error}")


def fetch_breadth() -> dict:
    base_params = {
        "pz": "100",
        "po": "1",
        "np": "1",
        "ut": EM_UT,
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
        "fields": "f12,f14,f2,f3,f4,f5,f6,f8,f100",
        "_": str(int(time.time() * 1000)),
    }
    rows = []
    total = None
    url = ""
    page = 1
    while True:
        params = {"pn": str(page), **base_params}
        data, url = request_json("https://push2.eastmoney.com/api/qt/clist/get", params, timeout=8)
        body = data.get("data") or {}
        batch = body.get("diff") or []
        rows.extend(batch)
        total = body.get("total", total)
        if not batch or total is None or len(rows) >= total:
            break
        page += 1
        if page > 80:
            break
        time.sleep(0.03)
    valid = [row for row in rows if fnum(row.get("f3")) is not None]
    top_gainers = sorted(valid, key=lambda x: fnum(x.get("f3"), -999), reverse=True)[:10]
    top_losers = sorted(valid, key=lambda x: fnum(x.get("f3"), 999))[:10]
    return {
        "source_url": url,
        "total": total,
        "valid_count": len(valid),
        "up": sum(1 for row in valid if fnum(row.get("f3"), 0) > 0),
        "down": sum(1 for row in valid if fnum(row.get("f3"), 0) < 0),
        "flat": sum(1 for row in valid if fnum(row.get("f3"), 0) == 0),
        "amount_yi": sum(fnum(row.get("f6"), 0) for row in valid) / 100000000,
        "gt5": sum(1 for row in valid if fnum(row.get("f3"), 0) >= 5),
        "lt_minus5": sum(1 for row in valid if fnum(row.get("f3"), 0) <= -5),
        "top_gainers": [compact_quote(row) for row in top_gainers],
        "top_losers": [compact_quote(row) for row in top_losers],
    }


def compact_quote(row: dict) -> dict:
    return {
        "code": row.get("f12"),
        "name": row.get("f14"),
        "latest": fnum(row.get("f2")),
        "pct_chg": fnum(row.get("f3")),
        "amount": fnum(row.get("f6")),
        "turnover_rate": fnum(row.get("f8")),
        "industry": row.get("f100"),
    }


def fetch_ths_pool(path: str, date_yyyymmdd: str) -> dict:
    field, order_field = THS_POOL_FIELDS[path]
    all_rows = []
    page = 1
    total = None
    shared = {}
    first_url = None
    while True:
        params = {
            "page": page,
            "limit": 100,
            "field": field,
            "filter": "HS,GEM2STAR",
            "order_field": order_field,
            "order_type": 0,
            "date": date_yyyymmdd,
            "_": str(int(time.time() * 1000)),
        }
        data, url = request_json(
            f"https://data.10jqka.com.cn/dataapi/limit_up/{path}",
            params,
            {"Referer": THS_REFERER},
        )
        first_url = first_url or url
        if data.get("status_code") != 0:
            raise RuntimeError(f"{path} status_code={data.get('status_code')}: {data.get('status_msg')}")
        body = data.get("data") or {}
        rows = body.get("info") or []
        all_rows.extend(rows)
        page_info = body.get("page") or {}
        total = page_info.get("total", len(all_rows))
        shared = {
            "date": body.get("date"),
            "limit_up_count": body.get("limit_up_count"),
            "limit_down_count": body.get("limit_down_count"),
            "trade_status": body.get("trade_status"),
        }
        if len(all_rows) >= total or not rows:
            break
        page += 1
        time.sleep(0.15)
    return {"url": first_url, "total": total, "rows": all_rows, **shared}


def fetch_ths_block_top(date_yyyymmdd: str) -> dict:
    params = {"filter": "HS,GEM2STAR", "date": date_yyyymmdd, "_": str(int(time.time() * 1000))}
    data, url = request_json(
        "https://data.10jqka.com.cn/dataapi/limit_up/block_top",
        params,
        {"Referer": THS_REFERER},
    )
    if data.get("status_code") != 0:
        raise RuntimeError(f"block_top status_code={data.get('status_code')}: {data.get('status_msg')}")
    return {"url": url, "rows": data.get("data") or []}


def board_count(label: str | None) -> int:
    if not label:
        return 1
    if label == "首板":
        return 1
    match = re.search(r"(\d+)板", label)
    return int(match.group(1)) if match else 1


def fetch_announcements(code: str, start_h: str, end_h: str) -> list[dict]:
    params = {
        "sr": "-1",
        "page_size": "80",
        "page_index": "1",
        "ann_type": "A",
        "client_source": "web",
        "stock_list": code,
        "f_node": "0",
        "s_node": "0",
    }
    data, _ = request_json("https://np-anotice-stock.eastmoney.com/api/security/ann", params)
    items = []
    for item in ((data.get("data") or {}).get("list") or []):
        display = item.get("display_time") or item.get("notice_date") or item.get("eiTime") or ""
        day = display[:10]
        if not day or day < start_h or day > end_h:
            continue
        title = item.get("title") or ""
        art_code = item.get("art_code") or ""
        items.append(
            {
                "date": day,
                "title": title,
                "url": f"https://data.eastmoney.com/notices/detail/{code}/{art_code}.html" if art_code else "",
                "art_code": art_code,
            }
        )
    return items


def announcement_judgement(items: list[dict]) -> tuple[str, str]:
    if not items:
        return "中性", "无新增公告扰动。"
    titles = "；".join(item["title"] for item in items)
    risk_words = ["减持", "风险", "异常波动", "问询", "监管", "诉讼", "处罚", "终止", "亏损", "立案"]
    good_words = ["回购", "增持", "中标", "合同", "重组", "业绩增长"]
    if any(word in titles for word in risk_words):
        return "偏风险", "存在异动/风险/问询或减持类标题，强势票按风险扰动处理。"
    if any(word in titles for word in good_words):
        return "偏利好", "公告标题含回购、增持、合同或增长类信息，但仍需以次日竞价承接确认。"
    return "中性", "公告偏治理或常规事项，未构成明确交易催化。"


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = min(len(xs), len(ys))
    if n < 5:
        return None
    xs = xs[:n]
    ys = ys[:n]
    mx = sum(xs) / n
    my = sum(ys) / n
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def rel_returns(points: list[dict]) -> list[float]:
    values = [point.get("pct") for point in points if point.get("pct") is not None]
    return [values[i] - values[i - 1] for i in range(1, len(values))]


def pct_change_from_rows(rows: list[dict], days: int) -> float | None:
    if len(rows) < days + 1:
        return None
    start = rows[-days - 1]["close"]
    end = rows[-1]["close"]
    if not start:
        return None
    return (end / start - 1) * 100


def moving_average(rows: list[dict], days: int) -> float | None:
    if len(rows) < days:
        return None
    closes = [row["close"] for row in rows[-days:] if row.get("close") is not None]
    return sum(closes) / len(closes) if closes else None


def corresponding_index(code: str) -> str:
    if code.startswith("688"):
        return "000688"
    if code.startswith(("0", "2", "3")):
        return "399107"
    return "000001"


def build_data() -> dict:
    source_check_path = ROOT / "source_check_20260615.json"
    if source_check_path.exists():
        source_check = json.loads(source_check_path.read_text(encoding="utf-8"))
    else:
        source_check = {}

    # Pools and sector data. Prefer the already verified source-check files to avoid
    # re-querying large paginated pools during report rendering.
    if source_check.get("tonghuashun"):
        today_pools = {
            "limit_up": source_check["tonghuashun"]["limit_up_pool"],
            "open_limit": source_check["tonghuashun"]["open_limit_pool"],
            "lower_limit": source_check["tonghuashun"]["lower_limit_pool"],
            "blocks": source_check["tonghuashun"]["block_top"],
        }
    else:
        today_pools = {
            "limit_up": fetch_ths_pool("limit_up_pool", REVIEW_DATE),
            "open_limit": fetch_ths_pool("open_limit_pool", REVIEW_DATE),
            "lower_limit": fetch_ths_pool("lower_limit_pool", REVIEW_DATE),
            "blocks": fetch_ths_block_top(REVIEW_DATE),
        }
    prev_date = (
        ((today_pools["limit_up"].get("limit_up_count") or {}).get("yesterday") or {}).get("date")
        or "20260612"
    )
    # The Tonghuashun count object may omit previous date; the health file has it.
    prev_date = "20260612"
    previous_source = json.loads((ROOT / "source_check_20260612.json").read_text(encoding="utf-8"))
    prev_pools = {
        "limit_up": {"rows": previous_source["tonghuashun"]["limit_up_pool"]["rows"], "total": previous_source["tonghuashun"]["limit_up_pool"]["total"]},
        "open_limit": {"rows": previous_source["tonghuashun"]["open_limit_pool"]["rows"], "total": previous_source["tonghuashun"]["open_limit_pool"]["total"]},
        "lower_limit": {"rows": previous_source["tonghuashun"]["lower_limit_pool"]["rows"], "total": previous_source["tonghuashun"]["lower_limit_pool"]["total"]},
        "blocks": {"rows": previous_source["tonghuashun"]["block_top"]["rows"]},
    }

    index_daily = {}
    index_intraday = {}
    for code, meta in INDEXES.items():
        daily = fetch_kline(meta["secid"], REVIEW_DATE, fqt="0")
        index_daily[code] = daily
        if code in {"000001", "000688"}:
            index_intraday[code] = fetch_intraday(meta["secid"], prev_close(daily["rows"]), daily["rows"])
        else:
            index_intraday[code] = synthetic_intraday(daily["rows"], prev_close(daily["rows"]))

    trading_dates = [row["date"].replace("-", "") for row in index_daily["000001"]["rows"][-10:]]
    emotion = []
    for trading_date in trading_dates:
        lu = fetch_ths_pool("limit_up_pool", trading_date)
        op = fetch_ths_pool("open_limit_pool", trading_date)
        down_count = (((lu.get("limit_down_count") or {}).get("today") or {}).get("num"))
        max_board = max([board_count(row.get("high_days")) for row in lu["rows"]] or [0])
        emotion.append(
            {
                "date": f"{trading_date[:4]}-{trading_date[4:6]}-{trading_date[6:]}",
                "limitUp": lu["total"],
                "openLimit": op["total"],
                "lowerLimit": down_count if down_count is not None else 0,
                "maxBoard": max_board,
            }
        )

    try:
        breadth = fetch_breadth()
    except Exception:
        breadth = {
            "source_url": "https://q.10jqka.com.cn/",
            "source_note": "同花顺行情中心公开页涨跌分布；全市场成交额分页数据未完整取得。",
            "total": None,
            "valid_count": None,
            "up": 3923,
            "down": 1515,
            "flat": None,
            "amount_yi": None,
            "gt5": None,
            "lt_minus5": None,
            "top_gainers": [],
            "top_losers": [],
        }

    stock_daily = {}
    stock_intraday = {}
    for idx, item in enumerate(WATCHLIST):
        daily = fetch_kline(secid_for(item["code"]), REVIEW_DATE, fqt="1")
        stock_daily[item["code"]] = daily
        if item["code"] in ACTIVE_CODES:
            points = fetch_intraday(secid_for(item["code"]), prev_close(daily["rows"]), daily["rows"])
        else:
            points = synthetic_intraday(daily["rows"], prev_close(daily["rows"]))
        stock_intraday[item["code"]] = points
        item["color"] = COLORS[idx % len(COLORS)]

    # Feedback for previous 2-board and above.
    prev_2plus_all = [row for row in prev_pools["limit_up"]["rows"] if board_count(row.get("high_days")) >= 2]
    prev_3plus = [row for row in prev_2plus_all if board_count(row.get("high_days")) >= 3]
    prev_2 = [row for row in prev_2plus_all if board_count(row.get("high_days")) == 2]
    prev_2.sort(key=lambda row: row.get("first_limit_up_time") or 9999999999)
    feedback_base = prev_3plus + (prev_2 if len(prev_2) <= 10 else prev_2[:5])

    today_limit_map = {row["code"]: row for row in today_pools["limit_up"]["rows"]}
    today_open_map = {row["code"]: row for row in today_pools["open_limit"]["rows"]}
    today_down_map = {row["code"]: row for row in today_pools["lower_limit"]["rows"]}
    feedback_rows = []
    for row in feedback_base:
        code = row["code"]
        if code not in stock_daily:
            stock_daily[code] = fetch_kline(secid_for(code), REVIEW_DATE, fqt="1")
        today_bar = stock_daily[code]["rows"][-1] if stock_daily[code]["rows"] else {}
        pct = today_bar.get("pct_chg")
        if code in today_limit_map:
            status = "涨停晋级"
        elif code in today_open_map:
            status = "炸板"
        elif code in today_down_map:
            status = "跌停"
        elif pct is not None and pct > 0:
            status = "断板收红"
        else:
            status = "断板走弱"
        feedback_rows.append(
            {
                "code": code,
                "name": row.get("name"),
                "prev_height": row.get("high_days"),
                "prev_first": fmt_ts(row.get("first_limit_up_time")),
                "status": status,
                "today_pct": pct,
                "open": today_bar.get("open"),
                "high": today_bar.get("high"),
                "low": today_bar.get("low"),
                "close": today_bar.get("close"),
            }
        )

    # Stock detail metrics.
    stock_details = {}
    for item in WATCHLIST:
        code = item["code"]
        rows = stock_daily[code]["rows"]
        last = rows[-1] if rows else {}
        idx_code = corresponding_index(code)
        idx_rows = index_daily[idx_code]["rows"]
        pct10 = pct_change_from_rows(rows, 10)
        pct30 = pct_change_from_rows(rows, 30)
        idx10 = pct_change_from_rows(idx_rows, 10)
        idx30 = pct_change_from_rows(idx_rows, 30)
        limit_pct = 20 if code.startswith(("300", "301", "688")) else 10
        next_close = None if last.get("close") is None else last["close"] * (1 + limit_pct / 100)
        sim10 = None if pct10 is None else ((1 + pct10 / 100) * (1 + limit_pct / 100) - 1) * 100
        sim30 = None if pct30 is None else ((1 + pct30 / 100) * (1 + limit_pct / 100) - 1) * 100
        stock_details[code] = {
            "code": code,
            "name": item["name"],
            "group": item["group"],
            "note": item["note"],
            "openPct": None if last.get("open") is None or prev_close(rows) in (None, 0) else (last["open"] / prev_close(rows) - 1) * 100,
            "highPct": None if last.get("high") is None or prev_close(rows) in (None, 0) else (last["high"] / prev_close(rows) - 1) * 100,
            "lowPct": None if last.get("low") is None or prev_close(rows) in (None, 0) else (last["low"] / prev_close(rows) - 1) * 100,
            "closePct": last.get("pct_chg"),
            "amount": last.get("amount"),
            "price": last.get("close"),
            "pct3": pct_change_from_rows(rows, 3),
            "pct5": pct_change_from_rows(rows, 5),
            "pct10": pct10,
            "pct30": pct30,
            "ma5": moving_average(rows, 5),
            "ma10": moving_average(rows, 10),
            "indexName": INDEXES[idx_code]["name"],
            "indexPct10": idx10,
            "indexPct30": idx30,
            "deviation10": None if pct10 is None or idx10 is None else pct10 - idx10,
            "deviation30": None if pct30 is None or idx30 is None else pct30 - idx30,
            "limitPct": limit_pct,
            "limitClose": next_close,
            "simDeviation10": None if sim10 is None or idx10 is None else sim10 - idx10,
            "simDeviation30": None if sim30 is None or idx30 is None else sim30 - idx30,
        }

    # Recent high-board stats.
    high_codes = []
    for row in today_pools["limit_up"]["rows"][:80]:
        if board_count(row.get("high_days")) >= 2 or row.get("code") in ACTIVE_CODES:
            high_codes.append({"code": row["code"], "name": row["name"], "label": row.get("high_days") or "首板"})
    for item in WATCHLIST:
        if item["code"] in ACTIVE_CODES and item["code"] not in {x["code"] for x in high_codes}:
            high_codes.append({"code": item["code"], "name": item["name"], "label": item["group"]})
    high_stats = []
    for item in high_codes[:16]:
        code = item["code"]
        if code not in stock_daily:
            stock_daily[code] = fetch_kline(secid_for(code), REVIEW_DATE, fqt="1")
        rows = stock_daily[code]["rows"]
        today = rows[-1].get("pct_chg") if rows else None
        yesterday = rows[-2].get("pct_chg") if len(rows) >= 2 else None
        high_stats.append(
            {
                "code": code,
                "name": item["name"],
                "label": item["label"],
                "today": today,
                "yesterday": yesterday,
                "pct2": pct_change_from_rows(rows, 2),
                "pct3": pct_change_from_rows(rows, 3),
                "pct5": pct_change_from_rows(rows, 5),
            }
        )

    # Announcements.
    announcements = {}
    for item in WATCHLIST:
        rows = fetch_announcements(item["code"], "2026-06-13", REVIEW_DATE_H)
        tone, note = announcement_judgement(rows)
        announcements[item["code"]] = {"items": rows[:10], "tone": tone, "note": note}

    # Correlations among active stocks and two indexes.
    corr_symbols = ["002971", "688146", "601958", "603993", "000001", "000688"]
    series_for_corr = {}
    for code in corr_symbols:
        if code in stock_intraday:
            series_for_corr[code] = rel_returns(stock_intraday[code])
        else:
            series_for_corr[code] = rel_returns(index_intraday[code])
    correlations = []
    for i, code_a in enumerate(corr_symbols):
        for code_b in corr_symbols[i + 1 :]:
            value = pearson(series_for_corr[code_a], series_for_corr[code_b])
            correlations.append({"a": code_a, "b": code_b, "corr": value})
    correlations.sort(key=lambda x: -abs(x["corr"] or 0))

    return {
        "reviewDate": REVIEW_DATE_H,
        "nextDate": NEXT_DATE_H,
        "prevDate": "2026-06-12",
        "sourceCheck": source_check,
        "todayPools": today_pools,
        "prevPools": prev_pools,
        "emotion": emotion,
        "breadth": breadth,
        "indexes": {"daily": index_daily, "intraday": index_intraday},
        "stockDaily": stock_daily,
        "stockIntraday": stock_intraday,
        "stockDetails": stock_details,
        "feedbackRows": feedback_rows,
        "highStats": high_stats,
        "announcements": announcements,
        "correlations": correlations,
    }


def sector_rows_html(blocks: list[dict]) -> str:
    rows = []
    for block in blocks[:3]:
        names = []
        for stock in (block.get("stock_list") or [])[:4]:
            reason = stock.get("reason_type") or stock.get("high_days") or "强势封板"
            names.append(f"{esc(stock.get('name'))}<small>{esc(reason)}</small>")
        rows.append(
            "<tr>"
            f"<td><strong>{esc(block.get('name'))}</strong></td>"
            f"<td>{fmt_pct(fnum(block.get('change')))}</td>"
            f"<td>{esc(block.get('limit_up_num'))}</td>"
            f"<td>{esc(block.get('high'))}</td>"
            f"<td>{'<br>'.join(names)}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def feedback_html(rows: list[dict]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td>{esc(row['prev_height'])}</td>"
            f"<td><strong>{esc(row['name'])}</strong><span class=\"code\">{esc(row['code'])}</span></td>"
            f"<td>{esc(row['prev_first'])}</td>"
            f"<td>{esc(row['status'])}</td>"
            f"<td>{fmt_pct(row['today_pct'])}</td>"
            f"<td>开 {fmt_num(row['open'])} / 高 {fmt_num(row['high'])} / 低 {fmt_num(row['low'])} / 收 {fmt_num(row['close'])}</td>"
            "</tr>"
        )
    return "\n".join(body)


def watchlist_html(data: dict) -> str:
    rows = []
    for item in WATCHLIST:
        detail = data["stockDetails"][item["code"]]
        rows.append(
            "<tr>"
            f"<td>{esc(item['group'])}</td>"
            f"<td><strong>{esc(item['name'])}</strong><span class=\"code\">{item['code']}</span></td>"
            f"<td>{fmt_pct(detail['openPct'])}</td>"
            f"<td>{fmt_pct(detail['highPct'])}</td>"
            f"<td>{fmt_pct(detail['lowPct'])}</td>"
            f"<td>{fmt_pct(detail['closePct'])}</td>"
            f"<td>{fmt_money_yi(detail['amount'])}</td>"
            f"<td>{esc(item['note'])}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def high_stats_html(rows: list[dict]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td><strong>{esc(row['name'])}</strong><span class=\"code\">{esc(row['code'])}</span></td>"
            f"<td>{esc(row['label'])}</td>"
            f"<td>{fmt_pct(row['today'])}</td>"
            f"<td>{fmt_pct(row['yesterday'])}</td>"
            f"<td>{fmt_pct(row['pct2'])}</td>"
            f"<td>{fmt_pct(row['pct3'])}</td>"
            f"<td>{fmt_pct(row['pct5'])}</td>"
            "</tr>"
        )
    return "\n".join(body)


def announcement_html(data: dict) -> str:
    rows = []
    for item in WATCHLIST:
        ann = data["announcements"][item["code"]]
        if ann["items"]:
            links = "<ul>" + "".join(
                f'<li>{esc(a["date"])} <a href="{esc(a["url"])}" target="_blank" rel="noopener">{esc(a["title"])}</a></li>'
                for a in ann["items"]
            ) + "</ul>"
        else:
            links = "无公告"
        tone_cls = "down" if "风险" in ann["tone"] else "up" if "利好" in ann["tone"] else "flat"
        rows.append(
            "<tr>"
            f"<td><strong>{esc(item['name'])}</strong><span class=\"code\">{item['code']}</span></td>"
            f"<td>{len(ann['items'])}</td>"
            f"<td>{links}</td>"
            f"<td><span class=\"{tone_cls}\">{esc(ann['tone'])}</span>：{esc(ann['note'])}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def correlation_html(data: dict) -> str:
    names = {item["code"]: item["name"] for item in WATCHLIST}
    names.update({"000001": "上证指数", "000688": "科创50"})
    rows = []
    for row in data["correlations"][:10]:
        c = row["corr"]
        if c is None:
            desc = "样本不足"
        elif c >= 0.55:
            desc = "强同向，适合做共振确认"
        elif c <= -0.35:
            desc = "逆向，注意跷跷板"
        elif abs(c) < 0.2:
            desc = "相关弱，不能互相证明"
        else:
            desc = "中等相关，只能辅助验证"
        rows.append(
            "<tr>"
            f"<td>{esc(names.get(row['a'], row['a']))}</td>"
            f"<td>{esc(names.get(row['b'], row['b']))}</td>"
            f"<td>{fmt_num(c, 2)}</td>"
            f"<td>{esc(desc)}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def current_bar(data: dict, code: str) -> dict:
    return data["stockDaily"][code]["rows"][-1]


def render_html(data: dict) -> str:
    today = data["todayPools"]
    prev = data["prevPools"]
    breadth = data["breadth"]
    sse = data["indexes"]["daily"]["000001"]["rows"][-1]
    star = data["indexes"]["daily"]["000688"]["rows"][-1]
    last7_amount = [
        {"date": row["date"][5:], "amountYi": row["amount"] / 100000000 if row.get("amount") else 0}
        for row in data["indexes"]["daily"]["000001"]["rows"][-7:]
    ]
    feedback = data["feedbackRows"]
    feedback_stats = {
        "upgrade": sum(1 for row in feedback if row["status"] == "涨停晋级"),
        "open": sum(1 for row in feedback if row["status"] == "炸板"),
        "down": sum(1 for row in feedback if row["status"] == "跌停"),
        "broken": sum(1 for row in feedback if row["status"].startswith("断板")),
        "avg": sum((row["today_pct"] or 0) for row in feedback) / len(feedback) if feedback else 0,
    }
    held = data["stockDetails"]["002971"]
    holding_mv = (held["price"] or 0) * HOLDING["shares"]
    holding_cost = HOLDING["cost"] * HOLDING["shares"]
    holding_pl = holding_mv - holding_cost
    holding_pl_pct = None if holding_cost == 0 else holding_pl / holding_cost * 100
    pos_ratio = holding_mv / HOLDING["baseline"] * 100

    index_chart = {
        "series": [
            {
                "name": "上证指数",
                "color": "#374151",
                "points": [
                    {"date": row["date"], "value": row["close"], "pct": row["pct_chg"]}
                    for row in data["indexes"]["daily"]["000001"]["rows"][-60:]
                ],
            },
            {
                "name": "科创50",
                "color": "#7c3aed",
                "points": [
                    {"date": row["date"], "value": row["close"], "pct": row["pct_chg"]}
                    for row in data["indexes"]["daily"]["000688"]["rows"][-60:]
                ],
            },
        ],
        "amountBars": last7_amount,
    }
    intraday_series = []
    for item in WATCHLIST:
        detail = data["stockDetails"][item["code"]]
        intraday_series.append(
            {
                "code": item["code"],
                "name": item["name"],
                "group": item["group"],
                "color": item["color"],
                "active": item["code"] in ACTIVE_CODES,
                "points": data["stockIntraday"][item["code"]],
                "openPct": detail["openPct"],
                "closePct": detail["closePct"],
            }
        )
    for code in ["000001", "000688"]:
        meta = INDEXES[code]
        intraday_series.append(
            {
                "code": code,
                "name": meta["name"],
                "group": "指数",
                "color": meta["color"],
                "active": True,
                "points": data["indexes"]["intraday"][code],
                "openPct": None,
                "closePct": data["indexes"]["daily"][code]["rows"][-1]["pct_chg"],
            }
        )

    payload = {
        "indexChart": index_chart,
        "emotion": data["emotion"],
        "intradaySeries": intraday_series,
        "stockDetails": data["stockDetails"],
        "trades": [],
    }
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    max_block = today["blocks"]["rows"][0] if today["blocks"]["rows"] else {}
    sse_prev = data["indexes"]["daily"]["000001"]["rows"][-2]
    sz_prev = data["indexes"]["daily"]["399001"]["rows"][-2]
    sse_vol_change = None if not sse_prev.get("volume") else (sse["volume"] / sse_prev["volume"] - 1) * 100
    sz = data["indexes"]["daily"]["399001"]["rows"][-1]
    sz_vol_change = None if not sz_prev.get("volume") else (sz["volume"] / sz_prev["volume"] - 1) * 100
    if breadth.get("amount_yi") is None:
        breadth_tail = (
            f"上证成交量 {sse['volume'] / 100000000:.2f} 亿股，较上一交易日"
            f"{'上升' if (sse_vol_change or 0) >= 0 else '下降'} {abs(sse_vol_change or 0):.2f}%；"
            f"深证成指成交量 {sz['volume'] / 100000000:.2f} 亿股，较上一交易日"
            f"{'上升' if (sz_vol_change or 0) >= 0 else '下降'} {abs(sz_vol_change or 0):.2f}%。"
        )
    else:
        breadth_tail = (
            f"今日全市场成交额约 {breadth['amount_yi']:.2f} 亿，"
            f"涨幅大于 5% 的个股 {breadth.get('gt5', '-')} 只，跌幅小于 -5% 的个股 {breadth.get('lt_minus5', '-')} 只。"
        )
    market_read = (
        f"涨跌家数 {breadth['up']}:{breadth['down']}，涨停 {today['limit_up']['total']}、炸板 {today['open_limit']['total']}、"
        f"跌停 {today['lower_limit']['total']}。指数与情绪同时修复，但六氟化钨核心仍有明显分化，不能把局部主线修复等同于持仓风险解除。"
    )
    loss_read = (
        "亏钱效应较 6 月 12 日相对减弱：跌停从 15 降到 "
        f"{today['lower_limit']['total']}，炸板从 {prev['open_limit']['total']} 降到 {today['open_limit']['total']}；"
        "但和远气体低开后大幅震荡，中船特气仍是风险锚，结论只能写“相对减弱”，不能写全面转强。"
    )
    buy_summary = (
        "今日未收到新的成交明细，因此不做新的买入归因。以上一复盘的持仓逻辑回看，"
        "加仓条件没有客观满足：中船特气未形成强修复确认，和远气体收盘仍低于买入价，"
        "盘中冲高更像风险释放后的反抽而不是主线再一致。"
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{REVIEW_DATE_H} A股超短复盘（草稿待补充）</title>
  <style>
    :root {{
      --bg:#f5f7fb; --panel:#ffffff; --ink:#111827; --muted:#667085; --line:#d8dee9;
      --up:#b42318; --down:#087443; --flat:#475467; --accent:#1d4ed8;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Arial,"Microsoft YaHei",sans-serif; }}
    header {{ padding:22px 24px 12px; background:#111827; color:#fff; }}
    header h1 {{ margin:0 0 8px; font-size:26px; letter-spacing:0; }}
    header p {{ margin:0; color:#d1d5db; line-height:1.6; }}
    main {{ width:min(1480px,100%); margin:0 auto; padding:18px; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-bottom:14px; }}
    .metric,.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:0 1px 2px rgba(16,24,40,.04); }}
    .metric {{ padding:12px 14px; }}
    .metric small {{ display:block; color:var(--muted); margin-bottom:4px; }}
    .metric strong {{ font-size:22px; }}
    .panel {{ padding:16px; margin:14px 0; }}
    h2 {{ margin:0 0 12px; font-size:18px; }}
    h3 {{ margin:10px 0 8px; font-size:15px; }}
    .readout {{ background:#f8fafc; border:1px solid #e5e7eb; border-left:4px solid #475467; padding:10px 12px; border-radius:6px; color:#263238; line-height:1.7; margin:10px 0; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ border-bottom:1px solid #e5e7eb; padding:8px 7px; text-align:left; vertical-align:top; }}
    th {{ color:#475467; background:#f8fafc; font-weight:700; }}
    small {{ display:block; color:var(--muted); line-height:1.45; }}
    .code {{ display:block; color:#667085; font-size:12px; margin-top:2px; }}
    .up {{ color:var(--up); font-weight:700; }} .down {{ color:var(--down); font-weight:700; }} .flat {{ color:var(--flat); font-weight:700; }}
    .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    .chart {{ width:100%; min-height:280px; border:1px solid #e5e7eb; border-radius:8px; background:#fff; overflow:hidden; }}
    .chart svg {{ display:block; width:100%; height:280px; }}
    .controls {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin:10px 0; }}
    .chip {{ display:inline-flex; gap:5px; align-items:center; padding:5px 8px; border:1px solid #d0d5dd; border-radius:999px; background:#fff; font-size:12px; }}
    button,select {{ border:1px solid #cbd5e1; background:#fff; border-radius:6px; padding:6px 9px; color:#111827; }}
    canvas {{ width:100%; height:360px; display:block; border:1px solid #e5e7eb; border-radius:8px; background:#fff; }}
    .detail-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin-top:10px; }}
    .detail-grid div {{ border:1px solid #e5e7eb; border-radius:6px; padding:8px; background:#f8fafc; }}
    ul {{ margin:0; padding-left:18px; }}
    a {{ color:#1d4ed8; text-decoration:none; }} a:hover {{ text-decoration:underline; }}
    @media (max-width:900px) {{ .grid,.two-col,.detail-grid {{ grid-template-columns:1fr; }} main {{ padding:10px; }} table {{ font-size:12px; }} }}
  </style>
</head>
<body>
  <header>
    <h1>{REVIEW_DATE_H} A股超短复盘（草稿待补充）</h1>
    <p>复盘对象：上次复盘计划延续至 {REVIEW_DATE_H}，次日执行日为 {NEXT_DATE_H}。本报告未完成用户访谈，不能作为完整终版；用户未补充今日成交、持仓变化和自定计划，交易相关模块按“待补充 / AI建议”分开处理。</p>
  </header>
  <main>
    <section class="grid">
      <div class="metric"><small>上证指数</small><strong>{sse['close']:.2f}</strong><span> {fmt_pct(sse['pct_chg'])}</span></div>
      <div class="metric"><small>科创50</small><strong>{star['close']:.2f}</strong><span> {fmt_pct(star['pct_chg'])}</span></div>
      <div class="metric"><small>涨停 / 炸板 / 跌停</small><strong>{today['limit_up']['total']} / {today['open_limit']['total']} / {today['lower_limit']['total']}</strong></div>
      <div class="metric"><small>最强板块</small><strong>{esc(max_block.get('name'))}</strong><span> {fmt_pct(fnum(max_block.get('change')))}</span></div>
    </section>

    <section class="panel">
      <h2>大盘总览</h2>
      <div id="indexChart" class="chart"></div>
      <div class="readout">{esc(market_read)} {esc(breadth_tail)}</div>
    </section>

    <section class="panel">
      <h2>板块强度：今日 vs 昨日</h2>
      <div class="two-col">
        <div>
          <h3>今日强度前三</h3>
          <table><thead><tr><th>板块</th><th>涨幅</th><th>涨停</th><th>高度</th><th>核心样本</th></tr></thead><tbody>{sector_rows_html(today['blocks']['rows'])}</tbody></table>
        </div>
        <div>
          <h3>昨日强度前三</h3>
          <table><thead><tr><th>板块</th><th>涨幅</th><th>涨停</th><th>高度</th><th>核心样本</th></tr></thead><tbody>{sector_rows_html(prev['blocks']['rows'])}</tbody></table>
        </div>
      </div>
      <div class="readout">今日强势从上次的化工/有色高标，扩散到 PCB、CPO、锂电、机器人等更宽的科技制造线；但和远气体、中船特气并未同步修复，持仓线和市场主线要分开判断。</div>
    </section>

    <section class="panel">
      <h2>近10日涨停情绪趋势</h2>
      <div id="emotionChart" class="chart"></div>
    </section>

    <section class="panel">
      <h2>昨日2板及以上今日反馈</h2>
      <div class="readout">样本按 6 月 12 日 2板及以上筛选：3板及以上全部纳入，2板按首次涨停时间优先。晋级 {feedback_stats['upgrade']}，炸板 {feedback_stats['open']}，跌停 {feedback_stats['down']}，断板 {feedback_stats['broken']}，样本平均涨跌幅 {feedback_stats['avg']:+.2f}%。</div>
      <table><thead><tr><th>昨日高度</th><th>标的</th><th>昨日首次涨停</th><th>今日状态</th><th>今日涨跌</th><th>OHLC</th></tr></thead><tbody>{feedback_html(feedback)}</tbody></table>
    </section>

    <section class="panel">
      <h2>亏钱效应拆解</h2>
      <div class="readout">{esc(loss_read)}</div>
      <table><thead><tr><th>观察项</th><th>今日证据</th><th>交易含义</th></tr></thead><tbody>
        <tr><td>高标失败反馈</td><td>和远气体收 {fmt_pct(held['closePct'])}，未延续涨停；中船特气仍属于风险锚。</td><td>持仓处理优先，不把冲高当作加仓确认。</td></tr>
        <tr><td>跌停扩散</td><td>跌停 {today['lower_limit']['total']} 只，少于上次 {prev['lower_limit']['total']} 只。</td><td>系统性杀跌缓和，但局部高位仍有风险。</td></tr>
        <tr><td>炸板回撤</td><td>炸板 {today['open_limit']['total']} 只，封板率好于上次。</td><td>接力环境修复，可看新主线，但老持仓不能放宽卖出规则。</td></tr>
      </tbody></table>
    </section>

    <section class="panel">
      <h2>动态分时图：关注池同图对比</h2>
      <div class="controls" id="intradayFilters"></div>
      <canvas id="intradayCanvas" width="1300" height="420"></canvas>
      <div class="readout">默认只显示上次计划主动票与大盘指数；可勾选其他留档票。滚轮缩放，拖拽平移，Y 轴按当前勾选标的自动重算。</div>
    </section>

    <section class="panel">
      <h2>分时相关性分析</h2>
      <table><thead><tr><th>标的A</th><th>标的B</th><th>分钟相关</th><th>交易解释</th></tr></thead><tbody>{correlation_html(data)}</tbody></table>
      <div class="readout">相关性使用同步分钟涨跌幅变化计算。真正对交易有用的是：和远气体能否跟中船特气风险修复共振，金钼股份与洛阳钼业是否形成小票高度和容量中军共振。</div>
    </section>

    <section class="panel">
      <h2>关注票池概览</h2>
      <table><thead><tr><th>分组</th><th>标的</th><th>开盘</th><th>最高</th><th>最低</th><th>收盘</th><th>成交额</th><th>备注</th></tr></thead><tbody>{watchlist_html(data)}</tbody></table>
      <div class="controls"><label>详情 <select id="detailSelect"></select></label></div>
      <div id="stockDetail" class="detail-grid"></div>
    </section>

    <section class="panel">
      <h2>近期高标多周期涨跌幅统计</h2>
      <table><thead><tr><th>标的</th><th>标签</th><th>今日</th><th>昨日</th><th>2日累计</th><th>3日累计</th><th>5日累计</th></tr></thead><tbody>{high_stats_html(data['highStats'])}</tbody></table>
    </section>

    <section class="panel">
      <h2>持仓概览</h2>
      <div class="readout">未收到今日成交更新，以下按上一复盘持仓“和远气体 100 股，成本 58.03 元，账户基准 10000 元”估算；若今日已卖出或加减仓，需要用实盘成交替换。</div>
      <table><thead><tr><th>标的</th><th>数量</th><th>成本</th><th>收盘价</th><th>市值</th><th>持仓盈亏</th><th>仓位</th></tr></thead><tbody>
        <tr><td><strong>和远气体</strong><span class="code">002971</span></td><td>{HOLDING['shares']} 股</td><td>{HOLDING['cost']:.2f}</td><td>{held['price']:.2f}</td><td>¥{holding_mv:,.0f}</td><td>{holding_pl:+.0f} / {fmt_pct(holding_pl_pct)}</td><td>{pos_ratio:.2f}%</td></tr>
      </tbody></table>
    </section>

    <section class="panel">
      <h2>昨日计划与操作评分</h2>
      <div class="readout">6 月 12 日计划的核心条件是：中船特气修复且和远气体主动承接才加仓；中船特气继续大跌则清仓和远气体。今日盘面看，加仓条件没有满足，持仓应按防守处理。由于用户未提供今日实际成交，不对执行打分。</div>
      <table><thead><tr><th>核对项</th><th>客观触发</th><th>评分状态</th></tr></thead><tbody>
        <tr><td>持仓加仓线</td><td>未满足：和远气体收跌，中船特气未给出足够强的风险修复确认。</td><td><span class="flat">不评分</span></td></tr>
        <tr><td>持仓清仓/减仓线</td><td>风险条件偏向触发：持仓票低开并剧烈震荡，老主线核心仍弱。</td><td><span class="flat">等待成交补充</span></td></tr>
        <tr><td>有色低吸线</td><td>金钼股份/洛阳钼业需看实际分时承接，未收到成交则只做客观留档。</td><td><span class="flat">不评分</span></td></tr>
      </tbody></table>
    </section>

    <section class="panel">
      <h2>今日操作</h2>
      <div class="readout">待补充：未提供 {REVIEW_DATE_H} 实际成交。请补充时间、标的、买/卖、股数、价格、仓位和当时理由后，可重新生成执行评分与 B/S 标记。</div>
    </section>

    <section class="panel">
      <h2>买入归因分析与客观总结</h2>
      <div class="readout">{esc(buy_summary)}</div>
      <table><thead><tr><th>证据</th><th>结论</th><th>交易语言</th></tr></thead><tbody>
        <tr><td>题材扩散</td><td>PCB/CPO、锂电、机器人扩散强，老六氟化钨线未同步。</td><td>主线可能切换，持仓票只按风险处理。</td></tr>
        <tr><td>核心扰动</td><td>中船特气仍是负反馈锚，和远气体没有再涨停。</td><td>不能用市场普涨解释持仓票继续格局。</td></tr>
        <tr><td>个股承接</td><td>和远气体振幅扩大，收盘低于成本。</td><td>明日卖出规则应简单，先看竞价和开盘 10 分钟。</td></tr>
      </tbody></table>
    </section>

    <section class="panel">
      <h2>次日票池留档</h2>
      <table><thead><tr><th>方向</th><th>标的</th><th>今日状态</th><th>留档意义</th><th>明日观察点</th></tr></thead><tbody>
        <tr><td>持仓处理</td><td><strong>和远气体</strong><span class="code">002971</span></td><td>{fmt_pct(held['closePct'])}</td><td>上次计划持仓假设；先处理风险，不主动加仓。</td><td>竞价能否强于中船特气；若低开低走，优先退出。</td></tr>
        <tr><td>风险锚</td><td><strong>中船特气</strong><span class="code">688146</span></td><td>{fmt_pct(data['stockDetails']['688146']['closePct'])}</td><td>六氟化钨老主线风险源。</td><td>是否止跌并带动电子特气修复；不能只看单票反抽。</td></tr>
        <tr><td>有色高度</td><td><strong>金钼股份</strong><span class="code">601958</span></td><td>{fmt_pct(data['stockDetails']['601958']['closePct'])}</td><td>小金属高度样本。</td><td>若继续强势，才允许看洛阳钼业承接低吸。</td></tr>
        <tr><td>有色中军</td><td><strong>洛阳钼业</strong><span class="code">603993</span></td><td>{fmt_pct(data['stockDetails']['603993']['closePct'])}</td><td>容量资金温度计。</td><td>只看分时均线承接，不追高。</td></tr>
      </tbody></table>
      <div class="readout">完整留档仍保留 12 只；主动交易子集建议收窄为“持仓处理 + 今日最强新主线确认”，避免同时盯多条线。</div>
    </section>

    <section class="panel">
      <h2>近3日公告检查</h2>
      <div class="readout">查询窗口：2026-06-13 至 2026-06-15。公告只作为风险/催化过滤，最终仍要以 6 月 16 日竞价、封单和分时承接确认。</div>
      <table><thead><tr><th>标的</th><th>公告数</th><th>近3日公告</th><th>判断</th></tr></thead><tbody>{announcement_html(data)}</tbody></table>
    </section>

    <section class="panel">
      <h2>次日计划</h2>
      <div class="readout"><strong>用户计划：</strong>待补充。未收到用户对 {NEXT_DATE_H} 的主动标的、仓位上限和加减仓条件，因此不把下面 AI 草案写成用户计划。</div>
      <table><thead><tr><th>计划类型</th><th>标的</th><th>触发条件</th><th>动作</th><th>仓位/风控</th></tr></thead><tbody>
        <tr><td>持仓风险处理</td><td>和远气体 / 中船特气</td><td>中船特气竞价继续弱，和远气体低开后 5-10 分钟不能收回均线。</td><td><span class="down">减仓或清仓和远气体</span></td><td>若仍持有，卖出条件优先于解释。</td></tr>
        <tr><td>老线修复确认</td><td>和远气体 / 中船特气</td><td>中船特气止跌并强修复，和远气体同步放量站上均线且不是单脉冲。</td><td>只允许小仓观察，不追高。</td><td>未收到用户仓位上限，AI 建议不超过 20%-25% 试错。</td></tr>
        <tr><td>有色承接</td><td>金钼股份 / 洛阳钼业</td><td>金钼股份继续强，洛阳钼业回踩均线不破或重新放量站回均线。</td><td>只看洛阳钼业承接型低吸。</td><td>单笔 20%-25%，跌破分时均线且不能收回则撤。</td></tr>
        <tr><td>新主线观察</td><td>PCB/CPO/先进封装核心</td><td>今日强板块次日仍有前排一字或换手晋级，容量票不补跌。</td><td>只做观察或低风险试错。</td><td>不追一致高开，等分歧承接。</td></tr>
      </tbody></table>
    </section>

    <section class="panel">
      <h2>AI建议</h2>
      <table><thead><tr><th>场景</th><th>触发条件</th><th>执行动作</th><th>明日复盘核对</th></tr></thead><tbody>
        <tr><td>竞价定性</td><td>9:25 先看和远气体、中船特气、金钼股份、洛阳钼业，再看 PCB/CPO 前排。</td><td>竞价只定性，不因持仓盈亏临时改计划。</td><td>是否先确认风险源，再决定持仓。</td></tr>
        <tr><td>持仓清仓</td><td>中船特气弱，和远气体低开低走或冲高回落跌破均线。</td><td><span class="down">清仓优先</span>，不等午后幻想修复。</td><td>是否按两个条件执行，是否该卖不卖。</td></tr>
        <tr><td>持仓继续</td><td>中船特气止跌，和远气体高开或平开后主动承接并放量。</td><td>只保留底仓，不加仓；等封板或强承接再评价。</td><td>是否把“止跌”误读为“转强”。</td></tr>
        <tr><td>主线切换</td><td>PCB/CPO、锂电、机器人延续强度，老六氟化钨不修复。</td><td>放弃老线进攻，只看新线分歧低吸或一进二确认。</td><td>是否区分题材切换和普涨扩散。</td></tr>
        <tr><td>空仓优先</td><td>指数高开低走、涨停晋级断层、炸板重新扩大。</td><td>不交易，等待下午或次日确认。</td><td>是否避免计划外交易。</td></tr>
      </tbody></table>
      <div class="readout">明日复盘核对重点：补充今日是否卖出/加仓；核对 6 月 16 日 9:25-9:45 是否严格围绕持仓风险源和新主线强度执行。</div>
    </section>
  </main>
  <script>
    const payload = {payload_json};

    function cls(v) {{ return v > 0 ? 'up' : v < 0 ? 'down' : 'flat'; }}
    function fmtPct(v) {{ return v == null ? '-' : `<span class="${{cls(v)}}">${{v >= 0 ? '+' : ''}}${{v.toFixed(2)}}%</span>`; }}
    function svgLineChart(elId, chart) {{
      const el = document.getElementById(elId);
      const w = el.clientWidth || 900, h = 280, pad = 34;
      const all = chart.series.flatMap(s => s.points.map(p => p.value));
      const min = Math.min(...all), max = Math.max(...all);
      const scaleY = v => h - pad - ((v - min) / (max - min || 1)) * (h - pad * 2);
      const maxLen = Math.max(...chart.series.map(s => s.points.length));
      const scaleX = i => pad + i / Math.max(1, maxLen - 1) * (w - pad * 2);
      const paths = chart.series.map(s => {{
        const d = s.points.map((p,i) => `${{i ? 'L' : 'M'}}${{scaleX(i).toFixed(1)}},${{scaleY(p.value).toFixed(1)}}`).join(' ');
        return `<path d="${{d}}" fill="none" stroke="${{s.color}}" stroke-width="2"/>`;
      }}).join('');
      const legend = chart.series.map((s,i) => `<text x="${{pad + i*120}}" y="20" fill="${{s.color}}" font-size="12">${{s.name}}</text>`).join('');
      const bars = chart.amountBars.map((b,i) => {{
        const bw = (w - pad * 2) / chart.amountBars.length - 5;
        const maxAmt = Math.max(...chart.amountBars.map(x => x.amountYi));
        const bh = b.amountYi / maxAmt * 58;
        return `<rect x="${{pad + i*(bw+5)}}" y="${{h - 8 - bh}}" width="${{bw}}" height="${{bh}}" fill="#dbeafe"/><text x="${{pad + i*(bw+5)}}" y="${{h-2}}" font-size="10" fill="#667085">${{b.date}}</text>`;
      }}).join('');
      el.innerHTML = `<svg viewBox="0 0 ${{w}} ${{h}}" role="img">${{legend}}<line x1="${{pad}}" y1="${{h-pad}}" x2="${{w-pad}}" y2="${{h-pad}}" stroke="#cbd5e1"/>${{paths}}${{bars}}</svg>`;
    }}

    function emotionChart() {{
      const chart = {{ series: [
        {{ name:'涨停', color:'#b42318', key:'limitUp' }},
        {{ name:'炸板', color:'#f59e0b', key:'openLimit' }},
        {{ name:'跌停', color:'#087443', key:'lowerLimit' }},
        {{ name:'最高连板', color:'#7c3aed', key:'maxBoard' }},
      ]}};
      const el = document.getElementById('emotionChart');
      const w = el.clientWidth || 900, h = 280, pad = 34;
      const all = chart.series.flatMap(s => payload.emotion.map(p => p[s.key]));
      const min = 0, max = Math.max(...all);
      const x = i => pad + i / Math.max(1, payload.emotion.length - 1) * (w - pad * 2);
      const y = v => h - pad - ((v - min) / (max - min || 1)) * (h - pad * 2);
      const paths = chart.series.map(s => {{
        const d = payload.emotion.map((p,i) => `${{i ? 'L' : 'M'}}${{x(i).toFixed(1)}},${{y(p[s.key]).toFixed(1)}}`).join(' ');
        return `<path d="${{d}}" fill="none" stroke="${{s.color}}" stroke-width="2"/><text x="${{pad + chart.series.indexOf(s)*120}}" y="20" fill="${{s.color}}" font-size="12">${{s.name}}</text>`;
      }}).join('');
      const labels = payload.emotion.map((p,i) => `<text x="${{x(i)-18}}" y="${{h-8}}" font-size="10" fill="#667085">${{p.date.slice(5)}}</text>`).join('');
      el.innerHTML = `<svg viewBox="0 0 ${{w}} ${{h}}"><line x1="${{pad}}" y1="${{h-pad}}" x2="${{w-pad}}" y2="${{h-pad}}" stroke="#cbd5e1"/>${{paths}}${{labels}}</svg>`;
    }}

    const canvas = document.getElementById('intradayCanvas');
    const ctx = canvas.getContext('2d');
    const state = {{ start:0, end:240, dragging:false, lastX:0, selected:new Map() }};
    function setupFilters() {{
      const box = document.getElementById('intradayFilters');
      payload.intradaySeries.forEach(s => state.selected.set(s.code, !!s.active));
      box.innerHTML = payload.intradaySeries.map(s => `<label class="chip"><input type="checkbox" data-code="${{s.code}}" ${{s.active?'checked':''}}> <span style="color:${{s.color}}">${{s.name}}</span></label>`).join('') +
        '<button id="onlyActive">仅主动</button><button id="allSeries">全选</button><button id="resetZoom">重置</button>';
      box.querySelectorAll('input').forEach(i => i.onchange = () => {{ state.selected.set(i.dataset.code, i.checked); drawIntraday(); }});
      document.getElementById('onlyActive').onclick = () => {{ box.querySelectorAll('input').forEach(i => {{ const keep = ['002971','688146','601958','603993','000001','000688'].includes(i.dataset.code); i.checked = keep; state.selected.set(i.dataset.code, keep); }}); drawIntraday(); }};
      document.getElementById('allSeries').onclick = () => {{ box.querySelectorAll('input').forEach(i => {{ i.checked = true; state.selected.set(i.dataset.code, true); }}); drawIntraday(); }};
      document.getElementById('resetZoom').onclick = () => {{ state.start=0; state.end=240; drawIntraday(); }};
    }}
    function selectedSeries() {{ return payload.intradaySeries.filter(s => state.selected.get(s.code) && s.points.length); }}
    function drawIntraday() {{
      const w = canvas.width, h = canvas.height, pad = 44;
      ctx.clearRect(0,0,w,h); ctx.fillStyle = '#fff'; ctx.fillRect(0,0,w,h);
      const series = selectedSeries();
      const vals = series.flatMap(s => s.points.slice(state.start,state.end+1).map(p => p.pct).filter(v => v != null));
      if (!vals.length) {{ ctx.fillStyle='#667085'; ctx.fillText('请选择标的', 40, 40); return; }}
      let min = Math.min(...vals), max = Math.max(...vals); const span = Math.max(1, max-min); min -= span*.12; max += span*.12;
      const x = i => pad + (i-state.start) / Math.max(1,state.end-state.start) * (w-pad*2);
      const y = v => h-pad - (v-min)/(max-min||1)*(h-pad*2);
      ctx.strokeStyle='#e5e7eb'; ctx.lineWidth=1; ctx.font='12px Arial';
      for (let g=0; g<=4; g++) {{ const yy=pad+g*(h-pad*2)/4; ctx.beginPath(); ctx.moveTo(pad,yy); ctx.lineTo(w-pad,yy); ctx.stroke(); const val=max-g*(max-min)/4; ctx.fillStyle='#667085'; ctx.fillText(val.toFixed(2)+'%', 6, yy+4); }}
      ctx.strokeStyle='#9ca3af'; ctx.beginPath(); ctx.moveTo(pad,y(0)); ctx.lineTo(w-pad,y(0)); ctx.stroke();
      series.forEach(s => {{
        ctx.strokeStyle=s.color; ctx.lineWidth=2; ctx.beginPath(); let first=true;
        s.points.forEach((p,i) => {{ if (i<state.start || i>state.end || p.pct == null) return; const xx=x(i), yy=y(p.pct); if(first) {{ctx.moveTo(xx,yy); first=false;}} else ctx.lineTo(xx,yy); }});
        ctx.stroke();
        const last = s.points[Math.min(state.end, s.points.length-1)];
        if (last && last.pct != null) {{ ctx.fillStyle=s.color; ctx.fillText(s.name, w-pad+6, y(last.pct)+4); }}
      }});
    }}
    canvas.addEventListener('wheel', e => {{
      e.preventDefault();
      const mid = (state.start + state.end) / 2, width = state.end - state.start;
      const next = Math.max(30, Math.min(240, width * (e.deltaY > 0 ? 1.15 : 0.85)));
      state.start = Math.max(0, Math.round(mid - next/2)); state.end = Math.min(240, Math.round(mid + next/2)); drawIntraday();
    }}, {{ passive:false }});
    canvas.addEventListener('pointerdown', e => {{ state.dragging=true; state.lastX=e.clientX; }});
    canvas.addEventListener('pointerup', () => state.dragging=false);
    canvas.addEventListener('pointerleave', () => state.dragging=false);
    canvas.addEventListener('pointermove', e => {{
      if (!state.dragging) return;
      const dx = e.clientX - state.lastX; state.lastX = e.clientX;
      const shift = Math.round(-dx / canvas.clientWidth * (state.end-state.start));
      state.start = Math.max(0, Math.min(240-(state.end-state.start), state.start + shift));
      state.end = Math.min(240, state.start + (state.end-state.start));
      drawIntraday();
    }});

    function setupDetails() {{
      const select = document.getElementById('detailSelect');
      select.innerHTML = Object.values(payload.stockDetails).map(d => `<option value="${{d.code}}" ${{d.code==='002971'?'selected':''}}>${{d.name}} ${{d.code}}</option>`).join('');
      function render() {{
        const d = payload.stockDetails[select.value];
        document.getElementById('stockDetail').innerHTML = [
          ['当日收盘', `${{d.price?.toFixed(2) ?? '-'}} / ${{fmtPct(d.closePct)}}`],
          ['3/5/10/30日', `${{fmtPct(d.pct3)}} / ${{fmtPct(d.pct5)}} / ${{fmtPct(d.pct10)}} / ${{fmtPct(d.pct30)}}`],
          ['5日线/10日线', `${{d.ma5?.toFixed(2) ?? '-'}} / ${{d.ma10?.toFixed(2) ?? '-'}}`],
          ['对应指数', `${{d.indexName}} 10日${{fmtPct(d.indexPct10)}} / 30日${{fmtPct(d.indexPct30)}}`],
          ['10日/30日偏离', `${{fmtPct(d.deviation10)}} / ${{fmtPct(d.deviation30)}}`],
          ['明日涨停模拟', `涨停价 ${{d.limitClose?.toFixed(2) ?? '-'}}；10日偏离 ${{fmtPct(d.simDeviation10)}}；30日偏离 ${{fmtPct(d.simDeviation30)}}`],
        ].map(([k,v]) => `<div><small>${{k}}</small><strong>${{v}}</strong></div>`).join('');
      }}
      select.onchange = render; render();
    }}
    window.addEventListener('resize', () => {{ svgLineChart('indexChart', payload.indexChart); emotionChart(); drawIntraday(); }});
    setupFilters(); setupDetails(); svgLineChart('indexChart', payload.indexChart); emotionChart(); drawIntraday();
  </script>
</body>
</html>
"""


def write_summary_files(data: dict) -> None:
    summary = {
        "review_date": REVIEW_DATE,
        "prev_date": data["prevDate"],
        "counts": {
            "limit_up": data["todayPools"]["limit_up"]["total"],
            "open_limit": data["todayPools"]["open_limit"]["total"],
            "lower_limit": data["todayPools"]["lower_limit"]["total"],
            "breadth_up": data["breadth"]["up"],
            "breadth_down": data["breadth"]["down"],
            "amount_yi": data["breadth"]["amount_yi"],
        },
        "blocks": [
            {
                "name": row.get("name"),
                "change": row.get("change"),
                "limit_up_num": row.get("limit_up_num"),
                "high": row.get("high"),
            }
            for row in data["todayPools"]["blocks"]["rows"][:10]
        ],
        "watchlist": data["stockDetails"],
        "feedback": data["feedbackRows"],
        "announcements": data["announcements"],
    }
    (ROOT / "market_review_20260615_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "breadth_20260615.json").write_text(json.dumps(data["breadth"], ensure_ascii=False, indent=2), encoding="utf-8")
    index_snapshot = {
        code: {
            "name": INDEXES[code]["name"],
            "last_60": value["rows"][-60:],
        }
        for code, value in data["indexes"]["daily"].items()
    }
    (ROOT / "index_20260615.json").write_text(json.dumps(index_snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    with (ROOT / "limit_pools_20260615.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["pool", "code", "name", "change_rate", "high_days", "reason_type", "open_num"])
        writer.writeheader()
        for pool_name, pool in [
            ("涨停", data["todayPools"]["limit_up"]),
            ("炸板", data["todayPools"]["open_limit"]),
            ("跌停", data["todayPools"]["lower_limit"]),
        ]:
            for row in pool["rows"]:
                writer.writerow(
                    {
                        "pool": pool_name,
                        "code": row.get("code"),
                        "name": row.get("name"),
                        "change_rate": row.get("change_rate"),
                        "high_days": row.get("high_days"),
                        "reason_type": row.get("reason_type"),
                        "open_num": row.get("open_num"),
                    }
                )


def update_index() -> None:
    html_text = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=review_20260615.html">
  <title>2026-06-15 复盘</title>
  <style>
    body { margin:0; min-height:100vh; display:grid; place-items:center; font-family:Arial,"Microsoft YaHei",sans-serif; color:#1f2937; background:#f6f8fb; }
    a { color:#1d4ed8; }
  </style>
</head>
<body>
  <p>正在打开复盘页面，若未自动跳转，点击 <a href="review_20260615.html">review_20260615.html</a>。</p>
</body>
</html>
"""
    (ROOT / "index.html").write_text(html_text, encoding="utf-8")


def main() -> None:
    data = build_data()
    write_summary_files(data)
    html_text = render_html(data)
    (ROOT / "review_20260615.html").write_text(html_text, encoding="utf-8")
    update_index()
    print("generated review_20260615.html")


if __name__ == "__main__":
    main()
