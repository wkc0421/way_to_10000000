#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import importlib.util
import json
import math
import time
from datetime import datetime
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
BASE_SCRIPT = ROOT / "tools" / "generate_review_20260615.py"
REVIEW_DATE = "20260616"
REVIEW_DATE_H = "2026-06-16"
NEXT_DATE_H = "2026-06-17"
PREV_DATE = "20260615"
PREV_DATE_H = "2026-06-15"

spec = importlib.util.spec_from_file_location("review_base_20260615", BASE_SCRIPT)
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(base)

base.REVIEW_DATE = REVIEW_DATE
base.REVIEW_DATE_H = REVIEW_DATE_H
base.NEXT_DATE_H = NEXT_DATE_H

UA = base.UA
COLORS = base.COLORS

WATCHLIST = [
    {"code": "600500", "name": "中化国际", "group": "旧高标", "note": "旧高标强修复样本"},
    {"code": "603065", "name": "宿迁联盛", "group": "旧高标", "note": "高标承接样本"},
    {"code": "000510", "name": "新金路", "group": "旧高标", "note": "材料/化工高标"},
    {"code": "002971", "name": "和远气体", "group": "旧高标", "note": "前期持仓线风险锚"},
    {"code": "002636", "name": "金安国纪", "group": "旧高标", "note": "失败高标修复观察"},
    {"code": "001696", "name": "宗申动力", "group": "旧高标", "note": "低空/动力链观察"},
    {"code": "601958", "name": "金钼股份", "group": "有色金属", "note": "明日备选进攻标的"},
    {"code": "603335", "name": "迪生力", "group": "持仓", "note": "明日不能红开则清仓"},
    {"code": "001257", "name": "盛龙股份", "group": "明日锚", "note": "一字强度与低位助攻锚"},
    {"code": "000636", "name": "风华高科", "group": "科技强度", "note": "元器件/科技强度观察"},
    {"code": "600162", "name": "香江控股", "group": "已卖出", "note": "今日卖出后留档"},
    {"code": "600396", "name": "华电辽能", "group": "电力观察", "note": "电力延续样本"},
    {"code": "000032", "name": "深桑达A", "group": "持仓", "note": "明日持仓到尾盘"},
    {"code": "603993", "name": "洛阳钼业", "group": "有色金属", "note": "明日备选容量标的"},
]

ACTIVE_CODES = {"000032", "603335", "600162", "001257", "601958", "603993", "000001", "000688"}

ACCOUNT = {
    "total_assets": 10483.08,
    "securities_value": 9864.00,
    "cash": 619.08,
    "total_pnl": 507.44,
    "day_pnl": 389.49,
    "realized_or_closed_pnl": 201.50,
}

HOLDINGS = [
    {"code": "603335", "name": "迪生力", "shares": 600, "cost": 8.808, "screen_price": 8.810, "pnl": 0.94, "pnl_pct": 0.023},
    {"code": "000032", "name": "深桑达A", "shares": 200, "cost": 21.365, "screen_price": 22.890, "pnl": 305.00, "pnl_pct": 7.138},
]

TRADES = [
    {"code": "000032", "name": "深桑达A", "side": "B", "time": "09:30", "full_time": "09:30:32", "price": 21.340, "order_price": 21.500, "shares": 200, "reason": "原始盘口理由待补充；结果上属于早盘强承接买入。"},
    {"code": "600162", "name": "香江控股", "side": "S", "time": "09:30", "full_time": "09:30:51", "price": 3.710, "order_price": 3.690, "shares": 1300, "reason": "兑现上一版计划外持仓的风险处理，卖出后规避尾盘走弱。"},
    {"code": "603335", "name": "迪生力", "side": "B", "time": "09:38", "full_time": "09:38:33", "price": 8.800, "order_price": 8.800, "shares": 600, "reason": "原始盘口理由待补充；收盘基本打平，明日按红开纪律处理。"},
]

INDEXES = base.INDEXES

KPL_HEADERS = {
    "User-Agent": "lhb/5.11.1 (com.kaipanla.www; build:0; iOS 14.6.0) Alamofire/5.11.1",
    "Accept": "*/*",
    "Connection": "keep-alive",
}


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def fnum(value, default: float | None = None) -> float | None:
    return base.fnum(value, default)


def fmt_num(value, digits: int = 2) -> str:
    return base.fmt_num(value, digits)


def fmt_ts(value) -> str:
    return base.fmt_ts(value)


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "-"
    cls = "up" if value > 0 else "down" if value < 0 else "flat"
    return f'<span class="{cls}">{value:+.2f}%</span>'


def fmt_money_yi(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value / 100000000:.2f}亿"


def secid_for(code: str) -> str:
    return base.secid_for(code)


def board_count(label: str | None) -> int:
    return base.board_count(label)


def pct_change_from_rows(rows: list[dict], days: int) -> float | None:
    return base.pct_change_from_rows(rows, days)


def moving_average(rows: list[dict], days: int) -> float | None:
    return base.moving_average(rows, days)


def prev_close(rows: list[dict]) -> float | None:
    return base.prev_close(rows, REVIEW_DATE_H)


def corresponding_index(code: str) -> str:
    return base.corresponding_index(code)


def request_json(url: str, params: dict | None = None, headers: dict | None = None, retries: int = 3, timeout: int = 10) -> tuple[dict, str]:
    return base.request_json(url, params=params, headers=headers, retries=retries, timeout=timeout)


def fetch_kpl_ranking(type_id: str, limit: int = 40) -> list[dict]:
    form = {
        "Index": "0",
        "Order": "1",
        "PhoneOSNew": "2",
        "Type": type_id,
        "VerSion": "5.11.0.1",
        "ZSType": "7",
        "a": "RealRankingInfo",
        "apiv": "w33",
        "c": "ZhiShuRanking",
        "st": str(limit),
    }
    response = requests.post("https://apphq.longhuvip.com/w1/api/index.php", headers=KPL_HEADERS, data=form, timeout=20)
    response.raise_for_status()
    rows = response.json().get("list") or []
    result = []
    for row in rows:
        result.append(
            {
                "code": row[0] if len(row) > 0 else "",
                "name": row[1] if len(row) > 1 else "",
                "strength": fnum(row[2]) if len(row) > 2 else None,
                "pct": fnum(row[3]) if len(row) > 3 else None,
                "momentum": fnum(row[4]) if len(row) > 4 else None,
                "amount": fnum(row[5]) if len(row) > 5 else None,
                "main_net": fnum(row[6]) if len(row) > 6 else None,
                "rank_strength": fnum(row[-2]) if len(row) >= 2 else None,
                "rank_pct": fnum(row[-1]) if len(row) >= 1 else None,
                "stocks": [],
            }
        )
    return result


def fetch_kpl_stock_list(plate_id: str) -> list[dict]:
    params = {
        "Order": "1",
        "st": "12",
        "a": "ZhiShuStockList_W8",
        "c": "ZhiShuRanking",
        "PhoneOSNew": "1",
        "old": "1",
        "apiv": "w21",
        "Type": "6",
        "PlateID": plate_id,
    }
    try:
        data, _ = request_json("https://apphq.longhuvip.com/w1/api/index.php", params=params, headers=KPL_HEADERS, retries=1, timeout=12)
    except Exception:
        return []
    raw_rows = data.get("List") or data.get("list") or []
    rows = []
    for row in raw_rows:
        if isinstance(row, list):
            rows.append(
                {
                    "code": row[0] if len(row) > 0 else "",
                    "name": row[1] if len(row) > 1 else "",
                    "pct": fnum(row[3]) if len(row) > 3 else None,
                    "tag": row[4] if len(row) > 4 else "",
                }
            )
        elif isinstance(row, dict):
            rows.append(row)
    return rows


def fetch_daily_fast(secid: str) -> dict:
    return base.fetch_sina_kline(secid, REVIEW_DATE, "direct daily OHLC fallback")


def fetch_intraday_fast(secid: str, base_close: float | None, daily_rows: list[dict] | None = None) -> list[dict]:
    urls = [
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
        "ut": base.EM_UT,
    }
    for url in urls:
        try:
            data, _ = request_json(url, params=params, retries=1, timeout=6)
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
            if rows:
                return rows
        except Exception:
            continue
    return base.synthetic_intraday(daily_rows, base_close)


