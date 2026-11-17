#!/usr/bin/env python3
"""Tìm B-roll THẬT (ảnh/video chân thực) cho một ý trong lời nói, tải về và làm bảng xem để chọn.

  python3 tim_broll.py "<từ khoá 1>|<từ khoá 2>" <thu_muc_ra> [--n 8] [--nguon may,commons,openverse,pexels] [--video]

Nguồn, theo thứ tự ưu tiên:
  may       — ảnh/video sẵn có trong thư mục của người dùng (khoá thu_muc_anh trong ~/.lbvid03/cau_hinh.json) — khớp tên file
  commons   — Wikimedia Commons: ảnh thật địa danh, công trình, sự kiện (CC BY / BY-SA / PD) — có cả video .webm
  openverse — kho ảnh giấy phép mở (Flickr…), lọc ảnh ≥ 1000px
  pexels    — video/ảnh stock chân thực cho ý chung (tiền, gia đình, văn phòng…) — cần biến môi trường PEXELS_API_KEY
Từ khoá: viết cả tiếng Việt có dấu và tiếng Anh ("công viên Yên Sở|Yen So park") — kho quốc tế tìm tiếng Anh tốt hơn.

Ghi ra <thu_muc_ra>/: 01_*.jpg|mp4 …, nguon.json (tác giả, giấy phép, link — để ghi credit), bang.jpg (lưới đánh số — XEM để chọn).
Chỉ chọn ảnh thật sự đẹp và đúng ý; không có ảnh tốt thì không chèn (hoặc dùng key text thay).
"""
import argparse, json, os, re, subprocess, sys, unicodedata, urllib.parse, urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (video-editor; broll-search)"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cau_hinh import C  # noqa: E402
ROOTS = [Path(x) for x in C["thu_muc_anh"]]
IMG = {".jpg", ".jpeg", ".png", ".webp"}
VID = {".mp4", ".mov", ".webm"}


