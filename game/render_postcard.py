#!/usr/bin/env python3
"""『おさんぽ絵はがき』Step C レンダラ v0.2

postcard.json (Step B) + scene 画像 → postcard.png（絵はがき）。
描画前に2つの検証を行う:
  1. 事実照合: postcard.json の発見・絵はがき場面・ハッシュが walk_draft.json と一致すること
  2. プライバシー検疫: setup.json の private_owner_names が postcard.json の全文に含まれないこと
どちらかで失敗したら描画せず終了コード2で止まる。
"""
import glob
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1260, 944
BG = (255, 248, 236)
INK = (58, 44, 32)
SUB = (122, 102, 82)
ACCENT = (196, 82, 46)


def font(size, bold=False):
    pats = ["/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc" % ("Bold" if bold else "Regular"),
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-%s.ttc" % ("Bold" if bold else "Regular")]
    for p in pats:
        hits = glob.glob(p)
        if hits:
            return ImageFont.truetype(hits[0], size, index=0)
    return ImageFont.load_default()


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if draw.textlength(cur + ch, font=fnt) > max_w and cur:
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def main():
    run_dir = sys.argv[1]
    pc_path = os.path.join(run_dir, "postcard.json")
    draft_path = os.path.join(run_dir, "walk_draft.json")
    setup_path = os.path.join(run_dir, "setup.json")
    scene_path = next((os.path.join(run_dir, s) for s in ("scene.webp", "scene.png", "scene.jpg")
                       if os.path.exists(os.path.join(run_dir, s))), None)
    if not scene_path:
        print("error: scene image not found in run dir"); sys.exit(2)
    pc = json.load(open(pc_path, encoding="utf-8"))
    draft = json.load(open(draft_path, encoding="utf-8"))
    setup = json.load(open(setup_path, encoding="utf-8"))

    # 1. 事実照合 (Step B が事実を書き換えていないか)
    if pc["verification"]["log_hash"] != draft["verification"]["log_hash"]:
        print("error: log_hash mismatch vs walk_draft.json"); sys.exit(2)
    if [d["item"] for d in pc["discoveries"]] != [d["item"] for d in draft["discoveries"]]:
        print("error: discoveries mismatch vs walk_draft.json"); sys.exit(2)
    if pc["postcard_spot"]["event_id"] != draft["postcard_spot"]["event_id"]:
        print("error: postcard_spot mismatch vs walk_draft.json"); sys.exit(2)
    # 2. プライバシー検疫 (2回目: 描画直前)
    raw = open(pc_path, encoding="utf-8").read()
    for name in setup.get("private_owner_names", []):
        if name and name in raw:
            print(f"error: private name found in postcard.json (blocked)"); sys.exit(2)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([14, 14, W - 14, H - 14], outline=ACCENT, width=3)

    scene = Image.open(scene_path).convert("RGB")
    sw, sh = 1180, 470
    scale = max(sw / scene.width, sh / scene.height)
    scene = scene.resize((int(scene.width * scale) + 1, int(scene.height * scale) + 1))
    x0 = (scene.width - sw) // 2; y0 = 0  # 上寄せクロップ（耳を切らない）
    img.paste(scene.crop((x0, y0, x0 + sw, y0 + sh)), (40, 36))
    d.rectangle([40, 36, 40 + sw, 36 + sh], outline=(255, 255, 255), width=4)

    t = pc["postcard_text"]
    y = 526
    d.text((44, y), t["headline"], font=font(37, bold=True), fill=INK); y += 52
    for ln in wrap(d, t["body"], font(21), 740):
        d.text((44, y), ln, font=font(21), fill=INK); y += 30
    y += 4
    for ln in wrap(d, t["to_master"], font(19), 740):
        d.text((44, y), ln, font=font(19), fill=SUB); y += 27

    rx = 824
    d.text((rx, 526), "今日の発見", font=font(23, bold=True), fill=ACCENT)
    ry = 562
    for disc in pc["discoveries"]:
        mark = "★" if disc.get("theme_hit") else "・"
        label = f"{mark} {disc['item']}"
        if disc.get("rare"):
            label += " ✨"
        d.text((rx, ry), label, font=font(19), fill=INK); ry += 28
    m = pc["metrics"]
    d.text((rx, ry + 6), f"発見 {m['discoveries']} ／ お題 {m['theme_discoveries']} ／ 疲れ {m['final_fatigue']}",
           font=font(18), fill=SUB)

    d.line([40, 842, W - 40, 842], fill=SUB, width=1)
    ch = pc["challenge"]
    d.text((44, 852), f"お題「{ch['theme']}」 seed {ch['seed']} ／ log {pc['verification']['log_hash']}",
           font=font(16), fill=SUB)
    prod = pc["credit"]["production"]
    d.text((W - 44 - d.textlength(prod, font=font(15)), 852), prod, font=font(15), fill=SUB)
    credit = "Special Thanks: " + pc["credit"]["text"].replace("Special Thanks: ", "")
    cy = 878
    for ln in wrap(d, credit, font(13), W - 88):
        d.text((44, cy), ln, font=font(13), fill=SUB); cy += 19

    out_path = os.path.join(run_dir, "postcard.png")
    img.save(out_path)
    print(json.dumps({"ok": True, "postcard": os.path.abspath(out_path),
                      "checks": ["facts_vs_draft: ok", "privacy_scan: ok"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