def fetch_announcements_fast(code: str, start_h: str, end_h: str) -> list[dict]:
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
    try:
        response = requests.get(
            "https://np-anotice-stock.eastmoney.com/api/security/ann",
            params=params,
            headers={"User-Agent": UA},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []
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


def load_kpl_snapshot() -> dict:
    cached_path = ROOT / "kpl_sector_20260616_20260615.json"
    if cached_path.exists():
        cached = json.loads(cached_path.read_text(encoding="utf-8"))
        if REVIEW_DATE_H in cached and PREV_DATE_H in cached:
            return cached
    previous_path = ROOT / "kpl_sector_20260615_20260612.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {}
    today = {
        "date": REVIEW_DATE_H,
        "source": "kaipanla-apphq",
        "groups": {
            "selected": fetch_kpl_ranking("0", 40),
            "concepts": fetch_kpl_ranking("2", 40),
            "themes": fetch_kpl_ranking("6", 40),
        },
    }
    for group in today["groups"].values():
        for row in group[:6]:
            row["stocks"] = fetch_kpl_stock_list(row["code"])
            time.sleep(0.05)
    snapshot = {
        REVIEW_DATE_H: today,
        PREV_DATE_H: previous.get(PREV_DATE_H, {}),
    }
    cached_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return snapshot


def fetch_breadth() -> dict:
    base_params = {
        "pz": "100",
        "po": "1",
        "np": "1",
        "ut": base.EM_UT,
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
        "fields": "f12,f14,f2,f3,f4,f5,f6,f8,f100",
        "_": str(int(time.time() * 1000)),
    }
    hosts = [
        "https://push2.eastmoney.com/api/qt/clist/get",
        "https://82.push2.eastmoney.com/api/qt/clist/get",
        "http://82.push2.eastmoney.com/api/qt/clist/get",
        "https://70.push2.eastmoney.com/api/qt/clist/get",
    ]
    rows = []
    total = None
    last_url = ""
    for page in range(1, 90):
        params = {"pn": str(page), **base_params}
        data = None
        for host in hosts:
            try:
                data, last_url = request_json(host, params=params, timeout=8, retries=1)
                break
            except Exception:
                continue
        if not data:
            raise RuntimeError("breadth endpoints unavailable")
        body = data.get("data") or {}
        batch = body.get("diff") or []
        rows.extend(batch)
        total = body.get("total", total)
        if not batch or total is None or len(rows) >= total:
            break
        time.sleep(0.03)
    valid = [row for row in rows if fnum(row.get("f3")) is not None]
    return {
        "source_url": last_url,
        "total": total,
        "valid_count": len(valid),
        "up": sum(1 for row in valid if fnum(row.get("f3"), 0) > 0),
        "down": sum(1 for row in valid if fnum(row.get("f3"), 0) < 0),
        "flat": sum(1 for row in valid if fnum(row.get("f3"), 0) == 0),
        "amount_yi": sum(fnum(row.get("f6"), 0) for row in valid) / 100000000,
        "gt5": sum(1 for row in valid if fnum(row.get("f3"), 0) >= 5),
        "lt_minus5": sum(1 for row in valid if fnum(row.get("f3"), 0) <= -5),
    }


def fetch_quote_amounts(codes: list[str]) -> dict:
    secids = ",".join(secid_for(code) for code in codes)
    params = {
        "fltt": "2",
        "invt": "2",
        "fields": "f12,f14,f2,f3,f4,f5,f6,f8",
        "secids": secids,
        "ut": base.EM_UT,
    }
    try:
        data, _ = request_json("https://82.push2.eastmoney.com/api/qt/ulist.np/get", params=params, timeout=10, retries=1)
        return {row.get("f12"): row for row in ((data.get("data") or {}).get("diff") or [])}
    except Exception:
        return {}


def pool_from_source(path: Path, key: str) -> dict | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    ths = data.get("tonghuashun") or {}
    return ths.get(key)


def fetch_pool_for_date(date_yyyymmdd: str, source_by_date: dict[str, dict] | None = None) -> dict:
    source_by_date = source_by_date or {}
    if date_yyyymmdd in source_by_date:
        return source_by_date[date_yyyymmdd]
    lu = base.fetch_ths_pool("limit_up_pool", date_yyyymmdd)
    op = base.fetch_ths_pool("open_limit_pool", date_yyyymmdd)
    lo = base.fetch_ths_pool("lower_limit_pool", date_yyyymmdd)
    result = {"limit_up": lu, "open_limit": op, "lower_limit": lo}
    source_by_date[date_yyyymmdd] = result
    return result


def build_data() -> dict:
    source_check_path = ROOT / "source_check_20260616.json"
    source_check = json.loads(source_check_path.read_text(encoding="utf-8")) if source_check_path.exists() else {}
    previous_source_path = ROOT / "source_check_20260615.json"
    previous_source = json.loads(previous_source_path.read_text(encoding="utf-8")) if previous_source_path.exists() else {}

    today_pools = {
        "limit_up": source_check["tonghuashun"]["limit_up_pool"] if source_check.get("tonghuashun") else base.fetch_ths_pool("limit_up_pool", REVIEW_DATE),
        "open_limit": source_check["tonghuashun"]["open_limit_pool"] if source_check.get("tonghuashun") else base.fetch_ths_pool("open_limit_pool", REVIEW_DATE),
        "lower_limit": source_check["tonghuashun"]["lower_limit_pool"] if source_check.get("tonghuashun") else base.fetch_ths_pool("lower_limit_pool", REVIEW_DATE),
        "blocks": source_check["tonghuashun"]["block_top"] if source_check.get("tonghuashun") else base.fetch_ths_block_top(REVIEW_DATE),
    }
    prev_pools = {
        "limit_up": previous_source["tonghuashun"]["limit_up_pool"],
        "open_limit": previous_source["tonghuashun"]["open_limit_pool"],
        "lower_limit": previous_source["tonghuashun"]["lower_limit_pool"],
        "blocks": previous_source["tonghuashun"]["block_top"],
    }

    kpl = load_kpl_snapshot()

    index_daily = {}
    index_intraday = {}
    for code, meta in INDEXES.items():
        daily = fetch_daily_fast(meta["secid"])
        index_daily[code] = daily
        if code in {"000001", "000688"}:
            index_intraday[code] = fetch_intraday_fast(meta["secid"], prev_close(daily["rows"]), daily["rows"])
        else:
            index_intraday[code] = base.synthetic_intraday(daily["rows"], prev_close(daily["rows"]))

    source_by_date = {
        PREV_DATE: {"limit_up": prev_pools["limit_up"], "open_limit": prev_pools["open_limit"], "lower_limit": prev_pools["lower_limit"]},
        REVIEW_DATE: {"limit_up": today_pools["limit_up"], "open_limit": today_pools["open_limit"], "lower_limit": today_pools["lower_limit"]},
    }
    trading_dates = [row["date"].replace("-", "") for row in index_daily["000001"]["rows"][-10:]]
    emotion = []
    for day in trading_dates:
        pools = fetch_pool_for_date(day, source_by_date)
        max_board = max([board_count(row.get("high_days")) for row in pools["limit_up"]["rows"]] or [0])
        emotion.append(
            {
                "date": f"{day[:4]}-{day[4:6]}-{day[6:]}",
                "limitUp": pools["limit_up"]["total"],
                "openLimit": pools["open_limit"]["total"],
                "lowerLimit": pools["lower_limit"]["total"],
                "maxBoard": max_board,
            }
        )

    try:
        breadth = fetch_breadth()
    except Exception:
        breadth = {
            "up": 2730,
            "down": 2677,
            "flat": None,
            "amount_yi": 30646.96,
            "gt5": None,
            "lt_minus5": None,
            "source_note": "公开新闻口径：全市场2730只上涨、2677只下跌，沪深两市成交额约30646.96亿元；平盘家数待补充。",
        }

    quote_rows = fetch_quote_amounts([item["code"] for item in WATCHLIST])
    stock_daily = {}
    stock_intraday = {}
    for idx, item in enumerate(WATCHLIST):
        daily = fetch_daily_fast(secid_for(item["code"]))
        stock_daily[item["code"]] = daily
        if item["code"] in ACTIVE_CODES:
            points = fetch_intraday_fast(secid_for(item["code"]), prev_close(daily["rows"]), daily["rows"])
        else:
            points = base.synthetic_intraday(daily["rows"], prev_close(daily["rows"]))
        stock_intraday[item["code"]] = points
        item["color"] = COLORS[idx % len(COLORS)]

    for trade in TRADES:
        if trade["code"] not in stock_intraday:
            daily = fetch_daily_fast(secid_for(trade["code"]))
            stock_daily[trade["code"]] = daily
            stock_intraday[trade["code"]] = fetch_intraday_fast(secid_for(trade["code"]), prev_close(daily["rows"]), daily["rows"])

    today_limit_map = {row["code"]: row for row in today_pools["limit_up"]["rows"]}
    today_open_map = {row["code"]: row for row in today_pools["open_limit"]["rows"]}
    today_down_map = {row["code"]: row for row in today_pools["lower_limit"]["rows"]}

    prev_2plus_all = [row for row in prev_pools["limit_up"]["rows"] if board_count(row.get("high_days")) >= 2]
    prev_3plus = [row for row in prev_2plus_all if board_count(row.get("high_days")) >= 3]
    prev_2 = [row for row in prev_2plus_all if board_count(row.get("high_days")) == 2]
    prev_2.sort(key=lambda row: row.get("first_limit_up_time") or 9999999999)
    feedback_base = prev_3plus + (prev_2 if len(prev_2) <= 10 else prev_2[:5])
    feedback_rows = []
    for row in feedback_base:
        code = row["code"]
        if code not in stock_daily:
            stock_daily[code] = fetch_daily_fast(secid_for(code))
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

    stock_details = {}
    for item in WATCHLIST:
        code = item["code"]
        rows = stock_daily[code]["rows"]
        last = rows[-1] if rows else {}
        pc = prev_close(rows)
        quote = quote_rows.get(code, {})
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
            "openPct": None if last.get("open") is None or pc in (None, 0) else (last["open"] / pc - 1) * 100,
            "highPct": None if last.get("high") is None or pc in (None, 0) else (last["high"] / pc - 1) * 100,
            "lowPct": None if last.get("low") is None or pc in (None, 0) else (last["low"] / pc - 1) * 100,
            "closePct": last.get("pct_chg"),
            "amount": fnum(quote.get("f6"), last.get("amount")),
            "turnover": fnum(quote.get("f8"), last.get("turnover")),
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
            "poolStatus": "涨停" if code in today_limit_map else "炸板" if code in today_open_map else "跌停" if code in today_down_map else "普通波动",
            "reasonType": (today_limit_map.get(code) or today_open_map.get(code) or {}).get("reason_type"),
        }

    high_codes = []
    for row in today_pools["limit_up"]["rows"][:100]:
        if board_count(row.get("high_days")) >= 2 or row.get("code") in ACTIVE_CODES:
            high_codes.append({"code": row["code"], "name": row["name"], "label": row.get("high_days") or "首板"})
    for item in WATCHLIST:
        if item["code"] in ACTIVE_CODES and item["code"] not in {x["code"] for x in high_codes}:
            high_codes.append({"code": item["code"], "name": item["name"], "label": item["group"]})
    high_stats = []
    for item in high_codes[:18]:
        code = item["code"]
        if code not in stock_daily:
            stock_daily[code] = fetch_daily_fast(secid_for(code))
        rows = stock_daily[code]["rows"]
        high_stats.append(
            {
                "code": code,
                "name": item["name"],
                "label": item["label"],
                "yesterday": rows[-2].get("pct_chg") if len(rows) >= 2 else None,
                "today": rows[-1].get("pct_chg") if rows else None,
                "pct2": pct_change_from_rows(rows, 2),
                "pct3": pct_change_from_rows(rows, 3),
                "pct5": pct_change_from_rows(rows, 5),
            }
        )

    announcements = {}
    for item in WATCHLIST:
        rows = fetch_announcements_fast(item["code"], "2026-06-14", REVIEW_DATE_H)
        tone, note = base.announcement_judgement(rows)
        announcements[item["code"]] = {"items": rows[:10], "tone": tone, "note": note}

    corr_symbols = ["000032", "603335", "001257", "601958", "603993", "000001", "000688"]
    series_for_corr = {}
    for code in corr_symbols:
        if code in stock_intraday:
            series_for_corr[code] = base.rel_returns(stock_intraday[code])
        else:
            series_for_corr[code] = base.rel_returns(index_intraday[code])
    correlations = []
    for i, code_a in enumerate(corr_symbols):
        for code_b in corr_symbols[i + 1 :]:
            value = base.pearson(series_for_corr[code_a], series_for_corr[code_b])
            correlations.append({"a": code_a, "b": code_b, "corr": value})
    correlations.sort(key=lambda row: -abs(row["corr"] or 0))

    return {
        "reviewDate": REVIEW_DATE_H,
        "nextDate": NEXT_DATE_H,
        "prevDate": PREV_DATE_H,
        "sourceCheck": source_check,
        "todayPools": today_pools,
        "prevPools": prev_pools,
        "kpl": kpl,
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


def kpl_rows(rows: list[dict], n: int = 3) -> str:
    body = []
    for row in rows[:n]:
        stocks = row.get("stocks") or []
        if stocks:
            lines = "".join(f"<li><strong>{esc(s.get('name'))}</strong><span>开盘啦成分股样本</span><em>{fmt_pct(fnum(s.get('pct')))}</em></li>" for s in stocks[:4])
        else:
            lines = '<li><strong>成分股待开盘啦补充</strong><span>当前接口未返回成分股，不使用其他来源冒充核心标的。</span><em class="flat">-</em></li>'
        body.append(
            f"""
            <article class="sector-card">
              <div class="sector-top"><h3>{esc(row.get('name'))}</h3><span>强度 {fmt_num(row.get('strength'), 0)}</span></div>
              <p>涨幅 {fmt_pct(row.get('pct'))}，动能 {fmt_num(row.get('momentum'), 3)}。交易含义：强度越靠前，越适合作为明日竞价和低位助攻的验证对象。</p>
              <ul>{lines}</ul>
            </article>
            """
        )
    return "\n".join(body)


def ths_sector_rows(blocks: list[dict], n: int = 5) -> str:
    rows = []
    for block in blocks[:n]:
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
    out = []
    for row in rows:
        pct = row.get("today_pct")
        if row["status"] == "涨停晋级":
            verdict = "晋级正反馈，可作为情绪强度样本。"
        elif row["status"] == "炸板":
            verdict = "冲板未封住，板上兑现压力偏大。"
        elif row["status"] == "跌停":
            verdict = "极端负反馈，压制同层接力风险偏好。"
        elif pct is not None and pct > 0:
            verdict = "断板收红，承接尚可但不算晋级确认。"
        else:
            verdict = "断板走弱，后排接力反馈一般。"
        out.append(
            "<tr>"
            f"<td>{esc(row['prev_height'])}</td>"
            f"<td><strong>{esc(row['name'])}</strong><span class=\"code\">{esc(row['code'])}</span></td>"
            f"<td>{esc(row['prev_first'])}</td>"
            f"<td>{esc(row['status'])}</td>"
            f"<td>开 {fmt_num(row['open'])} / 高 {fmt_num(row['high'])} / 收 {fmt_num(row['close'])}（{fmt_pct(row['today_pct'])}）</td>"
            f"<td>{esc(verdict)}</td>"
            "</tr>"
        )
    return "\n".join(out)


def watchlist_html(data: dict) -> str:
    rows = []
    for item in WATCHLIST:
        detail = data["stockDetails"][item["code"]]
        note = item["note"]
        if detail.get("reasonType"):
            note += f"；涨停归因：{detail['reasonType']}"
        rows.append(
            "<tr>"
            f"<td>{esc(item['group'])}</td>"
            f"<td><strong>{esc(item['name'])}</strong><span class=\"code\">{item['code']}</span></td>"
            f"<td>{fmt_pct(detail['openPct'])}</td>"
            f"<td>{fmt_pct(detail['highPct'])}</td>"
            f"<td>{fmt_pct(detail['lowPct'])}</td>"
            f"<td>{fmt_pct(detail['closePct'])}</td>"
            f"<td>{fmt_money_yi(detail['amount'])}</td>"
            f"<td>{esc(note)}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def high_stats_html(rows: list[dict]) -> str:
    return "\n".join(
        "<tr>"
        f"<td><strong>{esc(row['name'])}</strong><span class=\"code\">{esc(row['code'])}</span></td>"
        f"<td>{esc(row['label'])}</td>"
        f"<td>{fmt_pct(row['yesterday'])}</td>"
        f"<td>{fmt_pct(row['today'])}</td>"
        f"<td>{fmt_pct(row['pct2'])}</td>"
        f"<td>{fmt_pct(row['pct3'])}</td>"
        f"<td>{fmt_pct(row['pct5'])}</td>"
        "</tr>"
        for row in rows
    )


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


def correlation_cards(data: dict) -> str:
    names = {item["code"]: item["name"] for item in WATCHLIST}
    names.update({"000001": "上证指数", "000688": "科创50"})
    cards = []
    for row in data["correlations"][:8]:
        c = row["corr"]
        if c is None:
            desc = "样本不足"
        elif c >= 0.55:
            desc = "强同向，可作为共振确认"
        elif c <= -0.35:
            desc = "逆向，注意跷跷板"
        elif abs(c) < 0.2:
            desc = "相关弱，不能互相证明"
        else:
            desc = "中等相关，只能辅助验证"
        cards.append(
            f'<div class="corr-card"><small>{esc(names.get(row["a"], row["a"]))} / {esc(names.get(row["b"], row["b"]))}</small><strong>{fmt_num(c, 2)}</strong><span>{esc(desc)}</span></div>'
        )
    return "\n".join(cards)


def holdings_html(data: dict) -> str:
    rows = []
    for holding in HOLDINGS:
        detail = data["stockDetails"][holding["code"]]
        market_value = holding["shares"] * (detail["price"] or holding["screen_price"])
        position = market_value / ACCOUNT["total_assets"] * 100
        rows.append(
            "<tr>"
            f"<td><strong>{esc(holding['name'])}</strong><span class=\"code\">{holding['code']}</span></td>"
            "<td>持仓</td>"
            f"<td>{holding['shares']} 股</td>"
            f"<td>{holding['cost']:.3f}</td>"
            f"<td>{detail['price']:.2f}</td>"
            f"<td>¥{market_value:,.0f}</td>"
            f"<td>{holding['pnl']:+.2f} / {holding['pnl_pct']:+.3f}%</td>"
            f"<td>{position:.2f}%</td>"
            "</tr>"
        )
    return "\n".join(rows)


def trades_html() -> str:
    side_name = {"B": "买入", "S": "卖出"}
    cls = {"B": "up", "S": "down"}
    return "\n".join(
        "<tr>"
        f"<td>{esc(trade['full_time'])}</td>"
        f"<td><strong>{esc(trade['name'])}</strong><span class=\"code\">{trade['code']}</span></td>"
        f"<td><span class=\"{cls[trade['side']]}\">{side_name[trade['side']]}</span></td>"
        f"<td>{trade['shares']}</td>"
        f"<td>委托 {trade['order_price']:.3f} / 成交 {trade['price']:.3f}</td>"
        f"<td>{esc(trade['reason'])}</td>"
        "</tr>"
        for trade in TRADES
    )


def plan_from_prev_html() -> str:
    prev = ROOT / "review_20260615.html"
    if not prev.exists():
        return "未找到上一份复盘，今日不做计划一致性评分。"
    text = prev.read_text(encoding="utf-8", errors="ignore")
    if "香江控股" in text and "金钼股份" in text and "风华高科" in text:
        return "上一版计划的主动核对线为：香江控股持仓处理、金钼/洛钼有色强度确认、风华及 PCB/CPO/先进封装科技强度确认，空仓优先条件为主线分化或持仓走弱。"
    return "上一版复盘存在，但未能完整抽取计划文本。"


def render_html(data: dict) -> str:
    today = data["todayPools"]
    prev = data["prevPools"]
    kpl_today = data["kpl"][REVIEW_DATE_H]["groups"]
    kpl_prev = (data["kpl"].get(PREV_DATE_H) or {}).get("groups") or {}
    breadth = data["breadth"]
    sse = data["indexes"]["daily"]["000001"]["rows"][-1]
    star = data["indexes"]["daily"]["000688"]["rows"][-1]
    sz = data["indexes"]["daily"]["399001"]["rows"][-1]
    cy_like = data["indexes"]["daily"]["399107"]["rows"][-1]
    amount_text = "-" if breadth.get("amount_yi") is None else f"{breadth['amount_yi']:.0f}亿"
    breadth_total = max(1, (breadth.get("up") or 0) + (breadth.get("down") or 0) + (breadth.get("flat") or 0))
    breadth_up_pct = (breadth.get("up") or 0) / breadth_total * 100
    breadth_down_pct = (breadth.get("down") or 0) / breadth_total * 100
    breadth_flat_pct = (breadth.get("flat") or 0) / breadth_total * 100
    emotion_total = max(1, today["limit_up"]["total"] + today["open_limit"]["total"] + today["lower_limit"]["total"])
    emotion_limit_pct = today["limit_up"]["total"] / emotion_total * 100
    emotion_open_pct = today["open_limit"]["total"] / emotion_total * 100
    emotion_down_pct = today["lower_limit"]["total"] / emotion_total * 100
    top_kpl = kpl_today["selected"][0] if kpl_today.get("selected") else {}
    prev_top_kpl = (kpl_prev.get("selected") or [{}])[0]
    feedback = data["feedbackRows"]
    feedback_stats = {
        "upgrade": sum(1 for row in feedback if row["status"] == "涨停晋级"),
        "open": sum(1 for row in feedback if row["status"] == "炸板"),
        "down": sum(1 for row in feedback if row["status"] == "跌停"),
        "broken": sum(1 for row in feedback if row["status"].startswith("断板")),
        "avg": sum((row["today_pct"] or 0) for row in feedback) / len(feedback) if feedback else 0,
    }
    deep = data["stockDetails"]["000032"]
    disenli = data["stockDetails"]["603335"]
    shenglong = data["stockDetails"]["001257"]
    jinmu = data["stockDetails"]["601958"]
    luomo = data["stockDetails"]["603993"]
    xiangjiang = data["stockDetails"]["600162"]
    max_board = max([board_count(row.get("high_days")) for row in today["limit_up"]["rows"]] or [0])
    prev_limit_count = prev["limit_up"]["total"]
    limit_delta = today["limit_up"]["total"] - prev_limit_count
    loss_line = "负反馈相对扩散" if today["lower_limit"]["total"] > prev["lower_limit"]["total"] else "负反馈未继续扩散"
    execution_score = 68
    payload = {
        "indexChart": {
            "series": [
                {
                    "name": INDEXES[code]["name"],
                    "color": INDEXES[code]["color"],
                    "points": [
                        {"date": row["date"], "value": (row["close"] / rows[-60]["close"] - 1) * 100}
                        for row in rows[-60:]
                    ],
                }
                for code, rows in [
                    ("000001", data["indexes"]["daily"]["000001"]["rows"]),
                    ("000688", data["indexes"]["daily"]["000688"]["rows"]),
                ]
                if len(rows) >= 60 and rows[-60].get("close")
            ],
            "amountBars": [
                {"date": row["date"][5:], "amountYi": (row.get("amount") or row.get("volume") or 0) / 100000000}
                for row in data["indexes"]["daily"]["000001"]["rows"][-7:]
            ],
        },
        "marketStats": [
            {
                "label": "60日阶段强弱",
                "value": f"上证 {fmt_pct((sse['close'] / data['indexes']['daily']['000001']['rows'][-60]['close'] - 1) * 100)}",
                "sub": f"科创 {fmt_pct((star['close'] / data['indexes']['daily']['000688']['rows'][-60]['close'] - 1) * 100)}",
            },
            {
                "label": "科创50-上证阶段强弱差",
                "value": fmt_pct(((star["close"] / data["indexes"]["daily"]["000688"]["rows"][-60]["close"] - 1) - (sse["close"] / data["indexes"]["daily"]["000001"]["rows"][-60]["close"] - 1)) * 100),
                "sub": "科技线仍强于主板，但今日指数分化。",
            },
            {
                "label": "今日指数表现",
                "value": "深强沪弱",
                "sub": f"上证 {fmt_pct(sse.get('pct_chg'))}，深成 {fmt_pct(sz.get('pct_chg'))}，科创 {fmt_pct(star.get('pct_chg'))}，创业板口径 {fmt_pct(cy_like.get('pct_chg'))}",
            },
            {
                "label": "量能变化",
                "value": amount_text,
                "sub": "全A成交额口径；近7日柱状图使用指数成交量口径。" if breadth.get("amount_yi") is not None else "成交额口径待补充；柱状图使用指数成交量。",
            },
        ],
        "emotion": data["emotion"],
        "intradaySeries": [
            {
                "code": code,
                "name": meta["name"],
                "color": meta.get("color", "#374151"),
                "active": code in {"000032", "603335", "001257", "601958", "603993", "000001", "000688"},
                "points": data["stockIntraday"].get(code, data["indexes"]["intraday"].get(code, [])),
            }
            for code, meta in (
                [(item["code"], item) for item in WATCHLIST]
                + [("000001", {"name": "上证指数", "color": "#374151"}), ("000688", {"name": "科创50", "color": "#7c3aed"})]
            )
        ],
        "stockDetails": data["stockDetails"],
        "trades": TRADES,
    }
    payload_json = json.dumps(payload, ensure_ascii=False)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    previous_plan = plan_from_prev_html()

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>2026-06-16 超短复盘</title>
  <style>
    :root {{ --bg:#f6f8fb; --panel:#fff; --text:#1f2937; --muted:#667085; --line:#e5e7eb; --red:#b42318; --green:#087443; --up:#b42318; --down:#087443; --blue:#1d4ed8; --amber:#b45309; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:Arial,"Microsoft YaHei",sans-serif; line-height:1.55; }}
    header {{ background:#111827; color:#fff; padding:26px 32px; }}
    header h1 {{ margin:0 0 8px; font-size:28px; letter-spacing:0; }}
    header p {{ margin:0; color:#d1d5db; }}
    main {{ max-width:1480px; margin:0 auto; padding:18px; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-bottom:14px; }}
    .metric,.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:0 1px 2px rgba(16,24,40,.04); }}
    .metric {{ padding:14px; }}
    .metric small,.stat-card small,.position-card small,.trade-fact small,.corr-card small,.detail-metrics small {{ display:block; color:var(--muted); font-size:12px; margin-bottom:5px; }}
    .metric strong {{ display:block; font-size:22px; }}
    .metric span {{ color:var(--muted); font-size:13px; }}
    .panel {{ padding:18px; margin-bottom:14px; }}
    h2 {{ margin:0 0 14px; font-size:20px; }}
    h3 {{ margin:0; font-size:16px; }}
    .readout {{ background:#f8fafc; border:1px solid var(--line); border-radius:8px; padding:12px 14px; margin:12px 0; color:#344054; }}
    .readout span {{ display:inline-block; margin-right:16px; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ border-bottom:1px solid var(--line); padding:9px 8px; text-align:left; vertical-align:top; }}
    th {{ color:#475467; background:#f9fafb; font-weight:700; }}
    ul {{ margin:0; padding-left:18px; }}
    .code {{ display:block; color:#667085; font-size:12px; margin-top:2px; }}
    .up {{ color:var(--red); }} .down {{ color:var(--green); }} .flat {{ color:#667085; }}
    .market-overview {{ padding:0; overflow:hidden; }}
    .market-head {{ display:flex; justify-content:space-between; align-items:flex-start; gap:14px; padding:16px 18px 10px; border-bottom:1px solid var(--line); background:#fbfdff; }}
    .market-head h2 {{ margin:0 0 6px; }}
    .market-head p {{ margin:0; color:var(--muted); font-size:13px; line-height:1.5; }}
    .limit-trend-head,.analysis-head {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }}
    .market-layout {{ display:grid; grid-template-columns:1fr; gap:12px; padding:14px 18px 16px; }}
    .market-chart-card {{ min-width:0; }}
    #marketChart {{ width:100%; height:340px; display:block; border:1px solid var(--line); border-radius:8px; background:#fff; cursor:crosshair; }}
    .market-legend {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:10px; color:var(--muted); font-size:12px; }}
    .market-legend i {{ display:inline-block; width:12px; height:8px; margin-right:5px; border-radius:2px; vertical-align:middle; }}
    .market-legend .line-sse {{ background:#1c5d99; }}
    .market-legend .line-star {{ background:#c92a2a; }}
    .market-legend .line-zero {{ background:#94a3b8; }}
    .limit-trend-panel {{ display:grid; gap:14px; }}
    .limit-trend-head p {{ margin:0; color:var(--muted); font-size:13px; line-height:1.55; }}
    .limit-trend-chart {{ width:100%; height:380px; display:block; border:1px solid var(--line); border-radius:8px; background:#fff; cursor:crosshair; }}
    .market-side {{ display:grid; grid-template-columns:minmax(290px,.8fr) minmax(300px,.85fr) minmax(360px,1fr); gap:12px; align-items:start; }}
    .market-stats,.position-summary,.trade-fact-grid,.correlation-grid,.limit-trend-stats,.detail-metrics {{ display:grid; gap:10px; }}
    .market-stats {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
    .position-summary {{ grid-template-columns:repeat(5,minmax(0,1fr)); }}
    .trade-fact-grid {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
    .correlation-grid {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
    .limit-trend-stats {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
    .detail-metrics {{ grid-template-columns:repeat(4,minmax(0,1fr)); margin-top:10px; }}
    .stat-card,.position-card,.trade-fact,.corr-card,.detail-metrics div,.summary-point {{ border:1px solid var(--line); border-radius:8px; padding:10px; background:#fff; }}
    .market-stat {{ background:#f8fafc; border-radius:8px; padding:12px; min-height:78px; }}
    .market-stat small {{ display:block; color:var(--muted); margin-bottom:6px; }}
    .market-stat strong {{ display:block; font-size:24px; line-height:1.1; }}
    .market-stat span {{ display:block; margin-top:6px; color:var(--muted); font-size:12px; line-height:1.45; }}
    .turnover-card {{ border:1px solid var(--line); border-radius:8px; padding:12px; background:#fff; }}
    .turnover-card h3 {{ margin:0 0 8px; font-size:15px; }}
    .turnover-card svg {{ width:100%; height:168px; display:block; background:#fbfdff; border:1px solid #e5e7eb; border-radius:8px; cursor:crosshair; }}
    .turnover-note {{ margin-top:7px; color:var(--muted); font-size:12px; line-height:1.45; }}
    .breadth-board {{ border:1px solid var(--line); border-radius:8px; padding:12px; background:#fff; }}
    .breadth-board h3 {{ margin:0 0 10px; font-size:15px; }}
    .breadth-row {{ display:grid; grid-template-columns:72px minmax(0,1fr); gap:10px; align-items:center; padding:9px 0; border-top:1px solid #edf0f4; }}
    .breadth-row:first-of-type {{ border-top:0; padding-top:0; }}
    .breadth-row b {{ font-size:13px; }}
    .breadth-meter {{ height:12px; border-radius:999px; overflow:hidden; background:#e7ecf3; display:flex; }}
    .breadth-meter i {{ display:block; height:100%; }}
    .breadth-meter .rise {{ background:var(--up); width:var(--rise); }}
    .breadth-meter .fall {{ background:var(--down); width:var(--fall); }}
    .breadth-meter .flatbar {{ background:#cbd5e1; width:var(--flatbar); }}
    .breadth-meta {{ display:flex; flex-wrap:wrap; gap:8px 12px; margin-top:6px; color:var(--muted); font-size:12px; }}
    .market-readout {{ margin:0 18px 18px; }}
    .bar-track {{ height:10px; border-radius:999px; background:#e5e7eb; overflow:hidden; display:flex; }}
    .bar-up {{ background:#dc2626; }} .bar-down {{ background:#16a34a; }} .bar-flat {{ background:#9ca3af; }}
    .sector-day {{ display:flex; align-items:center; justify-content:space-between; margin:10px 0; color:#475467; }}
    .sector-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
    .sector-card {{ border:1px solid var(--line); border-radius:8px; padding:12px; background:#fff; }}
    .sector-top {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }}
    .sector-top span {{ font-weight:700; }}
    .sector-card p {{ margin:0 0 8px; color:#475467; font-size:13px; }}
    .sector-card li {{ display:grid; grid-template-columns:92px 1fr 68px; gap:8px; align-items:start; font-size:12px; border-top:1px solid #edf0f4; padding-top:8px; margin-top:8px; }}
    .sector-card em {{ text-align:right; font-style:normal; color:var(--red); }}
    .limit-trend-legend,.filters,.chart-toolbar,.filter-actions,.range-actions {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
    .limit-trend-legend {{ color:var(--muted); font-size:12px; }}
    .limit-trend-legend i {{ display:inline-block; width:16px; height:8px; margin-right:6px; border-radius:999px; vertical-align:middle; }}
    .limit-trend-stat {{ background:#f8fafc; border-radius:8px; padding:12px; min-height:82px; }}
    .limit-trend-stat small {{ display:block; color:var(--muted); margin-bottom:6px; }}
    .limit-trend-stat strong {{ display:block; font-size:24px; line-height:1.1; }}
    .limit-trend-stat span {{ display:block; margin-top:6px; color:var(--muted); font-size:12px; line-height:1.45; }}
    .legend-dot {{ width:10px; height:10px; display:inline-block; border-radius:999px; margin-right:4px; }}
    .chart-wrap {{ display:grid; grid-template-columns:280px minmax(0,1fr); gap:18px; }}
    .chip {{ display:inline-flex; align-items:center; gap:5px; border:1px solid var(--line); border-radius:999px; padding:6px 9px; font-size:12px; background:#fff; cursor:pointer; }}
    button,select {{ border:1px solid var(--line); background:#fff; border-radius:6px; padding:7px 10px; cursor:pointer; }}
    canvas {{ width:100%; height:520px; border:1px solid var(--line); border-radius:8px; background:#fff; }}
    .analysis-block {{ border:1px solid var(--line); border-radius:8px; padding:14px; margin-top:12px; background:#fff; }}
    .analysis-lead {{ margin:8px 0 12px; color:#475467; }}
    .summary-points {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
    .summary-point strong {{ display:block; margin-bottom:5px; }}
    .small {{ color:#667085; font-size:12px; }}
    .muted {{ color:var(--muted); font-size:13px; }}
    .chart-status {{ color:var(--muted); font-size:12px; }}
    .trade-legend i {{ display:inline-grid; place-items:center; width:18px; height:18px; border-radius:999px; margin:0 4px 0 8px; color:#fff; font-style:normal; font-size:11px; }}
    .trade-legend .buy {{ background:var(--red); }}
    .trade-legend .sell {{ background:var(--blue); }}
    @media (max-width:1100px) {{ .grid {{ grid-template-columns:repeat(2,1fr); }} .chart-wrap,.market-layout,.market-side {{ grid-template-columns:1fr; }} .filters {{ border-right:0; border-bottom:1px solid var(--line); padding:0 0 12px; }} .sector-grid,.summary-points {{ grid-template-columns:1fr; }} .detail-metrics,.correlation-grid,.trade-fact-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .limit-trend-stats {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
    @media (max-width:700px) {{ main {{ padding:14px; }} header {{ padding:22px 18px; }} .grid {{ grid-template-columns:1fr; }} table {{ font-size:12px; }} th,td {{ padding:8px 6px; }} canvas {{ height:460px; }} #marketChart,.limit-trend-chart {{ height:320px; }} .market-head,.limit-trend-head,.analysis-head {{ flex-direction:column; align-items:flex-start; }} .market-stats {{ grid-template-columns:1fr; }} .position-summary,.detail-metrics,.correlation-grid,.limit-trend-stats,.trade-fact-grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>2026-06-16 超短复盘</h1>
    <p>严格沿用 6月12 模块顺序；用户采访已补充：关注池、持仓、当日委托、明日计划。生成时间：{esc(generated_at)}</p>
  </header>
  <main>
    <section class="panel market-overview">
      <div class="market-head">
        <div>
          <h2>大盘总览：上证 / 科创60日同图</h2>
          <p>折线以 60日窗口首个可用收盘为 0% 基准，比较上证指数与科创50的阶段强弱。数据截至 {REVIEW_DATE_H} 收盘。</p>
        </div>
      </div>
      <div class="market-layout">
        <div class="market-chart-card">
          <svg id="marketChart" viewBox="0 0 940 340" preserveAspectRatio="none" role="img" aria-label="上证指数与科创50的60日相对涨跌幅折线图"></svg>
          <div class="market-legend"><span><i class="line-sse"></i>上证指数</span><span><i class="line-star"></i>科创50</span><span><i class="line-zero"></i>0%基准线</span></div>
        </div>
        <aside class="market-side">
          <div id="marketStats" class="market-stats"></div>
          <div class="turnover-card">
            <h3>近7日市场活动</h3>
            <svg id="totalTurnoverChart" viewBox="0 0 420 168" preserveAspectRatio="none" role="img" aria-label="近7日市场活动柱状图"></svg>
            <div class="turnover-note">柱状图口径：上证指数日成交量，单位亿股；全A成交额使用公开收评口径写在量能卡片。</div>
          </div>
          <div class="breadth-board">
            <h3>涨跌家数宽度</h3>
            <div class="breadth-row">
              <b>全A</b>
              <div>
                <div class="breadth-meter" style="--rise:{breadth_up_pct:.1f}%;--fall:{breadth_down_pct:.1f}%;--flatbar:{breadth_flat_pct:.1f}%;"><i class="rise"></i><i class="fall"></i><i class="flatbar"></i></div>
                <div class="breadth-meta"><span>上涨 {breadth.get('up') if breadth.get('up') is not None else '-'}</span><span>下跌 {breadth.get('down') if breadth.get('down') is not None else '-'}</span><span>平 {breadth.get('flat') if breadth.get('flat') is not None else '-'}</span></div>
              </div>
            </div>
            <div class="breadth-row">
              <b>情绪</b>
              <div>
                <div class="breadth-meter" style="--rise:{emotion_limit_pct:.1f}%;--fall:{emotion_down_pct:.1f}%;--flatbar:{emotion_open_pct:.1f}%;"><i class="rise"></i><i class="fall"></i><i class="flatbar"></i></div>
                <div class="breadth-meta"><span>涨停 {today['limit_up']['total']}</span><span>炸板 {today['open_limit']['total']}</span><span>跌停 {today['lower_limit']['total']}</span></div>
              </div>
            </div>
          </div>
        </aside>
      </div>
      <div class="readout market-readout"><span><strong>指数强弱：</strong>上证小跌，深成与科创更强，属于深强沪弱。</span><span><strong>量能确认：</strong>{amount_text} 的成交额支持活跃度，但不能单独确认全面转强。</span><span><strong>宽度/情绪：</strong>涨停较昨日减少 {abs(limit_delta)} 家、跌停增加到 {today['lower_limit']['total']} 家，强线还在但后排分化。</span><span><strong>持仓同步：</strong>深桑达 A 同步强，迪生力未同步强，两个持仓应分开处理。</span></div>
    </section>

    <section class="panel">
      <h2>板块强度：今日 vs 昨日</h2>
      <div class="sector-day"><h3>今日 {REVIEW_DATE_H}</h3><span>大类前三：{', '.join(esc(row.get('name')) for row in (kpl_today.get('selected') or [])[:3])}</span></div>
      <div class="sector-grid">{kpl_rows(kpl_today.get('selected') or [], 3)}</div>
      <div class="sector-day"><h3>昨日 {PREV_DATE_H}</h3><span>大类前三：{', '.join(esc(row.get('name')) for row in (kpl_prev.get('selected') or [])[:3])}</span></div>
      <div class="sector-grid">{kpl_rows(kpl_prev.get('selected') or [], 3)}</div>
      <div class="readout" style="margin-top:14px;">对比结论：昨日强度集中在通信/芯片/元器件并由 PCB、CPO、PET 铜箔扩散；今日前排仍是通信、芯片、机器人、算力、元器件，但强度读数从昨日通信 40075 降到今日 {fmt_num(top_kpl.get('strength'),0)}，属于强线延续后的降温，不是新一轮全面扩散。深桑达 A 更接近算力/信创承接，迪生力不在强度前排；金钼、洛钼属于有色备选，只有在盛龙一字带动情绪且低位有助攻时才提高优先级。同花顺涨停板块仅作补充验证，不作为本模块主口径。</div>
    </section>

    <section class="panel limit-trend-panel">
      <div class="limit-trend-head">
        <div>
          <h2>近10日涨停情绪趋势</h2>
          <p>同花顺涨停池、炸板池、跌停池口径；最高连板按涨停池“几天几板”中的板数统计。</p>
        </div>
        <div class="limit-trend-legend"><span><i style="background:#c92a2a"></i>涨停数</span><span><i style="background:#e8590c"></i>炸板数</span><span><i style="background:#087f5b"></i>跌停数</span><span><i style="background:#6f42c1"></i>最高连板</span></div>
      </div>
      <svg id="limitTrendChart" class="limit-trend-chart" viewBox="0 0 1080 380" preserveAspectRatio="none" role="img" aria-label="近10日涨停、炸板、跌停和最高连板趋势"></svg>
      <div id="limitTrendStats" class="limit-trend-stats">
        <div class="limit-trend-stat"><small>今日涨停</small><strong>{today['limit_up']['total']}</strong><span>昨日 {prev['limit_up']['total']}</span></div>
        <div class="limit-trend-stat"><small>今日炸板</small><strong>{today['open_limit']['total']}</strong><span>昨日 {prev['open_limit']['total']}</span></div>
        <div class="limit-trend-stat"><small>今日跌停</small><strong>{today['lower_limit']['total']}</strong><span>昨日 {prev['lower_limit']['total']}</span></div>
        <div class="limit-trend-stat"><small>最高连板</small><strong>{max_board}</strong><span>高标仍能抱团，但尾部风险抬升。</span></div>
      </div>
      <div class="readout">读数：涨停数从 {prev['limit_up']['total']} 降到 {today['limit_up']['total']}，跌停从 {prev['lower_limit']['total']} 增到 {today['lower_limit']['total']}；情绪不是崩盘，但从昨日普涨扩散转为前排抱团和后排分化。</div>
    </section>

    <section class="panel">
      <h2>昨日2板及以上今日反馈</h2>
      <table><thead><tr><th>昨日高度</th><th>标的</th><th>昨日首封</th><th>今日状态</th><th>今日表现</th><th>打板反馈</th></tr></thead><tbody>{feedback_html(feedback)}</tbody></table>
      <div class="readout">样本按 {PREV_DATE_H} 2板及以上筛选：3板及以上全部纳入，2板按首次涨停时间优先。晋级 {feedback_stats['upgrade']}，炸板 {feedback_stats['open']}，跌停 {feedback_stats['down']}，断板 {feedback_stats['broken']}，样本平均涨跌幅 {feedback_stats['avg']:+.2f}%。高标仍有晋级，但后排分化比昨日明显。</div>
    </section>

    <section class="panel">
      <h2>亏钱效应拆解</h2>
      <table><thead><tr><th>亏钱来源</th><th>代表标的 / 数据</th><th>影响</th><th>应对</th></tr></thead><tbody>
        <tr><td>跌停扩散</td><td>{today['lower_limit']['total']} 家，昨日 {prev['lower_limit']['total']} 家</td><td>{loss_line}，说明后排风险抬升，不是全面转强。</td><td>持仓卖点要简单，迪生力不红开优先清仓。</td></tr>
        <tr><td>炸板回撤</td><td>{today['open_limit']['total']} 家，昨日 {prev['open_limit']['total']} 家</td><td>炸板未失控，但涨停减少后，追一致的性价比下降。</td><td>新机会只做承接或回封确认，不追高开一致。</td></tr>
        <tr><td>高标反馈</td><td>最高 {max_board} 板，晋级样本 {feedback_stats['upgrade']} 个</td><td>情绪锚仍有效，盛龙明日一字才有情绪确认意义。</td><td>盛龙只作锚，不直接追；需低位助攻同步。</td></tr>
        <tr><td>持仓分化</td><td>迪生力收盘接近成本，深桑达 A 明显浮盈</td><td>强弱不一致，不能用深桑达的强承接覆盖迪生力风险。</td><td>深桑达按计划看到尾盘；迪生力按红开纪律处理。</td></tr>
      </tbody></table>
      <div class="readout">结论：亏钱效应是相对扩散，不是全面恶化。深桑达的强承接不能替代迪生力的弱承接，两个持仓必须分开处理。</div>
    </section>

    <section class="panel">
      <h2>动态分时图：关注池同图对比</h2>
      <div class="chart-wrap">
        <aside class="filters">
          <div class="filter-actions"><button id="selectAll">全选</button><button id="clearAll">清空</button><button id="focusHeld">只看持仓</button></div>
          <div id="filters"></div>
        </aside>
        <div>
          <div class="chart-toolbar">
            <div class="range-actions"><button id="zoomIn">放大</button><button id="zoomOut">缩小</button><span class="trade-legend"><i class="buy">B</i>买点 <i class="sell">S</i>卖点</span></div>
            <span id="chartStatus" class="chart-status">滚轮缩放，拖动平移；红 B 买入，蓝 S 卖出。</span>
          </div>
          <canvas id="chart" width="1100" height="520"></canvas>
          <div id="tooltip" class="tooltip"></div>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>分时相关性分析</h2>
      <p class="muted" style="margin-top:-6px;">口径：同一分钟涨跌幅序列计算 Pearson 相关；方向同步率统计相邻分钟涨跌方向是否一致。</p>
      <div id="correlationPanel" class="correlation-grid">{correlation_cards(data)}</div>
      <div id="correlationReadout" class="readout">交易解释：明日重点不是找最高相关，而是看深桑达是否能强于指数、盛龙是否作为情绪锚一字稳定、金钼/洛钼是否跟随有色承接。迪生力若不能红开，相关性再好也不应替代清仓纪律。</div>
    </section>

    <section class="panel">
      <h2>关注票池概览</h2>
      <table><thead><tr><th>分组</th><th>标的</th><th>开盘</th><th>最高</th><th>最低</th><th>收盘</th><th>成交额</th><th>备注</th></tr></thead><tbody>{watchlist_html(data)}</tbody></table>
      <div id="focusDetailPanel" class="readout"><label>查看明细：<select id="detailSelect"></select></label><div id="stockDetail" class="detail-metrics"></div></div>
    </section>

    <section class="panel">
      <h2>近期高标多周期涨跌幅统计</h2>
      <table><thead><tr><th>标的</th><th>标签</th><th>昨日涨幅</th><th>今日涨幅</th><th>两日累计</th><th>三日累计</th><th>五日累计</th></tr></thead><tbody>{high_stats_html(data['highStats'])}</tbody></table>
    </section>

    <section class="panel">
      <h2>持仓概览</h2>
      <div class="position-summary">
        <div class="position-card"><small>总资产</small><strong>¥{ACCOUNT['total_assets']:,.2f}</strong><span>截图口径</span></div>
        <div class="position-card"><small>证券市值</small><strong>¥{ACCOUNT['securities_value']:,.2f}</strong><span>仓位 {ACCOUNT['securities_value']/ACCOUNT['total_assets']*100:.2f}%</span></div>
        <div class="position-card"><small>可用现金</small><strong>¥{ACCOUNT['cash']:,.2f}</strong><span>现金 {ACCOUNT['cash']/ACCOUNT['total_assets']*100:.2f}%</span></div>
        <div class="position-card"><small>当日盈亏</small><strong class="up">+¥{ACCOUNT['day_pnl']:,.2f}</strong><span>深桑达贡献主要增量</span></div>
        <div class="position-card"><small>累计/持仓盈亏</small><strong class="up">+¥{ACCOUNT['total_pnl']:,.2f}</strong><span>含香江已卖出盈亏 {ACCOUNT['realized_or_closed_pnl']:+.2f}</span></div>
      </div>
      <table><thead><tr><th>标的</th><th>方向</th><th>数量</th><th>成本价</th><th>现价</th><th>市值</th><th>盈亏</th><th>仓位占比</th></tr></thead><tbody>{holdings_html(data)}</tbody></table>
    </section>

    <section class="panel">
      <h2>昨日计划与操作评分</h2>
      <div class="readout">上一版计划：{esc(previous_plan)} 本次执行评分 {execution_score} / 100；计划内为香江风险处理，计划外为深桑达 A、迪生力新开仓，仓位纪律偏激进。</div>
      <table><thead><tr><th>项目</th><th>本次记录</th><th>后续评分口径</th></tr></thead><tbody>
        <tr><td>昨日计划</td><td>主动核对线为香江控股持仓处理、金钼/洛钼有色强度确认、风华及科技强度确认。</td><td>逐条核对是否来自昨日计划；计划外操作需要单独说明原因。</td></tr>
        <tr><td>今日实际操作</td><td>香江控股卖出符合防守方向；深桑达 A、迪生力新开仓不在上一版主动交易子集。</td><td>计划一致性、触发满足度、仓位纪律、风控执行四项合计 100 分。</td></tr>
        <tr><td>执行评分</td><td>{execution_score} / 100；计划内：香江风险处理；计划外：深桑达、迪生力新开仓。</td><td>后续复盘继续核对是否按“昨日计划”和“AI建议”触发条件执行。</td></tr>
        <tr><td>扣分重点</td><td>两只持仓合计约 {ACCOUNT['securities_value']/ACCOUNT['total_assets']*100:.2f}% 仓位，隔夜暴露偏高；迪生力缺少原始盘口触发说明。</td><td>临盘新仓、仓位超过计划、该止损不止损、用结果盈利倒推买点，都需要扣分。</td></tr>
      </tbody></table>
    </section>

    <section class="panel trade-review">
      <h2>今日操作</h2>
      <div class="trade-fact-grid">
        <div class="trade-fact"><small>第一笔</small><strong>09:30:32</strong><span>买入深桑达 A 200 股，成交 21.340</span></div>
        <div class="trade-fact"><small>第二笔</small><strong>09:30:51</strong><span>卖出香江控股 1300 股，成交 3.710</span></div>
        <div class="trade-fact"><small>第三笔</small><strong>09:38:33</strong><span>买入迪生力 600 股，成交 8.800</span></div>
        <div class="trade-fact"><small>当前持仓</small><strong>深桑达 A / 迪生力</strong><span>总仓位 {ACCOUNT['securities_value']/ACCOUNT['total_assets']*100:.2f}%</span></div>
      </div>
      <div class="readout">操作记录：09:30:32 买入深桑达 A 200 股，成交 21.340；09:30:51 卖出香江控股 1300 股，成交 3.710；09:38:33 买入迪生力 600 股，成交 8.800。结果层面：深桑达浮盈明显，香江卖出有效；迪生力基本打平，明日不能红开则清仓。原始理由层面：深桑达和迪生力盘中理由待补充，香江属于风险处理。</div>
      <div class="analysis-block">
        <div class="analysis-head"><h3>买入归因分析与客观总结</h3><span>题材扩散、核心扰动、个股承接、负反馈修复、分歧风险</span></div>
        <p class="analysis-lead">用户未补充深桑达 A、迪生力的盘中原始买入理由，因此这里只做客观归因，不把结果盈利追认为完全计划内交易。</p>
        <table><thead><tr><th>归因维度</th><th>盘面证据</th><th>客观判断</th></tr></thead><tbody>
          <tr><td>题材扩散</td><td>开盘啦前排仍在通信、芯片、机器人、算力、元器件；深桑达更贴近算力/信创承接，迪生力不在强度前排。</td><td>深桑达可按强承接持有；迪生力不能用主线强度替代个股纪律。</td></tr>
          <tr><td>核心扰动</td><td>盛龙股份今日涨停，是明日情绪锚；金钼股份、洛阳钼业只作为有色备选。</td><td>明日先看盛龙是否一字和低位助攻，再决定是否做金钼/洛钼。</td></tr>
          <tr><td>个股承接</td><td>深桑达 A 收盘涨幅 {fmt_pct(deep['closePct'])}，买入后承接强；迪生力收盘 {fmt_pct(disenli['closePct'])}，强度不足。</td><td>一个按尾盘验证，一个按红开清仓线处理，不能混同。</td></tr>
          <tr><td>负反馈修复</td><td>涨停减少、跌停增加，说明并非全面转强。</td><td>隔夜高仓位要降低幻想，卖出规则比买入规则更简单。</td></tr>
          <tr><td>分歧风险</td><td>当前证券市值占总资产 {ACCOUNT['securities_value']/ACCOUNT['total_assets']*100:.2f}%，且两只新仓均非上一版明确计划。</td><td>明日先处理持仓，再看新机会；不允许因为深桑达盈利而放松迪生力风控。</td></tr>
        </tbody></table>
      </div>
      <div class="analysis-block">
        <div class="analysis-head"><h3>客观总结</h3><span>交易定义与后续验证</span></div>
        <div class="summary-points">
          <div class="summary-point"><strong>交易定义</strong>香江卖出是防守执行；深桑达买入是强承接结果较好的计划外新仓；迪生力买入目前只算试错仓，质量需要明日红开验证。</div>
          <div class="summary-point"><strong>风险定价</strong>深桑达可给到尾盘验证时间，迪生力只看红开与开盘承接；盛龙若一字但低位无助攻，不扩展到金钼/洛钼。</div>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>次日票池留档</h2>
      <table><thead><tr><th>方向</th><th>标的</th><th>今日状态</th><th>关注逻辑</th><th>明日观察点</th></tr></thead><tbody>
        <tr><td>持仓主线</td><td><strong>深桑达 A</strong><span class="code">000032</span></td><td>{fmt_pct(deep['closePct'])}</td><td>今日主要盈利来源，按用户计划持仓到尾盘。</td><td>看能否继续强于指数与算力/信创线；尾盘决定去留。</td></tr>
        <tr><td>持仓风控</td><td><strong>迪生力</strong><span class="code">603335</span></td><td>{fmt_pct(disenli['closePct'])}</td><td>新开仓弱承接样本。</td><td>不能红开则清仓；红开也要看 9:30-9:45 承接。</td></tr>
        <tr><td>情绪锚</td><td><strong>盛龙股份</strong><span class="code">001257</span></td><td>{fmt_pct(shenglong['closePct'])}</td><td>明日一字与低位助攻的情绪确认。</td><td>一字且低位助攻才允许扩大攻击范围。</td></tr>
        <tr><td>有色备选</td><td><strong>金钼股份</strong><span class="code">601958</span> / <strong>洛阳钼业</strong><span class="code">603993</span></td><td>{fmt_pct(jinmu['closePct'])} / {fmt_pct(luomo['closePct'])}</td><td>盛龙情绪确认后的备选方向。</td><td>只做承接/低吸，不追一致高开。</td></tr>
      </tbody></table>
      <div class="readout">完整关注池留档，不等于明日全部可交易。主动交易子集收窄为：深桑达 A、迪生力、盛龙股份、金钼股份、洛阳钼业。</div>
    </section>

    <section class="panel">
      <h2>近3日公告检查</h2>
      <div class="readout">查询窗口：2026-06-14 至 2026-06-16。公告只做风险/催化过滤，最终仍以 6月17日 9:25-9:45 竞价、封单、分时承接确认。</div>
      <table><thead><tr><th>标的</th><th>公告数量</th><th>近3日公告</th><th>利好/利空判断</th></tr></thead><tbody>{announcement_html(data)}</tbody></table>
      <div class="readout">行动结论：若持仓票叠加异动、风险提示、问询或减持类标题，明日先降低预期；无公告也不能替代盘口确认。</div>
    </section>

    <section class="panel">
      <h2>次日计划</h2>
      <div class="readout"><strong>用户计划：</strong>明日看深桑达 A 和盛龙股份；若盛龙一字且低位有助攻，可考虑金钼股份或洛阳钼业。深桑达持仓到尾盘，迪生力不能红开就清仓。</div>
      <table><thead><tr><th>观察线</th><th>重点标的</th><th>竞价信号</th><th>执行动作</th><th>风控说明</th></tr></thead><tbody>
        <tr><td>持仓延续线</td><td><strong>深桑达 A</strong><span class="code">000032</span></td><td>竞价不弱于指数，开盘后能维持强承接，算力/信创方向不明显补跌。</td><td>按计划持仓到尾盘，尾盘根据强弱决定是否继续隔夜。</td><td>若盘中极端破位且板块同步走弱，记录例外风险，不做盘中加仓。</td></tr>
        <tr><td>持仓清仓线</td><td><strong>迪生力</strong><span class="code">603335</span></td><td>不能红开，或红开后 9:30-9:45 快速跌回水下且无承接。</td><td><span class="down">清仓</span></td><td>这是最明确的卖出规则，不用题材解释覆盖。</td></tr>
        <tr><td>情绪确认线</td><td><strong>盛龙股份</strong><span class="code">001257</span></td><td>一字或接近一字，封单稳定，低位同方向有助攻。</td><td>只作为情绪锚，不追高硬做。</td><td>若盛龙开板走弱或低位无助攻，取消扩展交易。</td></tr>
        <tr><td>有色备选线</td><td><strong>金钼股份</strong><span class="code">601958</span> / <strong>洛阳钼业</strong><span class="code">603993</span></td><td>盛龙确认情绪强，且金钼/洛钼竞价强于指数、有分时均线承接。</td><td>考虑低吸或回封确认，优先容量承接更清晰的一只。</td><td>不追一致高开；单笔仓位需小于今日持仓主仓。</td></tr>
        <tr><td>忽略线</td><td>香江控股及其他旧高标</td><td>除非重新进入强度前排且有明确盘口。</td><td>只留档，不主动交易。</td><td>避免从两个持仓发散到全市场。</td></tr>
      </tbody></table>
    </section>

    <section class="panel">
      <h2>AI建议</h2>
      <div class="readout">AI 对用户计划的收紧：深桑达“持仓到尾盘”可以执行，但不能演变成无条件硬扛；迪生力的卖出规则最清晰，应优先执行。新机会必须排在持仓处理之后。</div>
      <table><thead><tr><th>场景</th><th>触发条件</th><th>执行动作</th><th>明日复盘核对</th></tr></thead><tbody>
        <tr><td>竞价定性</td><td>9:25 先看深桑达 A、迪生力、盛龙股份，再看金钼/洛钼。</td><td>先处理持仓，不因盛龙一字直接扩仓。</td><td>是否按顺序看盘，是否先卖弱后买强。</td></tr>
        <tr><td>深桑达持仓</td><td>开盘不弱，盘中维持均线上方或回落后能收回。</td><td>持有到尾盘；尾盘再决定隔夜。</td><td>是否遵守“尾盘决策”，是否盘中追涨加仓。</td></tr>
        <tr><td>迪生力清仓</td><td>不能红开，或红开失败后跌回水下。</td><td><span class="down">直接清仓</span>，不等待解释。</td><td>是否执行最简单的卖出纪律。</td></tr>
        <tr><td>盛龙一字</td><td>封单稳定，低位同方向助攻，市场跌停不扩散。</td><td>只把它作为情绪确认，再评估金钼/洛钼承接。</td><td>是否确认低位助攻，而不是只看一字。</td></tr>
        <tr><td>金钼/洛钼参与</td><td>资源线强于指数，回踩均线不破或分歧后回封。</td><td>小仓低吸/确认，不追高。</td><td>是否满足盛龙和资源线双条件。</td></tr>
        <tr><td>空仓优先</td><td>深桑达走弱、迪生力弱开、盛龙开板、跌停扩散。</td><td>清弱留强或降仓，不开新仓。</td><td>是否避免用新交易掩盖持仓风险。</td></tr>
      </tbody></table>
      <div class="readout">明日复盘核对：深桑达是否真的持到尾盘；迪生力若不红开是否清仓；盛龙是否一字且低位有助攻；金钼/洛钼是否只在承接条件满足后参与。</div>
    </section>
  </main>
  <script>
    const payload = {payload_json};
    function cls(v) {{ return v > 0 ? 'up' : v < 0 ? 'down' : 'flat'; }}
    function fmtPct(v) {{ return v == null ? '-' : `<span class="${{cls(v)}}">${{v >= 0 ? '+' : ''}}${{v.toFixed(2)}}%</span>`; }}
    function signed(v) {{ return v == null ? '-' : `${{v >= 0 ? '+' : ''}}${{Number(v).toFixed(2)}}%`; }}
    function setupMarketOverview() {{
      const chart = document.getElementById('marketChart');
      const stats = document.getElementById('marketStats');
      if (!chart || !stats) return;
      const rows = payload.indexChart.series?.[0]?.points?.map((point, i) => ({{
        date: point.date.slice(5),
        sse: point.value,
        star: payload.indexChart.series?.[1]?.points?.[i]?.value ?? 0,
      }})) || [];
      const w = 940, h = 340;
      const m = {{ left:58, right:28, top:22, bottom:34 }};
      const plotW = w - m.left - m.right;
      const plotH = h - m.top - m.bottom;
      const values = rows.flatMap(r => [r.sse, r.star, 0]);
      const minValue = Math.min(...values);
      const maxValue = Math.max(...values);
      const pad = Math.max(2, (maxValue - minValue) * 0.08);
      const minY = Math.floor((minValue - pad) / 5) * 5;
      const maxY = Math.ceil((maxValue + pad) / 5) * 5;
      const x = i => m.left + i / Math.max(1, rows.length - 1) * plotW;
      const y = value => m.top + (maxY - value) / Math.max(1, maxY - minY) * plotH;
      const pathFor = key => rows.map((r, i) => `${{i ? 'L' : 'M'}}${{x(i).toFixed(1)}},${{y(r[key]).toFixed(1)}}`).join(' ');
      let out = `<rect x="${{m.left}}" y="${{m.top}}" width="${{plotW}}" height="${{plotH}}" fill="#fbfdff" stroke="#cbd5e1" />`;
      const step = Math.max(5, Math.ceil((maxY - minY) / 6 / 5) * 5);
      for (let value = Math.ceil(minY / step) * step; value <= maxY; value += step) {{
        const yy = y(value);
        const isZero = Math.abs(value) < 0.001;
        out += `<line x1="${{m.left}}" y1="${{yy}}" x2="${{w-m.right}}" y2="${{yy}}" stroke="${{isZero ? '#94a3b8' : '#e5e7eb'}}" stroke-width="${{isZero ? 1.4 : 1}}" stroke-dasharray="${{isZero ? '5 4' : '0'}}" />`;
        out += `<text x="${{m.left-8}}" y="${{yy+4}}" text-anchor="end" font-size="11" fill="#64748b">${{value > 0 ? '+' : ''}}${{value}}%</text>`;
      }}
      [0, 14, 29, 44, rows.length - 1].filter((v, i, arr) => v >= 0 && v < rows.length && arr.indexOf(v) === i).forEach(i => {{
        const xx = x(i);
        out += `<line x1="${{xx}}" y1="${{m.top}}" x2="${{xx}}" y2="${{h-m.bottom}}" stroke="#edf2f7" />`;
        out += `<text x="${{xx}}" y="${{h-12}}" text-anchor="middle" font-size="11" fill="#64748b">${{rows[i].date}}</text>`;
      }});
      out += `<path d="${{pathFor('sse')}}" fill="none" stroke="#1c5d99" stroke-width="2.4" vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round" />`;
      out += `<path d="${{pathFor('star')}}" fill="none" stroke="#c92a2a" stroke-width="2.4" vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round" />`;
      out += `<text x="${{m.left}}" y="16" font-size="12" font-weight="700" fill="#334155">60日相对涨跌幅</text>`;
      out += `<text x="${{w-m.right}}" y="16" text-anchor="end" font-size="11" fill="#64748b">${{rows[0]?.date || ''}} 至 ${{rows.at(-1)?.date || ''}}</text>`;
      chart.innerHTML = out;
      stats.innerHTML = payload.marketStats.map(item => `
        <div class="market-stat"><small>${{item.label}}</small><strong>${{item.value}}</strong><span>${{item.sub}}</span></div>
      `).join('');
    }}
    function setupTotalTurnoverChart() {{
      const chart = document.getElementById('totalTurnoverChart');
      if (!chart) return;
      const rows = payload.indexChart.amountBars || [];
      const w = 420, h = 168;
      const m = {{ left:42, right:14, top:16, bottom:28 }};
      const pw = w - m.left - m.right;
      const ph = h - m.top - m.bottom;
      const maxA = Math.max(...rows.map(r => r.amountYi || 0), 1) * 1.08;
      const x = i => m.left + (i + .5) / Math.max(1, rows.length) * pw;
      const y = value => m.top + (maxA - value) / maxA * ph;
      const barW = Math.max(18, pw / Math.max(1, rows.length) * .52);
      let out = `<rect x="${{m.left}}" y="${{m.top}}" width="${{pw}}" height="${{ph}}" fill="#fbfdff" stroke="#e5e7eb" />`;
      [0, maxA / 2, maxA].forEach((value, idx) => {{
        const yy = y(value);
        out += `<line x1="${{m.left}}" y1="${{yy}}" x2="${{w-m.right}}" y2="${{yy}}" stroke="#e5e7eb" />`;
        if (idx > 0) out += `<text x="${{m.left-6}}" y="${{yy+4}}" text-anchor="end" font-size="10" fill="#64748b">${{value.toFixed(0)}}</text>`;
      }});
      rows.forEach((r, i) => {{
        const xx = x(i);
        const yy = y(r.amountYi || 0);
        const bh = m.top + ph - yy;
        const fill = i === rows.length - 1 ? '#c92a2a' : '#94a3b8';
        out += `<rect x="${{xx-barW/2}}" y="${{yy}}" width="${{barW}}" height="${{bh}}" rx="3" fill="${{fill}}" opacity=".82" />`;
        out += `<text x="${{xx}}" y="${{h-9}}" text-anchor="middle" font-size="10" fill="#64748b">${{r.date}}</text>`;
      }});
      out += `<text x="${{m.left}}" y="11" font-size="11" font-weight="700" fill="#334155">指数成交量</text>`;
      chart.innerHTML = out;
    }}
    function setupLimitTrendChart() {{
      const series = [
        {{ name:'涨停', color:'#b42318', key:'limitUp' }},
        {{ name:'炸板', color:'#f59e0b', key:'openLimit' }},
        {{ name:'跌停', color:'#087443', key:'lowerLimit' }},
        {{ name:'最高连板', color:'#7c3aed', key:'maxBoard' }},
      ];
      const el = document.getElementById('limitTrendChart');
      const w = 1080, h = 380, pad = 44;
      const all = series.flatMap(s => payload.emotion.map(p => p[s.key]));
      const max = Math.max(...all, 1);
      const x = i => pad + i / Math.max(1, payload.emotion.length - 1) * (w - pad * 2);
      const y = v => h - pad - v / max * (h - pad * 2);
      const paths = series.map((s, idx) => {{
        const d = payload.emotion.map((p,i) => `${{i ? 'L' : 'M'}}${{x(i).toFixed(1)}},${{y(p[s.key]).toFixed(1)}}`).join(' ');
        return `<path d="${{d}}" fill="none" stroke="${{s.color}}" stroke-width="2"/><text x="${{pad + idx*120}}" y="20" fill="${{s.color}}" font-size="12">${{s.name}}</text>`;
      }}).join('');
      const labels = payload.emotion.map((p,i) => `<text x="${{x(i)-18}}" y="${{h-8}}" font-size="10" fill="#667085">${{p.date.slice(5)}}</text>`).join('');
      el.setAttribute('viewBox', `0 0 ${{w}} ${{h}}`);
      el.innerHTML = `<line x1="${{pad}}" y1="${{h-pad}}" x2="${{w-pad}}" y2="${{h-pad}}" stroke="#cbd5e1"/>${{paths}}${{labels}}`;
    }}
    const canvas = document.getElementById('chart');
    const ctx = canvas.getContext('2d');
    const state = {{ start:0, end:240, dragging:false, lastX:0, selected:new Map() }};
    function setupFilters() {{
      const box = document.getElementById('filters');
      payload.intradaySeries.forEach(s => state.selected.set(s.code, !!s.active));
      box.innerHTML = payload.intradaySeries.map(s => `<label class="chip"><input type="checkbox" data-code="${{s.code}}" ${{s.active?'checked':''}}> <span style="color:${{s.color}}">${{s.name}}</span></label>`).join('');
      box.querySelectorAll('input').forEach(i => i.onchange = () => {{ state.selected.set(i.dataset.code, i.checked); drawIntraday(); }});
      document.getElementById('focusHeld').onclick = () => {{ box.querySelectorAll('input').forEach(i => {{ const keep = ['000032','603335'].includes(i.dataset.code); i.checked = keep; state.selected.set(i.dataset.code, keep); }}); drawIntraday(); }};
      document.getElementById('selectAll').onclick = () => {{ box.querySelectorAll('input').forEach(i => {{ i.checked = true; state.selected.set(i.dataset.code, true); }}); drawIntraday(); }};
      document.getElementById('clearAll').onclick = () => {{ box.querySelectorAll('input').forEach(i => {{ i.checked = false; state.selected.set(i.dataset.code, false); }}); drawIntraday(); }};
      document.getElementById('zoomIn').onclick = () => zoomIntraday(0.75);
      document.getElementById('zoomOut').onclick = () => zoomIntraday(1.25);
    }}
    function zoomIntraday(factor) {{
      const mid = (state.start + state.end) / 2, width = state.end - state.start;
      const next = Math.max(30, Math.min(240, width * factor));
      state.start = Math.max(0, Math.round(mid - next/2)); state.end = Math.min(240, Math.round(mid + next/2)); drawIntraday();
    }}
    function selectedSeries() {{ return payload.intradaySeries.filter(s => state.selected.get(s.code) && s.points.length); }}
    function drawIntraday() {{
      const w = canvas.width, h = canvas.height, pad = 44;
      ctx.clearRect(0,0,w,h); ctx.fillStyle = '#fff'; ctx.fillRect(0,0,w,h);
      const series = selectedSeries();
      const vals = series.flatMap(s => s.points.slice(state.start,state.end+1).map(p => p.pct).filter(v => v != null));
      if (!vals.length) {{ ctx.fillStyle='#667085'; ctx.fillText('请选择标的', 40, 40); return; }}
      const status = document.getElementById('chartStatus');
      if (status) status.textContent = `显示 ${{series.length}} 条曲线，区间 ${{state.start}}-${{state.end}} 分钟；滚轮缩放，拖动平移。`;
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
        payload.trades.filter(t => t.code === s.code).forEach(t => {{
          const idx = s.points.findIndex(p => p.time === t.time);
          if (idx < state.start || idx > state.end || idx < 0) return;
          const p = s.points[idx]; const xx = x(idx), yy = y(p.pct);
          ctx.fillStyle = t.side === 'B' ? '#b42318' : '#1d4ed8';
          ctx.beginPath(); ctx.arc(xx, yy, 9, 0, Math.PI*2); ctx.fill();
          ctx.fillStyle = '#fff'; ctx.font='bold 11px Arial'; ctx.fillText(t.side, xx-3.5, yy+4);
        }});
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
      const width = state.end-state.start;
      const shift = Math.round(-dx / canvas.clientWidth * width);
      state.start = Math.max(0, Math.min(240-width, state.start + shift));
      state.end = Math.min(240, state.start + width);
      drawIntraday();
    }});
    function setupDetails() {{
      const select = document.getElementById('detailSelect');
      select.innerHTML = Object.values(payload.stockDetails).map(d => `<option value="${{d.code}}" ${{d.code==='000032'?'selected':''}}>${{d.name}} ${{d.code}}</option>`).join('');
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
    window.addEventListener('resize', () => {{ setupMarketOverview(); setupTotalTurnoverChart(); setupLimitTrendChart(); drawIntraday(); }});
    setupFilters(); setupDetails(); setupMarketOverview(); setupTotalTurnoverChart(); setupLimitTrendChart(); drawIntraday();
  </script>
</body>
</html>
"""


def write_summary_files(data: dict) -> None:
    summary = {
        "review_date": REVIEW_DATE,
        "prev_date": PREV_DATE,
        "counts": {
            "limit_up": data["todayPools"]["limit_up"]["total"],
            "open_limit": data["todayPools"]["open_limit"]["total"],
            "lower_limit": data["todayPools"]["lower_limit"]["total"],
            "breadth_up": data["breadth"].get("up"),
            "breadth_down": data["breadth"].get("down"),
            "amount_yi": data["breadth"].get("amount_yi"),
        },
        "kpl_top": (data["kpl"][REVIEW_DATE_H]["groups"].get("selected") or [])[:10],
        "watchlist": data["stockDetails"],
        "feedback": data["feedbackRows"],
        "announcements": data["announcements"],
        "trades": TRADES,
        "holdings": HOLDINGS,
    }
    (ROOT / "market_review_20260616_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "breadth_20260616.json").write_text(json.dumps(data["breadth"], ensure_ascii=False, indent=2), encoding="utf-8")
    index_snapshot = {
        code: {"name": INDEXES[code]["name"], "last_60": value["rows"][-60:]}
        for code, value in data["indexes"]["daily"].items()
    }
    (ROOT / "index_20260616.json").write_text(json.dumps(index_snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    with (ROOT / "limit_pools_20260616.csv").open("w", encoding="utf-8-sig", newline="") as f:
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
  <meta http-equiv="refresh" content="0; url=review_20260616.html">
  <title>2026-06-16 复盘</title>
  <style>
    body { margin:0; min-height:100vh; display:grid; place-items:center; font-family:Arial,"Microsoft YaHei",sans-serif; color:#1f2937; background:#f6f8fb; }
    a { color:#1d4ed8; }
  </style>
</head>
<body>
  <p>正在打开复盘页面，若未自动跳转，点击 <a href="review_20260616.html">review_20260616.html</a>。</p>
</body>
</html>
"""
    (ROOT / "index.html").write_text(html_text, encoding="utf-8")


def main() -> None:
    data = build_data()
    write_summary_files(data)
    html_text = render_html(data)
    (ROOT / "review_20260616.html").write_text(html_text, encoding="utf-8")
    update_index()
    print("generated review_20260616.html")


if __name__ == "__main__":
    main()