def bodau(s):
    s = unicodedata.normalize("NFD", s.lower().replace("đ", "d"))
    return re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in s if not unicodedata.combining(c)))


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **({"Authorization": os.environ["PEXELS_API_KEY"]} if "pexels.com" in url and os.environ.get("PEXELS_API_KEY") else {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def src_may(q, want_video):
    toks = [t for t in bodau(q).split() if len(t) > 1]
    out = []
    for root in ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.suffix.lower() not in (IMG | VID) or "/ra/" in str(p) or "/tam/" in str(p) or "kiem_tra" in str(p):
                continue
            if p.stat().st_size < 60_000:
                continue
            name = bodau(str(p.relative_to(root)))
            hit = sum(t in name for t in toks)
            if toks and hit >= max(1, len(toks) - 1):
                out.append({"file": str(p), "nguon": "may", "giay_phep": "của người dùng", "diem": hit, "video": p.suffix.lower() in VID})
    out.sort(key=lambda x: -x["diem"])
    return out[:12]


def src_commons(q, want_video):
    ft = "filetype:video" if want_video else "filetype:bitmap"
    url = ("https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrlimit=20&format=json"
           "&prop=imageinfo&iiprop=url|size|mime|extmetadata&iiurlwidth=1600&gsrsearch=" + urllib.parse.quote(f"{q} {ft}"))
    d = json.loads(get(url))
    out = []
    for p in sorted(d.get("query", {}).get("pages", {}).values(), key=lambda x: x.get("index", 99)):
        ii = p["imageinfo"][0]
        if ii.get("width", 0) < 1000:
            continue
        em = ii.get("extmetadata", {})
        is_v = ii.get("mime", "").startswith("video")
        out.append({"url": ii["url"] if is_v else ii.get("thumburl", ii["url"]), "nguon": "commons", "video": is_v,
                    "tieu_de": p["title"], "trang": ii.get("descriptionurl"),
                    "tac_gia": re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", ""))[:80],
                    "giay_phep": em.get("LicenseShortName", {}).get("value", "")})
    return out


def src_openverse(q, want_video):
    if want_video:
        return []
    d = json.loads(get("https://api.openverse.org/v1/images/?page_size=20&mature=false&q=" + urllib.parse.quote(q)))
    out = []
    for r in d.get("results", []):
        if (r.get("width") or 0) < 1000:
            continue
        out.append({"url": r["url"], "nguon": "openverse", "video": False, "tieu_de": r.get("title", "")[:80], "trang": r.get("foreign_landing_url"),
                    "tac_gia": r.get("creator", ""), "giay_phep": f"{r.get('license','')} {r.get('license_version','')}".strip()})
    return out


def src_pexels(q, want_video):
    if not os.environ.get("PEXELS_API_KEY"):
        return []
    if want_video:
        d = json.loads(get("https://api.pexels.com/videos/search?per_page=12&orientation=portrait&q=" + urllib.parse.quote(q)))
        out = []
        for v in d.get("videos", []):
            fs = sorted([f for f in v["video_files"] if (f.get("height") or 0) >= 1080], key=lambda f: f["height"]) or v["video_files"]
            out.append({"url": fs[0]["link"], "nguon": "pexels", "video": True, "trang": v["url"], "tac_gia": v["user"]["name"], "giay_phep": "Pexels License"})
        return out
    d = json.loads(get("https://api.pexels.com/v1/search?per_page=12&q=" + urllib.parse.quote(q)))
    return [{"url": p["src"]["large2x"], "nguon": "pexels", "video": False, "trang": p["url"], "tac_gia": p["photographer"], "giay_phep": "Pexels License"} for p in d.get("photos", [])]


SRC = {"may": src_may, "commons": src_commons, "openverse": src_openverse, "pexels": src_pexels}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("q"); ap.add_argument("out")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--nguon", default="may,commons,openverse,pexels")
    ap.add_argument("--video", action="store_true", help="ưu tiên video (commons webm, pexels)")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    cands, seen = [], set()
    for q in [x.strip() for x in a.q.split("|") if x.strip()]:
        for s in a.nguon.split(","):
            try:
                for c in SRC[s](q, a.video):
                    k = c.get("url") or c.get("file")
                    if k not in seen:
                        seen.add(k); cands.append(c)
            except Exception as e:
                print(f"  ({s} '{q}': {e.__class__.__name__})", file=sys.stderr)
    got = []
    for c in cands:
        if len(got) >= a.n:
            break
        i = len(got) + 1
        try:
            if c.get("file"):
                ext = Path(c["file"]).suffix.lower()
                dst = out / f"{i:02d}_{c['nguon']}{ext}"
                if dst.exists() or dst.is_symlink():
                    dst.unlink()
                dst.symlink_to(c["file"])
            else:
                ext = Path(urllib.parse.urlparse(c["url"]).path).suffix.lower() or (".mp4" if c["video"] else ".jpg")
                dst = out / f"{i:02d}_{c['nguon']}{ext}"
                dst.write_bytes(get(c["url"], 90))
            c["luu"] = dst.name
            got.append(c)
        except Exception as e:
            print(f"  bỏ 1 ứng viên ({e.__class__.__name__})", file=sys.stderr)
    (out / "nguon.json").write_text(json.dumps(got, ensure_ascii=False, indent=1))
    # bảng xem: ảnh/khung giữa video, đánh số
    th = out / ".thumb"; th.mkdir(exist_ok=True)
    for c in got:
        f = out / c["luu"]
        ss = ["-ss", "1"] if c["video"] else []
        lab = f"{c['luu'][:2]} {c['nguon']}{' VIDEO' if c['video'] else ''}"
        subprocess.run(["ffmpeg", "-v", "error", "-y"] + ss + ["-i", str(f), "-frames:v", "1", "-vf",
                        f"scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2:black,format=yuvj420p,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='{lab}':x=8:y=8:fontsize=30:fontcolor=yellow:box=1:boxcolor=black@0.7",
                        str(th / f"{c['luu'][:2]}.jpg")], capture_output=True)
    if got:
        cols = min(4, len(got)); rows = (len(got) + cols - 1) // cols
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-pattern_type", "glob", "-i", str(th / "*.jpg"), "-vf", f"tile={cols}x{rows}:padding=4",
                        "-frames:v", "1", str(out / "bang.jpg")], capture_output=True)
    print(f"{len(got)} ứng viên → {out}/bang.jpg  (credit: nguon.json)")
    for c in got:
        print(f"  {c['luu']:<22} {c['giay_phep'][:18]:<18} {(c.get('tieu_de') or c.get('file') or '')[:70]}")


if __name__ == "__main__":
    main()
