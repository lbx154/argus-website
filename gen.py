#!/usr/bin/env python3
"""Generate a self-contained, Chinese blue-white invent-run dashboard.

Reads live state from the nanochat invent-run daemon + project and writes a
single self-contained index.html (data embedded, meta-refresh for liveness).
"""
from __future__ import annotations
import csv, glob, json, os, re, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

PROJ = Path("/home/xinjiezhang/zimo/argus-nanochat-attack")
LIFE = Path("/home/xinjiezhang/.argus-skill/projects/5ffdfcb3df60")
OUT = Path("/home/xinjiezhang/zimo/invent_dash/index.html")

FLOOR = 0.994157          # measured 438a26e on our H100 (seed42)
FLOOR_10S = 0.989         # 10-seed port mean
TARGETS = [               # (label, val, note)
    ("当前最好公开 (H100)", 0.969686, "要超的对象"),
    ("quasar 调参移植", 0.9644, "上一阶段，非发明"),
    ("Recursive 真前沿 (B200)", 0.9109, "禁区，不可直接比"),
]

def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=15).stdout.strip()
    except Exception:
        return ""

def read_events(n=14):
    evs = []
    try:
        lines = LIFE.joinpath("events.jsonl").read_text().splitlines()
        for l in lines[-400:]:
            try:
                d = json.loads(l)
                t = d.get("type", "")
                if t in ("engineer.progress","life.planner.start","life.planner.error",
                         "life.reviewer.start","life.status","life.inbox.queued"):
                    txt = (d.get("error") or d.get("text") or d.get("reason") or d.get("title") or "")
                    evs.append((d.get("ts"), t, txt))
            except Exception:
                pass
    except Exception:
        pass
    return evs[-n:]

def daemon_vitals():
    v = {"alive": False, "cost": 0.0, "seq": "?", "mission": "?"}
    try:
        st = sh("/home/xinjiezhang/zimo/argus-nanochat-attack/.venv/bin/python -m argus_skill --status --project-root /home/xinjiezhang/zimo/argus-nanochat-attack")
        v["alive"] = "alive" in st
        m = re.search(r"cost\s*:\s*\$([\d.]+)", st);  v["cost"] = float(m.group(1)) if m else 0.0
        m = re.search(r"seq (\d+)", st);  v["seq"] = m.group(1) if m else "?"
        m = re.search(r"mission ([\dhm ]+s)", st);  v["mission"] = m.group(1).strip() if m else "?"
    except Exception:
        pass
    return v

def attempts():
    rows = []
    for d in sorted(glob.glob(str(PROJ / "attempts" / "h100_438a26e_*"))):
        name = os.path.basename(d)
        if name.endswith("floor_profilebase"):
            mech, kind = "地板 profile 基线", "base"
        else:
            mech = name.replace("h100_438a26e_", "")
            kind = "invent"
        mean = None; n = 0
        csvp = os.path.join(d, "results.csv")
        if os.path.exists(csvp):
            try:
                vals = [float(r["val_bpb"]) for r in csv.DictReader(open(csvp)) if r.get("val_bpb")]
                if vals: mean = sum(vals)/len(vals); n = len(vals)
            except Exception:
                pass
        # status hint from CHANGES.md / smoke logs
        status = "测出 %d-seed 均值 %.4f" % (n, mean) if mean else "调试/smoke 中"
        rows.append((mech, kind, mean, n, status))
    return rows

def gpu1():
    out = sh("nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader")
    for line in out.splitlines():
        if line.strip().startswith("1"):
            return line.strip()
    return "?"

def fmt_ago(ts):
    if not ts: return ""
    try:
        d = time.time() - float(ts)
        if d < 60: return f"{int(d)}秒前"
        if d < 3600: return f"{int(d/60)}分前"
        return f"{int(d/3600)}时前"
    except Exception:
        return ""

