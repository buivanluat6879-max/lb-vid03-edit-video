#!/usr/bin/env python3
"""BƯỚC 3 — Dựng video dọc 9:16 từ ke_hoach.json (đã được người dùng duyệt).

  python3 dung_video.py ke_hoach.json [ke_hoach_2.json ...] [--nhap]

--nhap : bản xem nhanh 540x960, mã hoá nhanh (để soát bố cục), không chuẩn hoá âm lượng 2 lượt.

Làm theo thứ tự: chọn đoạn → cắt khoảng lặng/từ đệm bên trong → khung dọc bám mặt + zoom giật/đẩy
→ màu → ảnh/video chèn (B-roll) → hook + phụ đề karaoke + thẻ số liệu + CTA (ASS) → logo
→ giọng (gốc đã làm sạch hoặc lồng tiếng) + nhạc né giọng + SFX → -14 LUFS → ảnh bìa nhúng vào MP4.
Ghi ra thư mục "ra": <ten>.mp4, <ten>_gui-nhanh.mp4 (720p nhẹ), <ten>_bia.jpg, <ten>.srt, kiem_tra/luoi.jpg
Lược đồ đầy đủ của ke_hoach.json: references/ke_hoach.md
"""
import hashlib, json, math, re, shlex, subprocess, sys, unicodedata
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
FONTS = SK / "assets/fonts"
sys.path.insert(0, str(SK / "scripts"))
from cau_hinh import C  # noqa: E402
LOGO = Path(C["logo"]) if C["logo"] else None
EDGE_GIONG = {"bac-nu": "vi-VN-HoaiMyNeural", "bac-nu2": "vi-VN-HoaiMyNeural", "nu": "vi-VN-HoaiMyNeural",
              "bac-nam": "vi-VN-NamMinhNeural", "bac-nam2": "vi-VN-NamMinhNeural", "nam": "vi-VN-NamMinhNeural"}


def tts_mot_cau(giong, doc, out, toc):
    """Đọc 1 câu ra out.wav. Có tts_lenh trong cấu hình -> dùng lệnh đó; không -> edge-tts (giọng Microsoft, cần mạng)."""
    if C["tts_lenh"]:
        return run(shlex.split(C["tts_lenh"]) + [giong, doc, out] + ([str(toc)] if toc else []), check=False)
    voice = EDGE_GIONG.get(giong, giong if "Neural" in giong else "vi-VN-HoaiMyNeural")
    rate = f"{(float(toc) - 1) * 100:+.0f}%" if toc else "+0%"
    mp3 = Path(str(out) + ".mp3")
    for _ in range(5):
        r = run([C["python"] if Path(C["python"]).exists() else sys.executable, "-m", "edge_tts", "--voice", voice, f"--rate={rate}",
                 "--text", doc, "--write-media", mp3], check=False)
        if mp3.exists() and mp3.stat().st_size > 0:
            run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ar", "48000", out])
            return r
    return r
NHAC = SK / "scripts/nhac_nen.py"

PHONG = {
    # cắt lặng >x giây, đệm giữ lại, zoom giật, số chữ/khung phụ đề, cỡ chữ, viết hoa, màu chữ đang đọc, màu từ khoá
    "viral":      dict(cat_lang=0.28, dem=0.06, punch=1.14, so_chu=3, co=84, hoa=True,  act="&H0000E6FF&", kw="&H006EFF3D&", pop=True,  sfx=True,  nhac="soi_dong", mau="sang"),
    "chuyen_gia": dict(cat_lang=0.45, dem=0.10, punch=1.08, so_chu=6, co=64, hoa=False, act="&H004AD5FF&", kw="&H0020A0FF&", pop=False, sfx=False, nhac="nhe",      mau="tu_nhien"),
    "dien_anh":   dict(cat_lang=0.70, dem=0.15, punch=1.00, so_chu=6, co=58, hoa=False, act="&H0080DCFF&", kw="&H0060B8FF&", pop=False, sfx=False, nhac="dien_anh", mau="dien_anh"),
}
MAU = {
    "none": "",
    "tu_nhien": "eq=contrast=1.04:saturation=1.08",
    "sang": "eq=contrast=1.06:saturation=1.14:brightness=0.015,colorbalance=rh=0.02:bh=-0.02",
    "am": "colorbalance=rs=0.04:gs=0.01:bs=-0.05:rm=0.03:bm=-0.03,eq=contrast=1.05:saturation=1.06",
    "dien_anh": "colorbalance=rs=-0.04:gs=-0.01:bs=0.05:rh=0.05:gh=0.01:bh=-0.04,eq=contrast=1.10:saturation=0.97,vignette=angle=PI/5",
}
FILLER = {"ờ", "ừ", "ừm", "ưm", "à", "ơ", "ạ", "hmm", "um", "uh", "ừa", "ờm"}


def run(cmd, check=True, quiet=True):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if check and r.returncode:
        print(" ".join(map(str, cmd))[:1500], file=sys.stderr)
        print(r.stderr[-2500:], file=sys.stderr)
        sys.exit(f"Lỗi ffmpeg/lệnh (mã {r.returncode})")
    return r


def dur_of(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).stdout.strip() or 0)


def norm(s):
    return re.sub(r"[^\w%]", "", unicodedata.normalize("NFC", s.lower()))


# ---------------------------------------------------------------- văn bản

def apply_fixes(words, fixes):
    """sua_chu: {"Gia đất": "Giá đất", "đâu?": "đâu."} — khớp cụm chữ liền nhau (không phân biệt hoa thường, bỏ qua dấu câu).
    Số chữ khác nhau -> chia đều mốc thời gian cho các chữ mới (vẫn là chữ riêng, tu_khoa/khi_noi khớp được).
    Chữ mới tự có dấu câu cuối -> thay luôn dấu câu cũ; không có -> giữ dấu câu cũ."""
    if not fixes:
        return words
    for bad, good in fixes.items():
        bt = [norm(x) for x in bad.split()]
        gt = good.split()
        i = 0
        while i <= len(words) - len(bt):
            seg = words[i:i + len(bt)]
            if [norm(w["text"]) for w in seg] != bt:
                i += 1
                continue
            tail = re.sub(r"^.*?([.,!?…:;]*)$", r"\1", seg[-1]["text"])
            if tail and not re.search(r"[.,!?…:;]$", gt[-1]):
                gt2 = gt[:-1] + [gt[-1] + tail]
            else:
                gt2 = list(gt)
            t0, t1 = seg[0]["t0"], seg[-1]["t1"]
            if len(gt2) == len(seg):
                new = [dict(w, text=g) for w, g in zip(seg, gt2)]
            else:
                step = (t1 - t0) / len(gt2)
                new = [{"t0": round(t0 + k * step, 3), "t1": round(t0 + (k + 1) * step, 3), "text": g} for k, g in enumerate(gt2)]
            words[i:i + len(bt)] = new
            i += len(new)
    return words


# ---------------------------------------------------------------- dòng thời gian