def esc(s):
    return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def build():
    v = daemon_vitals(); evs = read_events(); atts = attempts(); g = gpu1()
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    best = min([m for _,_,m,_,_ in atts if m], default=None)

    # scale for the race bar: 0.91 (frontier) .. 1.00 (floor-ish)
    lo, hi = 0.905, 1.00
    def pct(x): return max(0, min(100, (hi - x)/(hi-lo)*100))

    target_marks = "".join(
        f'<div class="mark" style="left:{pct(val):.1f}%"><span class="dot"></span>'
        f'<div class="lbl">{esc(lab)}<b>{val:.4f}</b><i>{esc(note)}</i></div></div>'
        for lab,val,note in TARGETS)
    floor_mark = (f'<div class="mark floor" style="left:{pct(FLOOR):.1f}%"><span class="dot"></span>'
                  f'<div class="lbl">合法地板 (H100)<b>{FLOOR:.4f}</b><i>起点</i></div></div>')
    best_mark = ""
    if best:
        best_mark = (f'<div class="mark best" style="left:{pct(best):.1f}%"><span class="dot"></span>'
                     f'<div class="lbl up">argus 当前最好<b>{best:.4f}</b><i>实测</i></div></div>')

    att_cards = ""
    for mech, kind, mean, n, status in atts:
        cls = "card base" if kind == "base" else ("card win" if (mean and mean < FLOOR) else "card")
        val = f'<span class="v">{mean:.4f}</span><span class="vn">×{n} seed</span>' if mean else '<span class="v dim">—</span>'
        att_cards += (f'<div class="{cls}"><div class="m">{esc(mech)}</div>{val}'
                      f'<div class="s">{esc(status)}</div></div>')
    if not att_cards:
        att_cards = '<div class="card"><div class="m">尚无 invent attempt</div></div>'

    feed = ""
    for ts, t, txt in reversed(evs):
        short = esc(txt[:150])
        tag = {"engineer.progress":"工程","life.planner.start":"规划","life.planner.error":"规划✗",
               "life.reviewer.start":"评审","life.status":"状态","life.inbox.queued":"收件"}.get(t, t)
        feed += f'<div class="ev"><span class="t">{tag}</span><span class="a">{fmt_ago(ts)}</span><span class="x">{short}</span></div>'

    status_pill = '<span class="pill on">● 运行中</span>' if v["alive"] else '<span class="pill off">● 已停止</span>'

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>Argus 发明实验 · nanochat 5分钟</title>
<style>
 :root{{--blue:#2f6df0;--blue2:#5b8def;--ink:#10243e;--mut:#5a708f;--line:#e3ecfa;--bg:#f5f9ff;--win:#10b981;}}
 *{{box-sizing:border-box}}
 body{{margin:0;font-family:'Noto Sans SC',system-ui,sans-serif;background:var(--bg);color:var(--ink);}}
 .wrap{{max-width:960px;margin:0 auto;padding:24px 18px 60px}}
 h1{{font-size:20px;margin:0 0 2px;display:flex;align-items:center;gap:10px}}
 .sub{{color:var(--mut);font-size:13px;margin-bottom:18px}}
 .pill{{font-size:12px;padding:3px 10px;border-radius:20px;font-weight:600}}
 .pill.on{{background:#e6f7ef;color:var(--win)}} .pill.off{{background:#fdeaea;color:#e0564a}}
 .vit{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:22px}}
 .vit .b{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 14px;flex:1;min-width:120px}}
 .vit .b .k{{font-size:11px;color:var(--mut)}} .vit .b .val{{font-size:18px;font-weight:700;margin-top:3px}}
 .panel{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px;margin-bottom:18px;box-shadow:0 1px 3px rgba(47,109,240,.04)}}
 .panel h2{{font-size:14px;margin:0 0 18px;color:var(--blue);font-weight:700;letter-spacing:.3px}}
 .track{{position:relative;height:120px;margin:38px 8px 70px}}
 .rail{{position:absolute;top:50px;left:0;right:0;height:8px;border-radius:8px;
   background:linear-gradient(90deg,#10b981,#5b8def 55%,#cdd9ef)}}
 .mark{{position:absolute;top:50px;transform:translateX(-50%)}}
 .mark .dot{{display:block;width:14px;height:14px;border-radius:50%;background:var(--blue);border:3px solid #fff;
   box-shadow:0 0 0 1px var(--blue);margin:-3px auto 0}}
 .mark.floor .dot{{background:#94a8c6;box-shadow:0 0 0 1px #94a8c6}}
 .mark.best .dot{{background:var(--win);box-shadow:0 0 0 1px var(--win);width:18px;height:18px}}
 .mark .lbl{{position:absolute;top:18px;left:50%;transform:translateX(-50%);text-align:center;width:130px;font-size:11px;color:var(--mut)}}
 .mark .lbl b{{display:block;font-size:15px;color:var(--ink);margin:2px 0}}
 .mark .lbl i{{font-style:normal;font-size:10px;color:#9ab}}
 .mark .lbl.up{{color:var(--win)}} .mark .lbl.up b{{color:var(--win)}}
 .mark.floor .lbl,.mark:nth-child(2) .lbl{{top:-52px}}
 .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px}}
 .card{{border:1px solid var(--line);border-radius:12px;padding:14px;background:#fbfdff}}
 .card.base{{opacity:.7}} .card.win{{border-color:var(--win);background:#f0fdf8}}
 .card .m{{font-size:13px;font-weight:600;margin-bottom:6px}}
 .card .v{{font-size:22px;font-weight:800;color:var(--blue)}} .card.win .v{{color:var(--win)}}
 .card .v.dim{{color:#c2cee0;font-weight:600}}
 .card .vn{{font-size:11px;color:var(--mut);margin-left:6px}}
 .card .s{{font-size:11px;color:var(--mut);margin-top:8px}}
 .ev{{display:flex;gap:10px;align-items:baseline;padding:7px 0;border-top:1px solid #f0f5fd;font-size:12px}}
 .ev .t{{flex:0 0 42px;color:var(--blue);font-weight:600}}
 .ev .a{{flex:0 0 48px;color:#9ab;font-size:11px}}
 .ev .x{{color:#374e6b;font-family:ui-monospace,monospace;font-size:11px;word-break:break-all}}
 .foot{{text-align:center;color:#9ab;font-size:11px;margin-top:24px}}
 .note{{background:#eef4ff;border-left:3px solid var(--blue);padding:10px 14px;border-radius:8px;font-size:12px;color:#33507a;margin-top:14px}}
</style></head><body><div class="wrap">
 <h1>🧪 Argus 发明实验 {status_pill}</h1>
 <div class="sub">nanochat 5 分钟预训练 · 单卡 H100 · val&nbsp;BPB（越低越好）· 从合法地板 438a26e 起，禁读答案，逼真发明</div>

 <div class="vit">
   <div class="b"><div class="k">守护进程</div><div class="val">{'运行' if v['alive'] else '停止'}</div></div>
   <div class="b"><div class="k">本轮已花</div><div class="val">${v['cost']:.2f}</div></div>
   <div class="b"><div class="k">循环 seq</div><div class="val">{v['seq']}</div></div>
   <div class="b"><div class="k">GPU1 状态</div><div class="val" style="font-size:13px">{esc(g)}</div></div>
 </div>

 <div class="panel"><h2>赛道 · 地板 → 目标</h2>
  <div class="track"><div class="rail"></div>{floor_mark}{target_marks}{best_mark}</div>
  <div class="note">绿点是 argus 自己实测的最好成绩；灰点是合法起点（地板）；蓝点是要超越的公开/前沿目标。
  目标：用<b>自创的结构级机制</b>把成绩从地板往左推，<b>不许</b>读 0.9109 答案或抄 quasar。</div>
 </div>

 <div class="panel"><h2>发明尝试（全部从 438a26e 地板派生）</h2>
  <div class="cards">{att_cards}</div>
 </div>

 <div class="panel"><h2>实时活动</h2>{feed}</div>

 <div class="foot">生成于 {now} · 每 30 秒自动刷新 · life_dir 5ffdfcb3df60</div>
</div></body></html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print("wrote", OUT, "best=", best, "attempts=", len(atts))

if __name__ == "__main__":
    build()