def build_pieces(plan, A, st):
    """Từ các 'doan' (giây gốc) -> danh sách mảnh liền mạch sau khi bỏ khoảng lặng + từ đệm."""
    sil = A.get("khoang_lang", [])
    words = [w for s in A.get("cau", []) for w in s["words"]]
    am = plan.get("am", {})
    muted = am.get("tat_tieng_goc") or am.get("long_tieng")
    cut_gap = plan.get("cat_lang", None if muted else st["cat_lang"])  # tiếng gốc bị tắt -> khoảng lặng không còn ý nghĩa
    pad = st["dem"]
    bo = {norm(x) for x in plan.get("bo_tu", [])} if plan.get("bo_tu") is not None else set()
    pieces = []
    for di, d in enumerate(plan["doan"]):
        t0, t1 = float(d["t0"]), float(d["t1"])
        holes = []
        if cut_gap and not d.get("giu_lang"):
            for a, b in sil:
                if a > t0 and b < t1 and b - a > cut_gap:
                    holes.append((a + pad, b - pad))
        for w in words:
            if bo and norm(w["text"]) in bo and w["t0"] >= t0 and w["t1"] <= t1:
                holes.append((w["t0"] - 0.03, w["t1"] + 0.03))
        holes.sort()
        segs, cur = [], t0
        for a, b in holes:
            if a > cur:
                segs.append([cur, a])
            cur = max(cur, b)
        if t1 > cur:
            segs.append([cur, t1])
        segs = [s for s in segs if s[1] - s[0] >= 0.22] or [[t0, t1]]
        for k, (a, b) in enumerate(segs):
            pieces.append({"s0": round(a, 3), "s1": round(b, 3), "doan": di, "dau_doan": k == 0,
                           "toc": float(d.get("toc_do", 1.0)), "zoom": d.get("zoom"), "day": d.get("day", False),
                           "reframe": d.get("reframe"), "cx": d.get("cx")})
    # zoom giật tự động: đổi cỡ ở mỗi chỗ cắt để giấu vết nhảy hình
    base_toggle = 0
    gmode = plan.get("khung", {}).get("reframe", "mat")
    for i, p in enumerate(pieces):
        if p["zoom"] is None and (p.get("reframe") or gmode) == "nen_mo":
            p["zoom"] = 1.0  # khung ngang trên nền mờ: zoom tự động sẽ xén mất nội dung hai bên
        if p["zoom"] is None:
            if st["punch"] > 1.0:
                base_toggle = (base_toggle + 1) % 2 if i else 0
                p["zoom"] = 1.0 if base_toggle == 0 else st["punch"]
            else:
                p["zoom"] = 1.0
        p["zoom"] = float(p["zoom"])
    t = 0.0
    for p in pieces:
        p["o0"] = round(t, 3)
        t += (p["s1"] - p["s0"]) / p["toc"]
        p["o1"] = round(t, 3)
    return pieces, words


def map_words(words, pieces):
    """Đổi mốc chữ từ giây gốc sang giây thành phẩm. Chữ rơi vào lỗ đã cắt (Whisper lệch mốc) thì kẹp vào mảnh gần nhất
    của cùng đoạn, để phụ đề không mất chữ. Kết quả xếp theo thời gian thành phẩm (đoạn có thể bị đảo thứ tự)."""
    by_doan = {}
    for p in pieces:
        by_doan.setdefault(p["doan"], []).append(p)
    out = []
    for w in words:
        mid = (w["t0"] + w["t1"]) / 2
        best = None
        for d, ps in by_doan.items():
            lo, hi = ps[0]["s0"], ps[-1]["s1"]
            if lo - 0.05 <= mid <= hi + 0.05:
                best = min(ps, key=lambda p: 0 if p["s0"] <= mid < p["s1"] else min(abs(mid - p["s0"]), abs(mid - p["s1"])))
                break
        if best is None:
            continue
        p = best
        a = min(max(w["t0"], p["s0"]), p["s1"] - 0.05)
        b = min(max(w["t1"], a + 0.08), p["s1"])
        o0 = p["o0"] + (a - p["s0"]) / p["toc"]
        o1 = p["o0"] + (b - p["s0"]) / p["toc"]
        out.append({"o0": round(o0, 3), "o1": round(max(o1, o0 + 0.06), 3), "text": w["text"]})
    out.sort(key=lambda w: w["o0"])
    for i in range(len(out) - 1):  # không chồng nhau
        if out[i]["o1"] > out[i + 1]["o0"]:
            out[i]["o1"] = max(out[i]["o0"] + 0.04, out[i + 1]["o0"])
    return out


def find_phrase(owords, phrase, after=0.0):
    pt = [norm(x) for x in phrase.split()]
    for i in range(len(owords) - len(pt) + 1):
        if owords[i]["o0"] >= after and [norm(w["text"]) for w in owords[i:i + len(pt)]] == pt:
            return owords[i]["o0"]
    return None


def resolve_time(item, owords, pieces, A):
    if "t" in item:
        return float(item["t"])
    if "khi_noi" in item:
        t = find_phrase(owords, item["khi_noi"])
        if t is not None:
            return t
        print(f"  ! không tìm thấy cụm '{item['khi_noi']}' trong lời — bỏ mục này", file=sys.stderr)
        return None
    if "t_goc" in item:
        tg = float(item["t_goc"])
        for p in pieces:
            if p["s0"] <= tg < p["s1"]:
                return p["o0"] + (tg - p["s0"]) / p["toc"]
    return None


# ---------------------------------------------------------------- hình

def face_at(A, s0, s1):
    fs = [f for f in A.get("mat", []) if s0 - 0.3 <= f["t"] <= s1 + 0.3]
    if not fs:
        fs = A.get("mat", [])
        if not fs:
            return None
    xs = sorted(f["cx"] for f in fs); ys = sorted(f["cy"] for f in fs); hs = sorted(f["h"] for f in fs)
    m = len(xs) // 2
    return xs[m], ys[m], hs[m]


def piece_vf(p, info, W, H, mode, face, draft, ck=None):
    sw, sh, z = info["w"], info["h"], max(1.0, p["zoom"])
    tail = f"fps=30,setsar=1"
    head = ""
    if ck:  # cat_khung [x, y, w, h] theo pixel gốc: cắt bỏ viền/phụ đề cứng trước khi dựng khung dọc
        cx_, cy_, cw_, ch_ = [int(v) // 2 * 2 for v in ck]
        head = f"crop={cw_}:{ch_}:{cx_}:{cy_},"
        if face:
            face = ((face[0] * sw - cx_) / cw_, (face[1] * sh - cy_) / ch_, face[2] * sh / ch_)
        sw, sh = cw_, ch_
    return head + _piece_vf(p, sw, sh, z, W, H, mode, face, draft, tail)


def _piece_vf(p, sw, sh, z, W, H, mode, face, draft, tail):
    if mode == "nen_mo":
        fg_w = int(W * z) // 2 * 2
        return (f"split=2[a][b];[a]scale={W//4}:{H//4}:force_original_aspect_ratio=increase,crop={W//4}:{H//4},boxblur=12:2,"
                f"scale={W}:{H},eq=brightness=-0.12:saturation=0.8[bg];[b]scale={fg_w}:-2:flags=lanczos[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,{tail}")
    target = 9 / 16
    if sw / sh >= target:     # khung ngang/vuông -> cắt dọc
        ch = sh / z; cw = ch * target
    else:                      # khung đã dọc (hoặc hẹp hơn) -> cắt theo bề ngang
        cw = sw / z; ch = cw / target
    cw, ch = min(cw, sw), min(ch, sh)
    cw, ch = int(cw) // 2 * 2, int(ch) // 2 * 2
    if p.get("cx") is not None:
        fcx, fcy, fh = float(p["cx"]), 0.45, 0.2
    elif face and mode == "mat":
        fcx, fcy, fh = face
    else:
        fcx, fcy, fh = 0.5, 0.45, 0.2
    x = min(max(fcx * sw - cw / 2, 0), sw - cw)
    if face and mode == "mat" and ch < sh:
        y = min(max(fcy * sh - 0.40 * ch, 0), sh - ch)   # mặt nằm ~40% chiều cao khung
    else:
        y = (sh - ch) / 2
    if face and mode == "mat":
        p["face_oy"] = round((fcy * sh - y) / ch, 4)   # tâm mặt theo chiều cao khung thành phẩm (0..1)
        p["face_oh"] = round(fh * sh / ch, 4)
    vf = f"crop={cw}:{ch}:{int(x)}:{int(y)},scale={W}:{H}:flags=lanczos"
    if cw < W * 0.75 and not draft:
        vf += ",unsharp=5:5:0.55:5:5:0"
    if p.get("day"):
        n = max(1, int((p["s1"] - p["s0"]) / p["toc"] * 30))
        big = "" if draft else f"scale={W*2}:{H*2}:flags=bicubic,"
        vf += f",{big}zoompan=z='1+0.10*on/{n}':d=1:x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':s={W}x{H}:fps=30"
    return vf + "," + tail


def render_piece(i, p, plan, A, info, W, H, tmp, draft):
    out = tmp / f"p{i:03d}.mp4"
    mode = p.get("reframe") or plan.get("khung", {}).get("reframe", "mat")
    if mode == "mat" and not A.get("mat"):
        mode = "giua"
    face = face_at(A, p["s0"], p["s1"])
    vf = piece_vf(p, info, W, H, mode, face, draft, plan.get("cat_khung"))
    d = p["s1"] - p["s0"]
    od = d / p["toc"]
    if p["toc"] != 1.0:
        vf = f"setpts=PTS/{p['toc']}," + vf
    src = plan["nguon"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{p['s0']:.3f}", "-t", f"{d:.3f}", "-i", src]
    has_a = info["co_tieng"] and not plan.get("am", {}).get("tat_tieng_goc")
    if not has_a:
        cmd += ["-f", "lavfi", "-t", f"{od:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    af = "aresample=48000,aformat=channel_layouts=stereo"
    if p["toc"] != 1.0:
        af += f",atempo={p['toc']}"
    fd = 0.012
    af += f",afade=t=in:d={fd},afade=t=out:st={max(0, od - fd):.3f}:d={fd}"
    fc = f"[0:v]{vf}[v]"
    amap = "[a]" if has_a else "1:a"
    if has_a:
        fc += f";[0:a]{af}[a]"
    enc = ["-c:v", "libx264", "-preset", "ultrafast" if draft else "medium", "-crf", "26" if draft else "15", "-pix_fmt", "yuv420p",
           "-c:a", "pcm_s16le"]
    run(cmd + ["-filter_complex", fc, "-map", "[v]", "-map", amap, "-t", f"{od:.3f}"] + enc + [out.with_suffix(".mov")])
    return out.with_suffix(".mov")


def freeze_cover(plan, A, info, W, H, tmp, draft, t_goc, n_frames=3):
    p = {"s0": t_goc, "s1": t_goc + 0.5, "toc": 1.0, "zoom": 1.0, "day": False, "reframe": None, "cx": None}
    mode = plan.get("khung", {}).get("reframe", "mat")
    if mode == "mat" and not A.get("mat"):
        mode = "giua"
    vf = piece_vf(p, info, W, H, mode, face_at(A, t_goc, t_goc + 0.5), draft, plan.get("cat_khung"))
    out = tmp / "bia.mov"
    dd = n_frames / 30
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t_goc:.3f}", "-i", plan["nguon"], "-f", "lavfi", "-t", f"{dd:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
         "-filter_complex", f"[0:v]{vf},trim=end_frame=1,loop=loop={n_frames - 1}:size=1,setpts=N/30/TB[v]", "-map", "[v]", "-map", "1:a",
         "-t", f"{dd:.3f}", "-c:v", "libx264", "-crf", "15", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", out])
    return out, dd


# ---------------------------------------------------------------- chữ (ASS)

def ass_time(t):
    t = max(0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def esc(s):
    return s.replace("\\", "").replace("{", "(").replace("}", ")")


def chunks(owords, n, maxc):
    out, cur = [], []
    for i, w in enumerate(owords):
        cur.append(w)
        nxt = owords[i + 1] if i + 1 < len(owords) else None
        txt = " ".join(x["text"] for x in cur)
        name_cont = (nxt is not None and w["text"][:1].isupper() and nxt["text"][:1].isupper() and i > 0
                     and len(cur) < n + 2 and w["text"][-1] not in ".?!…,;:")  # không tách đôi tên riêng (Hà | Nội)
        brk = (nxt is None or w["text"][-1] in ".?!…,;:" or nxt["o0"] - w["o1"] > 0.45
               or ((len(cur) >= n or len(txt) >= maxc) and not name_cont))
        if brk:
            out.append(cur); cur = []
    return out


def kw_mask(ch, kws):
    mask = [False] * len(ch)
    for k in kws:
        kt = [norm(x) for x in k.split()]
        for i in range(len(ch) - len(kt) + 1):
            if [norm(w["text"]) for w in ch[i:i + len(kt)]] == kt:
                for j in range(i, i + len(kt)):
                    mask[j] = True
    return mask


def split_num(txt):
    """'30%' -> ('', 30.0, '%', 0) · '3,2 TỶ' -> ('', 3.2, ' TỶ', 1) · '+1.250 ha' ... ; không có số -> None"""
    m = re.search(r"(\d+(?:[.,]\d+)?)", txt)
    if not m:
        return None
    raw = m.group(1)
    dec = 0
    if "," in raw:
        val = float(raw.replace(",", ".")); dec = len(raw.split(",")[1])
    elif re.fullmatch(r"\d{1,3}\.\d{3}", raw):
        val = float(raw.replace(".", ""))
    elif "." in raw:
        val = float(raw); dec = len(raw.split(".")[1])
    else:
        val = float(raw)
    return txt[:m.start()], val, txt[m.end():], dec, "," in raw


def fmt_num(v, dec, comma):
    s = f"{v:.{dec}f}"
    return s.replace(".", ",") if comma else s


def kinetic_events(k, t, W, H, fsz, owords):
    """Key text động. kieu: dap | dem_so | xep_chu | go_chu. Trả về danh sách dòng Dialogue."""
    ev = []
    kieu = k.get("kieu", "dap")
    d = float(k.get("dur", 1.8))
    chu = k.get("chu", "")
    cx = W // 2
    y = int(k.get("y", 0.40) * H)
    col = k.get("mau", "&H0000E1FF&")  # vàng
    big = fsz(int(k.get("co", 170)))
    T = lambda a: ass_time(a)
    if k.get("toi_nen", True):  # nền tối lại cho chữ nổi
        ev.append(f"Dialogue: 6,{T(t)},{T(t+d)},Kin,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H000000&\\1a&H70&\\fad(90,160)}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\\p0}}")
    base = f"\\an5\\fs{big}\\1c{col}\\bord{fsz(10)}\\shad{fsz(5)}"
    if kieu == "dap":
        # đập vào: to 260% + nhoè -> 100% trong 0,14s, rung nhẹ, rời đi phóng to mờ dần
        ev.append(f"Dialogue: 7,{T(t)},{T(t+d)},Kin,,0,0,0,,{{{base}\\pos({cx},{y})\\fscx260\\fscy260\\blur8\\alpha&H60&"
                  f"\\t(0,140,\\fscx100\\fscy100\\blur0\\alpha&H00&)\\t(140,200,\\frz-3)\\t(200,260,\\frz2)\\t(260,320,\\frz0)"
                  f"\\t({int(d*1000)-180},{int(d*1000)},\\fscx125\\fscy125\\alpha&HFF&)}}{esc(chu)}")
    elif kieu == "dem_so":
        sp = split_num(chu)
        if not sp:
            return kinetic_events(dict(k, kieu="dap"), t, W, H, fsz, owords)
        pre, val, suf, dec, comma = sp
        run_t = min(0.8, d * 0.45); steps = max(6, int(run_t * 30))
        for i in range(steps):
            a = t + run_t * i / steps; b = t + run_t * (i + 1) / steps
            e = 1 - (1 - (i + 1) / steps) ** 3  # chậm dần
            ev.append(f"Dialogue: 7,{T(a)},{T(b)},Kin,,0,0,0,,{{{base}\\pos({cx},{y})}}{esc(pre + fmt_num(val * e, dec, comma) + suf)}")
        ev.append(f"Dialogue: 7,{T(t+run_t)},{T(t+d)},Kin,,0,0,0,,{{{base}\\pos({cx},{y})\\t(0,90,\\fscx115\\fscy115)\\t(90,200,\\fscx100\\fscy100)"
                  f"\\t({int((d-run_t)*1000)-160},{int((d-run_t)*1000)},\\alpha&HFF&)}}{esc(chu)}")
    elif kieu == "xep_chu":
        words = chu.split()
        # mỗi chữ hiện đúng lúc được nói (nếu tìm thấy trong lời), không thì rải đều
        times = []
        if k.get("_khop") is not None:
            i0 = k["_khop"]
            times = [owords[i0 + j]["o0"] for j in range(len(words)) if i0 + j < len(owords)]
        if len(times) != len(words):
            step = min(0.32, d * 0.6 / max(1, len(words)))
            times = [t + j * step for j in range(len(words))]
        lines = []  # tối đa 2 chữ / 11 ký tự mỗi dòng, gom từ cuối để dòng cuối là cụm trọn ("PHẢI" / "CẨN THẬN")
        rest = list(words)
        while rest:
            take = 2 if len(rest) >= 2 and len(" ".join(rest[-2:])) <= 11 else 1
            lines.insert(0, rest[-take:]); rest = rest[:-take]
        sizes = [fsz(150), fsz(118), fsz(150), fsz(118)]
        cols = [col, "&H00FFFFFF&", col, "&H00FFFFFF&"]
        tot_h = sum(sizes[i % 4] * 1.08 for i in range(len(lines)))
        yy = y - tot_h / 2
        wi = 0
        end = max(times[-1] + 0.6, t + d)
        for li, ln in enumerate(lines):
            sz = sizes[li % 4]; yy += sz * 0.54
            t_ln = times[wi]
            txt = " ".join(ln)
            dx = -60 if li % 2 == 0 else 60
            ev.append(f"Dialogue: 7,{T(t_ln)},{T(end)},Kin,,0,0,0,,{{\\an5\\fs{sz}\\1c{cols[li%4]}\\bord{fsz(9)}\\shad{fsz(4)}"
                      f"\\move({cx+dx},{int(yy)},{cx},{int(yy)},0,160)\\fscx70\\fscy70\\t(0,160,\\fscx100\\fscy100)\\fad(60,180)}}{esc(txt)}")
            yy += sz * 0.54
            wi += len(ln)
        k["_het"] = end
    elif kieu == "go_chu":
        n = len(chu); run_t = min(0.9, 0.045 * n)
        for i in range(1, n + 1):
            a = t + run_t * (i - 1) / n; b = t + run_t * i / n if i < n else t + d
            ev.append(f"Dialogue: 7,{T(a)},{T(b)},Kin,,0,0,0,,{{\\an5\\fs{fsz(int(k.get('co', 110)))}\\1c{col}\\bord{fsz(8)}\\shad{fsz(4)}\\pos({cx},{y})}}"
                      f"{esc(chu[:i])}{{\\alpha&HFF&}}{esc(chu[i:])}")
    if k.get("phu"):
        ev.append(f"Dialogue: 7,{T(t+0.18)},{T(k.get('_het', t+d))},Kin,,0,0,0,,{{\\an5\\fs{fsz(56)}\\1c&H00FFFFFF&\\bord{fsz(6)}\\shad{fsz(3)}"
                  f"\\pos({cx},{y + int(big*0.78) if kieu != 'xep_chu' else int(y + H*0.16)})\\fad(120,160)}}{esc(k['phu'])}")
    return ev


def build_ass(plan, st, owords, total, W, H, cards, path, kins=(), flashes=(), splits=()):
    sc = W / 1080
    cap = plan.get("phu_de", {})
    co = int(cap.get("co", st["co"]) * sc)
    fsz = lambda v: int(v * sc)
    marg = int(cap.get("cach_day", 0.25) * H)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Be Vietnam Pro ExtraBold,{co},&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,{max(2, co // 12)},{max(1, co // 28)},2,{fsz(60)},{fsz(60)},{marg},1
Style: Hook1,Be Vietnam Pro ExtraBold,{fsz(86)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,3,{fsz(18)},0,8,{fsz(50)},{fsz(50)},0,1
Style: Hook2,Be Vietnam Pro ExtraBold,{fsz(86)},&H00101010,&H00101010,&H0000D7FF,&H0000D7FF,0,0,0,0,100,100,0,0,3,{fsz(18)},0,8,{fsz(50)},{fsz(50)},0,1
Style: Kick,Be Vietnam Pro Bold,{fsz(44)},&H0000D7FF,&H0000D7FF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,{fsz(4)},0,8,{fsz(50)},{fsz(50)},0,1
Style: Num,Be Vietnam Pro ExtraBold,{fsz(130)},&H0000D7FF,&H0000D7FF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,{fsz(8)},{fsz(3)},8,{fsz(50)},{fsz(50)},0,1
Style: Lab,Be Vietnam Pro Bold,{fsz(50)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,{fsz(5)},{fsz(2)},8,{fsz(50)},{fsz(50)},0,1
Style: Kin,Be Vietnam Pro ExtraBold,{fsz(150)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,{fsz(10)},{fsz(5)},5,0,0,0,1
Style: Cta,Be Vietnam Pro ExtraBold,{fsz(60)},&H00101010,&H00101010,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,3,{fsz(16)},0,8,{fsz(50)},{fsz(50)},0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    hook = plan.get("hook") or {}
    hook_end = 0.0
    if hook.get("dong1") or hook.get("dong2"):
        hd = float(hook.get("dur", 2.8))
        if kins:  # key text đầu tiên đến sớm -> hook nhường chỗ (không chồng 2 lớp chữ to)
            hd = max(0.6, min(hd, min(k["_t"] for k in kins)))
        hook_end = hd
        nm = plan.get("khung", {}).get("reframe") == "nen_mo"
        y = int(hook.get("y", 0.10 if nm else 0.17) * H)
        gap = fsz(122)
        rows = []
        if hook.get("kicker"):
            rows.append(("Kick", hook["kicker"], fsz(70)))
        if hook.get("dong1"):
            rows.append(("Hook1", hook["dong1"], gap))
        if hook.get("dong2"):
            rows.append(("Hook2", hook["dong2"], gap))
        yy = y
        for k, (sty, txt, step) in enumerate(rows):
            # khung 0 hiện đủ chữ (ảnh bìa), sau đó chỉ nảy nhẹ — không mờ dần từ đen
            ev.append(f"Dialogue: 5,{ass_time(0)},{ass_time(hd)},{sty},,0,0,0,,{{\\pos({W//2},{yy})\\fad(0,180)}}{esc(txt)}")
            yy += step
    # phụ đề karaoke
    if cap.get("bat", True) and owords:
        kws = cap.get("tu_khoa", [])
        n = cap.get("so_chu", st["so_chu"])
        maxc = 18 if n <= 3 else 30
        hoa = cap.get("viet_hoa", st["hoa"])
        CH = chunks(owords, n, maxc)
        for ci, ch in enumerate(CH):
            mask = kw_mask(ch, kws)
            c_end = ch[-1]["o1"] + 0.12
            if ci + 1 < len(CH):
                c_end = min(c_end, CH[ci + 1][0]["o0"])  # không để 2 dòng phụ đề chồng nhau
            for i, w in enumerate(ch):
                s = w["o0"]
                e = ch[i + 1]["o0"] if i + 1 < len(ch) else c_end
                if e - s < 0.04:
                    continue
                parts = []
                for j, x in enumerate(ch):
                    t = esc(x["text"].upper() if hoa else x["text"])
                    if j == i:
                        pop = "\\t(0,90,\\fscx112\\fscy112)\\t(90,180,\\fscx100\\fscy100)" if st["pop"] else ""
                        parts.append(f"{{\\c{st['act']}{pop}}}{t}{{\\r}}")
                    elif mask[j]:
                        parts.append(f"{{\\c{st['kw']}}}{t}{{\\r}}")
                    else:
                        parts.append(t)
                pos = ""
                if any(a - 0.05 <= s < b for a, b in splits):  # đang chia đôi -> phụ đề nằm trên đường phân cách
                    pos = f"{{\\an5\\pos({W//2},{H//2})}}"
                ev.append(f"Dialogue: 1,{ass_time(s)},{ass_time(e)},Cap,,0,0,0,,{pos}{' '.join(parts)}")
    # thẻ số liệu
    for c in cards:
        t, d = c["_t"], float(c.get("dur", 2.6))
        y = int(c.get("y", 0.2) * H)
        anim = "\\fscx55\\fscy55\\t(0,140,\\fscx108\\fscy108)\\t(140,240,\\fscx100\\fscy100)\\fad(0,200)"
        if c.get("dong1"):
            ev.append(f"Dialogue: 4,{ass_time(t)},{ass_time(t + d)},Num,,0,0,0,,{{\\pos({W//2},{y}){anim}}}{esc(c['dong1'])}")
        if c.get("dong2"):
            ev.append(f"Dialogue: 4,{ass_time(t + 0.08)},{ass_time(t + d)},Lab,,0,0,0,,{{\\pos({W//2},{y + fsz(150)}){anim}}}{esc(c['dong2'])}")
    # key text động
    for k in kins:
        ev += kinetic_events(k, k["_t"], W, H, fsz, owords)
    # chớp sáng khi vào B-roll (viral)
    for ft in flashes:
        ev.append(f"Dialogue: 8,{ass_time(ft)},{ass_time(ft + 0.12)},Kin,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HFFFFFF&\\1a&H50&\\fad(0,110)}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\\p0}}")
    # lời kêu gọi cuối
    if plan.get("cta"):
        cta = plan["cta"] if isinstance(plan["cta"], dict) else {"text": plan["cta"]}
        cd = float(cta.get("dur", 2.4))
        c0 = max(hook_end, total - cd)
        cy = cta.get("y")
        if cy is None:  # né thẻ số liệu đang hiện cùng lúc
            busy = [c for c in cards if c["_t"] < total and c["_t"] + float(c.get("dur", 2.6)) > c0]
            cy = 0.08 if busy else 0.17
        ev.append(f"Dialogue: 4,{ass_time(c0)},{ass_time(total)},Cta,,0,0,0,,{{\\pos({W//2},{int(cy*H)})\\fad(150,0)}}{esc(cta['text'])}")
    path.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")


def write_srt(owords, path):
    L, k = [], 1
    for ch in chunks(owords, 7, 36):
        def f(t):
            return f"{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{int(t*1000)%1000:03d}"
        L += [str(k), f"{f(ch[0]['o0'])} --> {f(ch[-1]['o1'])}", " ".join(w["text"] for w in ch), ""]
        k += 1
    path.write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------- lồng tiếng

def tts_lines(lt, tmp):
    """long_tieng.cau: ["câu đọc", {"doc": "ba mươi phần trăm", "chu": "30%"}] -> voice.wav + chữ có mốc giây."""
    giong = lt.get("giong", "bac-nam"); toc = lt.get("toc_do")
    gap = float(lt.get("nghi", 0.22))
    files, owords, t = [], [], float(lt.get("bat_dau", 0.25))
    sil = tmp / "nghi.wav"
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{gap}", "-c:a", "pcm_s16le", sil])
    lead = tmp / "dau.wav"
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{t}", "-c:a", "pcm_s16le", lead])
    files.append(lead)
    for c in lt["cau"]:
        doc, chu = (c, c) if isinstance(c, str) else (c["doc"], c.get("chu", c["doc"]))
        h = hashlib.md5(f"{giong}|{toc}|{doc}".encode()).hexdigest()[:12]
        raw = tmp / f"tts_{h}.wav"
        if not raw.exists():
            r = tts_mot_cau(giong, doc, raw, toc)
            if not raw.exists():
                sys.exit(f"Lồng tiếng lỗi ở câu: {doc}\n{r.stderr[-500:]}")
        fix = tmp / f"tts_{h}_48.wav"
        run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,aresample=48000,aformat=channel_layouts=stereo", "-c:a", "pcm_s16le", fix])
        d = dur_of(fix)
        ws = chu.split()
        wt = [len(x) + 2 for x in ws]
        tot = sum(wt); a = t + 0.03
        for x, wv in zip(ws, wt):
            b = a + (d - 0.08) * wv / tot
            owords.append({"o0": round(a, 3), "o1": round(b, 3), "text": x}); a = b
        files += [fix, sil]
        t += d + gap
    lst = tmp / "tts_list.txt"
    lst.write_text("".join(f"file '{f}'\n" for f in files))
    voice = tmp / "voice_tts.wav"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:a", "pcm_s16le", voice])
    return voice, owords, t


# ---------------------------------------------------------------- dựng 1 kế hoạch

def build(plan_path, draft):
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text())
    base = plan_path.parent
    rp = lambda p: str((base / p).resolve()) if p and not str(p).startswith("/") else p
    plan["nguon"] = rp(plan["nguon"])
    A = json.loads(Path(rp(plan.get("phan_tich", "phan_tich.json"))).read_text())
    info = A["thong_so"]
    style = plan.get("phong_cach", "chuyen_gia")
    st = dict(PHONG[style])
    W, H = (540, 960) if draft else (1080, 1920)
    ra = Path(rp(plan.get("ra", "ra")))
    ten = plan.get("ten", plan_path.stem) + ("_nhap" if draft else "")
    tmp = ra / "tam" / ten
    tmp.mkdir(parents=True, exist_ok=True)
    (ra / "kiem_tra").mkdir(parents=True, exist_ok=True)
    am = plan.get("am", {})
    lt = am.get("long_tieng")

    # nhạc trước (cảnh không lời cần biết nhịp để cắt khớp phách)
    music, bpm = None, None
    nh = am.get("nhac", "auto")
    has_voice_plan = bool(lt) or (info["co_tieng"] and not am.get("tat_tieng_goc"))
    if nh == "auto" and C["nhac_mac_dinh"] and Path(C["nhac_mac_dinh"]).exists() and has_voice_plan:
        nh = C["nhac_mac_dinh"]                 # nhạc thật (CC) trong cấu hình cho video có lời
        am.setdefault("nhac_vol", 0.13)
        am.setdefault("sfx", False)
    est_total = sum(float(d["t1"]) - float(d["t0"]) for d in plan["doan"]) + 5
    print(f"  nhạc: {'tự tổng hợp' if nh == 'auto' else (Path(str(nh)).name if nh else 'không')}")
    if nh == "auto":
        kieu = am.get("kieu_nhac") or ("soi_dong" if A.get("kieu_doan") == "canh" else st["nhac"])
        music = tmp / f"nhac_{kieu}.wav"
        r = run(["python3", NHAC, "nhac", music, "--dur", f"{est_total + 30:.1f}", "--kieu", kieu, "--seed", str(am.get("seed", abs(hash(ten)) % 97 + 1))])
        bpm = json.loads(r.stdout.strip().splitlines()[-1])["bpm"]
    elif nh:
        music = Path(rp(nh))
        bpm = am.get("bpm")
    if bpm and plan.get("khop_nhip", A.get("kieu_doan") == "canh" and not lt):
        beat = 60 / bpm
        for d in plan["doan"]:
            L = float(d["t1"]) - float(d["t0"])
            k = max(2, round(L / beat))
            d["t1"] = round(float(d["t0"]) + k * beat * float(d.get("toc_do", 1.0)), 3)
            if d["t1"] > info["dur"]:
                d["t1"] = round(float(d["t0"]) + max(2, int(L / beat)) * beat, 3)
        plan.setdefault("cat_lang", None)

    pieces, words = build_pieces(plan, A, st)
    words = apply_fixes([dict(w) for w in words], plan.get("sua_chu"))
    total = pieces[-1]["o1"]
    print(f"▸ {ten}: {len(plan['doan'])} đoạn → {len(pieces)} mảnh, dài {total:.1f}s (gốc giữ {sum(float(d['t1'])-float(d['t0']) for d in plan['doan']):.1f}s)")

    # 1) mảnh hình
    files = []
    cover_d = 0.0
    bia = plan.get("bia", {})
    if bia.get("t_goc") is not None:
        f, cover_d = freeze_cover(plan, A, info, W, H, tmp, draft, float(bia["t_goc"]))
        files.append(f)
    for i, p in enumerate(pieces):
        files.append(render_piece(i, p, plan, A, info, W, H, tmp, draft))
        print(f"  mảnh {i+1}/{len(pieces)}", end="\r")
    print()
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{f}'\n" for f in files))
    cat = tmp / "noi.mov"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", cat])

    # dịch mốc theo ảnh bìa đóng băng đầu video
    for p in pieces:
        p["o0"] += cover_d; p["o1"] += cover_d
    total += cover_d

    # 2) lời + chữ
    cat_audio = cat
    if lt:
        voice, owords, vend = tts_lines(lt, tmp)
        owords = [dict(w, o0=w["o0"] + cover_d, o1=w["o1"] + cover_d) for w in owords]
        if vend + cover_d > total:  # hình ngắn hơn lời -> kéo chậm hình cho vừa (tối đa 1,6 lần), còn thiếu thì lặp
            f = (vend + cover_d + 0.4) / total
            slow = tmp / "noi_cham.mov"
            if f <= 1.6:
                run(["ffmpeg", "-v", "error", "-y", "-i", cat, "-filter_complex", f"[0:v]setpts=PTS*{f:.4f},fps=30[v]", "-map", "[v]", "-c:v", "libx264", "-crf", "15", "-preset", "medium", slow])
            else:
                run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", cat, "-t", f"{vend + cover_d + 0.4:.3f}", "-an", "-c:v", "libx264", "-crf", "15", slow])
            cat = slow
            total = vend + cover_d + 0.4
        else:
            total = min(total, vend + cover_d + 0.6)
    else:
        voice = None
        owords = map_words(words, pieces)
        bo = {norm(x) for x in plan.get("bo_tu", [])} | FILLER
        owords = [w for w in owords if norm(w["text"]) not in bo]
        if am.get("tat_tieng_goc"):
            owords = []  # tiếng gốc đã tắt, không có lời -> không có phụ đề (chỉ hook/thẻ/CTA)

    cards = []
    for c in plan.get("the", []):
        t = resolve_time(c, owords, pieces, A)
        if t is not None:
            cards.append(dict(c, _t=t))
    chen = []
    for c in plan.get("chen", []):
        t = resolve_time(c, owords, pieces, A)
        if t is not None:
            chen.append(dict(c, _t=t, file=rp(c["file"])))

    kins = []
    for kk in plan.get("chu_dong", []):
        t = resolve_time(kk, owords, pieces, A)
        if t is None:
            continue
        kk = dict(kk, _t=max(0.0, t - float(kk.get("som", 0.05))))
        if kk.get("kieu") == "xep_chu" and kk.get("khi_noi"):
            pt = [norm(x) for x in kk.get("chu", "").split()]
            for i in range(len(owords)):
                if abs(owords[i]["o0"] - t) < 0.01 and [norm(w["text"]) for w in owords[i:i + len(pt)]] == pt:
                    kk["_khop"] = i
                    break
        kins.append(kk)
    # quyết định trước vị trí thẻ ảnh / chia đôi (cần cho phụ đề), dựa vào vị trí mặt trong mảnh
    for c in chen:
        if c.get("kieu") == "the_anh" and "y" not in c:
            pc = next((p for p in pieces if p["o0"] <= c["_t"] < p["o1"]), None)
            foy, foh = (pc.get("face_oy"), pc.get("face_oh")) if pc else (None, None)
            if foy is not None:
                ch_n = float(c.get("rong", 0.74)) * W * float(c.get("ti_le", 0.68)) / H + 0.02
                room = foy - foh * 0.75 - 0.05
                if room >= ch_n:
                    c["y"] = 0.05 + room / 2 + 0.01
                else:
                    c["kieu"] = "chia_doi"
    splits = [(c["_t"], c["_t"] + float(c.get("dur", 3.0))) for c in chen if c.get("kieu") == "chia_doi"]
    flashes = [c["_t"] for c in chen if st["sfx"] and c.get("kieu", "full") in ("full", "the_anh", "chia_doi")]
    ass = tmp / "chu.ass"
    build_ass(plan, st, owords, total, W, H, cards, ass, kins, flashes, splits)
    write_srt(owords, ra / f"{ten}.srt")

    # 3) hình hoàn chỉnh: màu → chèn → logo → chữ
    mau = plan.get("mau", "auto")
    look = MAU.get(st["mau"] if mau == "auto" else mau, "")
    pre = []
    y = A.get("do_sang_tb")
    if mau == "auto" and y:
        if y < 75:
            pre.append(f"eq=gamma={min(1.45, 1 + (80 - y) / 110):.2f}:brightness=0.02")
        elif y > 175:
            pre.append("eq=gamma=0.93")
    grade = ",".join([x for x in pre + [look] if x]) or "null"
    inputs = ["-i", cat]
    fc = [f"[0:v]{grade}[g0]"]
    last = "g0"
    k = 1
    for j, c in enumerate(chen):
        t, d = c["_t"], float(c.get("dur", 3.0))
        f = c["file"]
        is_img = Path(f).suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
        if is_img:
            inputs += ["-loop", "1", "-framerate", "30", "-t", f"{d:.3f}", "-i", f]
        else:
            inputs += ["-ss", str(c.get("tu", 0)), "-t", f"{d:.3f}", "-i", f]
        kieu = c.get("kieu", "full")
        n = int(d * 30)
        pc = next((p for p in pieces if p["o0"] <= t < p["o1"]), None)
        foy = pc.get("face_oy") if pc else None
        if kieu == "khung":
            bw, bh = int(W * 0.88) // 2 * 2, int(W * 0.88 * 0.62) // 2 * 2
            zp = f"scale={bw*2}:{bh*2}:force_original_aspect_ratio=increase,crop={bw*2}:{bh*2},zoompan=z='1+0.06*on/{n}':d=1:x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':s={bw}x{bh}:fps=30" if is_img else f"scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},fps=30"
            fc.append(f"[{k}:v]{zp},pad={bw+12}:{bh+12}:6:6:white,format=yuva420p,fade=t=in:st=0:d=0.18:alpha=1,fade=t=out:st={d-0.18:.3f}:d=0.18:alpha=1,setpts=PTS-STARTPTS+{t:.3f}/TB[c{j}]")
            fc.append(f"[{last}][c{j}]overlay=(W-w)/2:{int(H*0.14)}:eof_action=pass:enable='between(t,{t:.3f},{t+d:.3f})'[g{k}]")
        elif kieu == "chia_doi":
            hh = H // 2 // 2 * 2
            fy = foy if foy is not None else 0.42
            ycrop = int(min(max(fy * H - hh * 0.40, 0), H - hh))
            zp = f"scale={W*2}:{hh*2}:force_original_aspect_ratio=increase,crop={W*2}:{hh*2},zoompan=z='1+0.08*on/{n}':d=1:x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':s={W}x{hh}:fps=30" if is_img else f"scale={W}:{hh}:force_original_aspect_ratio=increase,crop={W}:{hh},fps=30"
            fc.append(f"[{last}]split[bs{j}][bc{j}]")
            fc.append(f"[bc{j}]crop={W}:{hh}:0:{ycrop}[bl{j}]")
            fc.append(f"[bs{j}][bl{j}]overlay=0:{H-hh}:enable='between(t,{t:.3f},{t+d:.3f})'[bb{j}]")
            fc.append(f"[{k}:v]{zp},drawbox=x=0:y=ih-{max(4, H//240)}:w=iw:h={max(4, H//240)}:color=white:t=fill,format=yuva420p,fade=t=in:st=0:d=0.12:alpha=1,fade=t=out:st={d-0.15:.3f}:d=0.15:alpha=1,setpts=PTS-STARTPTS+{t:.3f}/TB[c{j}]")
            fc.append(f"[bb{j}][c{j}]overlay=0:0:eof_action=pass:enable='between(t,{t:.3f},{t+d:.3f})'[g{k}]")
        elif kieu == "the_anh":
            cw = int(W * float(c.get("rong", 0.74))) // 2 * 2
            chh = int(cw * float(c.get("ti_le", 0.68))) // 2 * 2
            pre_ = f"scale={cw*2}:{chh*2}:force_original_aspect_ratio=increase,crop={cw*2}:{chh*2},zoompan=z='1+0.07*on/{n}':d=1:x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':s={cw}x{chh}:fps=30" if is_img else f"scale={cw}:{chh}:force_original_aspect_ratio=increase,crop={cw}:{chh},fps=30"
            bd = int(W * 0.014)
            R = int(((cw + 2*bd) ** 2 + (chh + 2*bd) ** 2) ** 0.5) // 2 * 2 + 4
            ang = float(c.get("nghieng", -4.0))
            rot = f"rotate='({ang}+({-ang*2.2:.2f})*max(0,1-t/0.35)^2)*PI/180':ow={R}:oh={R}:c=none"
            yc = int(H * float(c.get("y", 0.205)))  # phía trên đầu người nói
            fc.append(f"[{k}:v]{pre_},pad={cw+2*bd}:{chh+2*bd}:{bd}:{bd}:white,format=rgba,{rot},fade=t=in:st=0:d=0.12:alpha=1,fade=t=out:st={d-0.2:.3f}:d=0.2:alpha=1,setpts=PTS-STARTPTS+{t:.3f}/TB,split[c{j}][sh{j}]")
            fc.append(f"[sh{j}]colorchannelmixer=rr=0:gg=0:bb=0:aa=0.55,boxblur=18:2[shb{j}]")
            fc.append(f"[{last}][shb{j}]overlay=(W-w)/2+{int(W*0.02)}:{yc}-h/2+{int(W*0.03)}+max(0\\,140*(1-(t-{t:.3f})/0.3))*lt(t-{t:.3f}\\,0.3):eof_action=pass:enable='between(t,{t:.3f},{t+d:.3f})'[gs{k}]")
            fc.append(f"[gs{k}][c{j}]overlay=(W-w)/2:{yc}-h/2+max(0\\,140*(1-(t-{t:.3f})/0.3))*lt(t-{t:.3f}\\,0.3):eof_action=pass:enable='between(t,{t:.3f},{t+d:.3f})'[g{k}]")
        else:
            mv = c.get("chuyen_dong") or ["vao", "ra", "trai", "phai"][j % 4]
            if mv == "ra":
                zz, xx = f"1.12-0.10*on/{n}", "iw/2-iw/zoom/2"
            elif mv == "trai":
                zz, xx = "1.12", f"(iw-iw/zoom)*(1-on/{n})"
            elif mv == "phai":
                zz, xx = "1.12", f"(iw-iw/zoom)*on/{n}"
            else:
                zz, xx = f"1+0.10*on/{n}", "iw/2-iw/zoom/2"
            zp = f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},zoompan=z='{zz}':d=1:x='{xx}':y='ih/2-ih/zoom/2':s={W}x{H}:fps=30" if is_img else f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30"
            fc.append(f"[{k}:v]{zp},format=yuva420p,fade=t=in:st=0:d=0.12:alpha=1,fade=t=out:st={d-0.15:.3f}:d=0.15:alpha=1,setpts=PTS-STARTPTS+{t:.3f}/TB[c{j}]")
            fc.append(f"[{last}][c{j}]overlay=0:0:eof_action=pass:enable='between(t,{t:.3f},{t+d:.3f})'[g{k}]")
        last = f"g{k}"; k += 1
    if plan.get("logo", True) and LOGO and LOGO.exists():
        lw = int(W * 0.17)
        inputs += ["-i", LOGO]
        fc.append(f"[{k}:v]scale={lw}:-1,format=rgba,colorchannelmixer=aa=0.9[lg]")
        fc.append(f"[{last}][lg]overlay=W-w-{int(W*0.035)}:{int(H*0.03)}[g{k}]")
        last = f"g{k}"; k += 1
    fd = str(FONTS).replace(":", "\\:")
    fc.append(f"[{last}]ass='{ass}':fontsdir='{fd}',format=yuv420p[vout]")
    vid = tmp / "hinh.mp4"
    run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(fc), "-map", "[vout]", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "ultrafast" if draft else "slow", "-crf", "28" if draft else "17", "-pix_fmt", "yuv420p", "-an", vid])

    # 4) tiếng: giọng sạch + nhạc né giọng + SFX → -14 LUFS
    sfxd = tmp / "sfx"
    if not (sfxd / "whoosh.wav").exists():
        run(["python3", NHAC, "sfx", sfxd])
    ain = []
    has_voice = bool(lt) or (info["co_tieng"] and not am.get("tat_tieng_goc"))
    if lt:
        ain += ["-i", voice]
        keep = float(am.get("giu_tieng_goc", 0.0))
        if keep > 0 and info["co_tieng"]:
            ain += ["-i", cat_audio]
    else:
        ain += ["-i", cat]
    afc = []
    vchain = "highpass=f=75,afftdn=nf=-25,equalizer=f=3200:t=q:w=1.2:g=2.5,equalizer=f=250:t=q:w=1:g=-1.5,acompressor=threshold=0.08:ratio=3:attack=8:release=160:makeup=2"
    if lt:
        vchain = "highpass=f=70,acompressor=threshold=0.1:ratio=2.5:attack=8:release=160:makeup=1.5"
    afc.append(f"[0:a]{vchain if has_voice else 'anull'},apad,atrim=0:{total:.3f}[vo]")
    mixes = ["[vo]"]
    idx = len([x for x in ain if x == "-i"])
    if lt and float(am.get("giu_tieng_goc", 0)) > 0 and info["co_tieng"]:
        afc.append(f"[1:a]volume={float(am['giu_tieng_goc']):.2f},apad,atrim=0:{total:.3f}[og]")
        mixes.append("[og]")
    if music:
        ain += ["-stream_loop", "-1", "-i", music]
        mv = float(am.get("nhac_vol", 0.16 if has_voice else 0.85))
        afc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f},volume={mv},afade=t=out:st={max(0,total-1.5):.3f}:d=1.5[mu]")
        if has_voice:
            afc.append("[vo]asplit=2[vo1][key]")
            mixes[0] = "[vo1]"
            afc.append("[mu][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[mud]")
            mixes.append("[mud]")
        else:
            mixes.append("[mu]")
        idx += 1
    # SFX
    ev = []
    use_sfx = am.get("sfx", st["sfx"])
    if use_sfx:
        if (plan.get("hook") or {}).get("dong1"):
            ev.append(("thump", 0.0, 0.35))
        for p in pieces:
            if p["dau_doan"] and p["doan"] > 0:
                ev.append(("whoosh", max(0, p["o0"] - 0.2), 0.22))
    for c in cards:
        ev.append(("ding", c["_t"], 0.28 if use_sfx else 0.18))
    for c in chen:
        if use_sfx or c.get("kieu", "full") == "full":
            ev.append(("whoosh", max(0, c["_t"] - 0.2), 0.2 if use_sfx else 0.12))
    for kk in kins:
        kd = kk.get("kieu", "dap")
        if kd == "dap":
            ev.append(("thump", kk["_t"], 0.4)); ev.append(("whoosh", max(0, kk["_t"] - 0.15), 0.18))
        elif kd == "dem_so":
            ev.append(("rise", max(0, kk["_t"] - 0.3), 0.22)); ev.append(("ding", kk["_t"] + min(0.8, float(kk.get("dur", 1.8)) * 0.45), 0.3))
        elif kd == "xep_chu":
            ev.append(("pop", kk["_t"], 0.25))
    for s in plan.get("sfx", []):  # tự đặt: {"ten":"pop","t":3.2,"vol":0.3}
        ev.append((s["ten"], float(s["t"]), float(s.get("vol", 0.3))))
    for j, (nm, t, vol) in enumerate(ev):
        ain += ["-i", sfxd / f"{nm}.wav"]
        ms = int(t * 1000)
        afc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},adelay={ms}|{ms}[s{j}]")
        mixes.append(f"[s{j}]"); idx += 1
    afc.append(f"{''.join(mixes)}amix=inputs={len(mixes)}:normalize=0:duration=first,atrim=0:{total:.3f}[mix]")
    mixw = tmp / "mix.wav"
    run(["ffmpeg", "-v", "error", "-y"] + ain + ["-filter_complex", ";".join(afc), "-map", "[mix]", "-ar", "48000", "-c:a", "pcm_s24le", mixw])
    master = tmp / "master.wav"
    if draft:
        run(["ffmpeg", "-v", "error", "-y", "-i", mixw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", master])
    else:
        r = run(["ffmpeg", "-hide_banner", "-i", mixw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"])
        J = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
        run(["ffmpeg", "-v", "error", "-y", "-i", mixw, "-af",
             f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={J['input_i']}:measured_TP={J['input_tp']}:measured_LRA={J['input_lra']}:measured_thresh={J['input_thresh']}:offset={J['target_offset']}:linear=true,aresample=48000",
             "-c:a", "pcm_s24le", master])

    # 5) ảnh bìa (khung đầu tiên — đã có hook) + đóng gói
    bia_jpg = ra / f"{ten}_bia.jpg"
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-frames:v", "1", "-q:v", "2", bia_jpg])
    final = ra / f"{ten}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", master, "-i", bia_jpg, "-map", "0:v", "-map", "1:a", "-map", "2:v",
         "-c:v:0", "copy", "-c:a", "aac", "-b:a", "192k", "-c:v:1", "mjpeg", "-disposition:v:1", "attached_pic",
         "-movflags", "+faststart", "-t", f"{total:.3f}", final])
    if not draft:
        light = ra / f"{ten}_gui-nhanh.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-i", final, "-map", "0:v:0", "-map", "0:a", "-vf", "scale=720:1280:flags=lanczos", "-c:v", "libx264",
             "-preset", "medium", "-crf", "27", "-maxrate", "2M", "-bufsize", "4M", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", light])
    # lưới soát
    step = max(total / 12, 0.1)
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-vf", f"fps=1/{step:.3f},scale=270:-2,tile=6x2:padding=4", "-frames:v", "1", ra / "kiem_tra" / f"{ten}_luoi.jpg"])
    (tmp / "dong_thoi_gian.json").write_text(json.dumps({"tong": total, "manh": pieces, "chu": owords, "the": cards, "chen": chen}, ensure_ascii=False, indent=1))
    print(f"✔ {final}  ({total:.1f}s)\n  bìa: {bia_jpg}\n  soát: {ra/'kiem_tra'/(ten+'_luoi.jpg')}")
    return final


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    for pth in args:
        build(pth, "--nhap" in sys.argv)
