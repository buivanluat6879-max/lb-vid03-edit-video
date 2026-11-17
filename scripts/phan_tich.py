#!/usr/bin/env python3
"""BƯỚC 1 — Nghe + xem video gốc, ghi mọi thứ cần để lên kế hoạch cắt.

Dùng (tự chuyển sang python trong cấu hình nếu python hiện tại thiếu OpenCV/torch; thiếu hẳn thì vẫn chạy, bỏ phần mặt/căn chữ):
  python3 phan_tich.py <video> <thu_muc_lam_viec> [--ngon-ngu vi|auto|en|zh] [--khong-mat]

Ghi ra thư mục làm việc:
  phan_tich.json  — số liệu máy đọc: thông số, câu + từng chữ có mốc giây, khoảng lặng, điểm chuyển cảnh, mặt người, độ sáng, độ to
  phan_tich.md    — bản người đọc: tóm tắt + lời thoại theo câu có mốc giây (để chọn đoạn giữ)
  luoi.jpg        — lưới 4x4 khung hình rải đều (XEM ảnh này để biết video trông thế nào)
  a16.wav         — âm thanh 16 kHz (dùng lại khi cần)
"""
import argparse, json, os, re, subprocess, sys, unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cau_hinh import C  # noqa: E402

WHISPER = Path(C["whisper_model"])
YUNET = Path(C["yunet_model"])


def _dung_python_cau_hinh():
    """Python đang chạy thiếu cv2/torch mà python trong cấu hình có -> chạy lại bằng python đó."""
    try:
        import cv2, torch  # noqa: F401
        return
    except ImportError:
        pass
    py = C["python"]
    if Path(py).exists() and Path(py).resolve() != Path(sys.executable).resolve() and not os.environ.get("LBV_DA_CHUYEN"):
        os.environ["LBV_DA_CHUYEN"] = "1"
        os.execv(py, [py] + sys.argv)


def run(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)


def probe(src):
    j = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", src]).stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    if not v:
        sys.exit("Không thấy luồng hình trong file.")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    rot = int(v.get("tags", {}).get("rotate", rot) or 0)
    if abs(rot) % 180 == 90:
        w, h = h, w
    n, d = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1").split("/")
    fps = float(n) / float(d) if float(d) else 30.0
    return {"w": w, "h": h, "fps": round(fps, 3), "dur": round(float(j["format"]["duration"]), 3),
            "co_tieng": a is not None, "codec": v.get("codec_name"), "rotate": rot}


def parse_srt_time(s):
    h, m, rest = s.split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def speech_groups(sil, dur, maxlen=24.0, pad=0.15):
    """Vùng có tiếng (ngoài khoảng lặng), gộp liền nhau tới ~24s/cụm để Whisper không bỏ sót."""
    regs, t = [], 0.0
    for a, b in sil:
        if a - t > 0.12:
            regs.append([t, a])
        t = b
    if dur - t > 0.12:
        regs.append([t, dur])
    groups = []
    for a, b in regs:
        while b - a > maxlen:  # một hơi nói quá dài -> chẻ cứng
            groups.append([a, a + maxlen]); a += maxlen
        if groups and b - groups[-1][0] <= maxlen and a - groups[-1][1] < 1.5:
            groups[-1][1] = b
        else:
            groups.append([a, b])
    return [[max(0.0, a - pad), min(dur, b + pad)] for a, b in groups]


DIGITS = "không một hai ba bốn năm sáu bảy tám chín".split()


def doc3(n, full):
    tr, ch, dv = n // 100, n % 100 // 10, n % 10
    out = []
    if full or tr:
        out += [DIGITS[tr], "trăm"]
    if ch == 0:
        if dv and (full or tr):
            out.append("linh")
    elif ch == 1:
        out.append("mười")
    else:
        out += [DIGITS[ch], "mươi"]
    if dv:
        if dv == 1 and ch > 1:
            out.append("mốt")
        elif dv == 5 and ch > 0:
            out.append("lăm")
        elif dv == 4 and ch > 1:
            out.append("tư")
        else:
            out.append(DIGITS[dv])
    return out


def doc_so(n):
    if n == 0:
        return ["không"]
    units = ["", "nghìn", "triệu", "tỷ"]
    groups = []
    while n:
        groups.append(n % 1000); n //= 1000
    out = []
    for i in range(len(groups) - 1, -1, -1):
        g = groups[i]
        if g == 0:
            continue
        out += doc3(g, full=bool(out)) + ([units[i % 4]] if units[i % 4] else [])
    return out


def spoken(word):
    """Chữ hiển thị -> các âm tiết đọc thật (để căn mốc): '30%' -> ba mươi phần trăm."""
    w = word.lower().strip(".,!?…:;\"'()[]")
    m = re.fullmatch(r"(\d+(?:[.,]\d+)*)(%?)", w)
    if m:
        num, pct = m.groups()
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", num):
            num = num.replace(".", "")
        if "," in num or ("." in num and not re.fullmatch(r"\d+", num)):
            a, b = re.split(r"[.,]", num, 1)
            out = doc_so(int(a)) + ["phẩy"] + [DIGITS[int(c)] for c in b]
        else:
            out = doc_so(int(num))
        return out + (["phần", "trăm"] if pct else [])
    return [x for x in re.split(r"[-/]", w) if x]


def roman(w):
    w = unicodedata.normalize("NFD", w.lower().replace("đ", "d"))
    return re.sub(r"[^a-z]", "", "".join(c for c in w if not unicodedata.combining(c)))


class Aligner:
    """Căn từng chữ vào sóng âm bằng torchaudio MMS_FA (chính xác hơn mốc Whisper nhiều). Thiếu torch -> None."""
    def __init__(self, wav16):
        import numpy as np, torch
        from torchaudio.pipelines import MMS_FA as B
        self.np, self.torch, self.B = np, torch, B
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(wav16), "-ac", "1", "-ar", str(B.sample_rate), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        self.y = np.frombuffer(raw, np.float32).copy()
        self.model, self.tok, self.al = B.get_model(), B.get_tokenizer(), B.get_aligner()

    def align(self, a, b, words):
        sr = self.B.sample_rate
        seg = self.y[int(a * sr):int(b * sr)]
        units = []
        for w in words:
            toks = [roman(x) for x in spoken(w["text"])]
            units.append([t for t in toks if t])
        flat = [t for u in units for t in u]
        if not flat or len(seg) < sr * 0.2:
            return False
        with self.torch.inference_mode():
            em, _ = self.model(self.torch.from_numpy(seg)[None])
            spans = self.al(em[0], self.tok(flat))
        ratio = len(seg) / em.shape[1] / sr
        i = 0
        for w, u in zip(words, units):
            if not u:
                continue
            sp = spans[i:i + len(u)]; i += len(u)
            w["t0"] = round(a + sp[0][0].start * ratio, 3)
            w["t1"] = round(a + sp[-1][-1].end * ratio, 3)
        # chữ không đọc được (ký hiệu) -> kẹp giữa 2 chữ bên cạnh
        for k, (w, u) in enumerate(zip(words, units)):
            if not u:
                prev = words[k - 1]["t1"] if k else a
                w["t0"] = w["t1"] = prev
        return True


def transcribe(wav16, sil, dur, wd, lang):
    """Gỡ băng từng chữ: cắt cụm theo khoảng lặng, chạy whisper-cli 1 lần cho mọi cụm, cộng lại mốc giây."""
    cd = wd / "cum"
    cd.mkdir(exist_ok=True)
    for f in cd.glob("*"):
        f.unlink()
    groups = speech_groups(sil, dur)
    files = []
    for i, (a, b) in enumerate(groups):
        f = cd / f"c{i:04d}.wav"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", wav16, "-c", "copy", f])
        files.append(f)
    words, detected = [], lang
    try:
        AL = Aligner(wav16) if lang in ("vi", "auto") else None
    except Exception as e:  # không có torch/torchaudio -> giữ mốc Whisper
        print(f"    (không căn được theo sóng âm: {e.__class__.__name__}; dùng mốc Whisper)")
        AL = None
    for k in range(0, len(files), 150):
        batch = files[k:k + 150]
        r = run(["whisper-cli", "-m", WHISPER, "-l", lang, "-np", "-ml", "1", "-sow", "-oj", "-nf"] + batch)
        if r.returncode:
            print(r.stderr[-600:], file=sys.stderr)
    for f, (a, b) in zip(files, groups):
        jp = Path(str(f) + ".json")
        if not jp.exists():
            continue
        j = json.loads(jp.read_text(errors="replace"))
        detected = j.get("result", {}).get("language", detected)
        gw = []
        for x in j.get("transcription", []):
            t = x.get("text", "").strip()
            if not t or t.startswith("["):
                continue
            o = x["offsets"]
            w0, w1 = a + o["from"] / 1000, a + o["to"] / 1000
            if gw and t == gw[-1]["text"] and w0 - gw[-1]["t1"] < 0.05 and len(t) > 3:
                continue  # chặn lặp ảo giác
            gw.append({"t0": round(w0, 3), "t1": round(min(w1, b), 3), "text": t})
        if AL and gw and detected == "vi":
            try:
                AL.align(a, b, gw)
            except Exception as e:
                print(f"    căn cụm {a:.1f}s lỗi ({e.__class__.__name__}) — giữ mốc Whisper")
        words += gw
    return words, detected


def sentences(words, gap=0.55, maxw=30):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        end = (w["text"][-1] in ".?!…" or nxt is None or (nxt["t0"] - w["t1"] > gap) or len(cur) >= maxw
               or (w["text"][-1] in ",;:" and len(cur) >= 16))
        if end:
            out.append({"id": len(out) + 1, "t0": cur[0]["t0"], "t1": cur[-1]["t1"],
                        "text": " ".join(x["text"] for x in cur), "words": cur})
            cur = []
    return out


def silences(src, dur, db=None, d=0.25):
    """Khoảng lặng. Video có nhạc nền lót dưới giọng thì -35 dB không bao giờ "lặng" -> tự nâng ngưỡng tới khi tìm được."""
    if db is None:
        for t in (-35, -30, -26, -22):
            s = silences(src, dur, t, d)
            if len(s) >= max(3, dur / 15):
                return s
        return s
    err = run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"silencedetect=n={db}dB:d={d}", "-f", "null", "-"]).stderr
    ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    se += [dur] * (len(ss) - len(se))
    return [[round(a, 3), round(b, 3)] for a, b in zip(ss, se)]


def scenes(src, thr=0.32):
    err = run(["ffmpeg", "-hide_banner", "-i", src, "-vf", f"scale=320:-2,select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"]).stderr
    return [round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", err)]


def loudness(src):
    err = run(["ffmpeg", "-hide_banner", "-i", src, "-af", "ebur128", "-f", "null", "-"]).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    return float(m[-1]) if m else None


def luma(src):
    err = run(["ffmpeg", "-hide_banner", "-i", src, "-vf", "fps=1,scale=160:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-an", "-f", "null", "-"]).stderr
    v = [float(x) for x in re.findall(r"YAVG=([\d.]+)", err)]
    return round(sum(v) / len(v), 1) if v else None


def faces(src, info, step=0.5):
    """Mặt lớn nhất mỗi 0,5 giây -> [{t, cx, cy, w, h}] theo tỉ lệ khung (0..1)."""
    try:
        import cv2
    except ImportError:
        return None
    if not YUNET.exists():
        return None
    cap = cv2.VideoCapture(str(src))
    out, t = [], 0.0
    det = None
    while t < info["dur"]:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if not ok:
            break
        H, W = f.shape[:2]
        s = 640 / max(W, H)
        small = cv2.resize(f, (int(W * s), int(H * s)))
        if det is None:
            det = cv2.FaceDetectorYN.create(str(YUNET), "", (small.shape[1], small.shape[0]), 0.6)
        det.setInputSize((small.shape[1], small.shape[0]))
        _, fs = det.detect(small)
        if fs is not None and len(fs):
            x, y, w, h = [float(v) for v in max(fs, key=lambda r: r[2] * r[3])[:4] / s]
            out.append({"t": round(t, 2), "cx": round((x + w / 2) / W, 4), "cy": round((y + h / 2) / H, 4),
                        "w": round(w / W, 4), "h": round(h / H, 4)})
        t += step
    return out


def contact_sheet(src, dur, out):
    n = 16
    step = max(dur / n, 0.04)
    vf = f"fps=1/{step:.4f},scale=360:-2,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='%{{pts\\:hms}}':x=6:y=6:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=4x4:padding=4"
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-frames:v", "1", "-q:v", "3", out])


def doan_kieu(info, speech_ratio, n_scenes, face_ratio=1.0):
    if not info["co_tieng"] or speech_ratio < 0.15:
        return "canh"  # cảnh quay không lời / chỉ có nhạc
    if face_ratio < 0.2:
        return "thuyet_minh"  # có lời nhưng không có mặt người: giọng đọc trên hình/infographic/màn hình
    if info["dur"] > 150:
        return "dai"
    return "noi"


def main():
    _dung_python_cau_hinh()
    if not WHISPER.exists():
        sys.exit(f"Thiếu model Whisper: {WHISPER}\nChạy cai_dat.sh (hoặc sửa whisper_model trong ~/.lbvid03/cau_hinh.json).")
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("wd")
    ap.add_argument("--ngon-ngu", default="vi")
    ap.add_argument("--khong-mat", action="store_true")
    a = ap.parse_args()
    src = Path(a.src).expanduser().resolve()
    wd = Path(a.wd).expanduser().resolve()
    wd.mkdir(parents=True, exist_ok=True)

    info = probe(src)
    print(f"[1/6] {info['w']}x{info['h']} {info['fps']}fps {info['dur']}s tiếng={'có' if info['co_tieng'] else 'không'}")

    sents, words, sil, lufs = [], [], [], None
    lang = a.ngon_ngu
    if info["co_tieng"]:
        wav = wd / "a16.wav"
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav])
        sil = silences(src, info["dur"])
        print("[2/6] gỡ băng từng chữ (Whisper large-v3-turbo)…")
        words, lang = transcribe(wav, sil, info["dur"], wd, lang)
        print(f"[3/6] {len(words)} chữ")
        sents = sentences(words)
        lufs = loudness(src)
    else:
        print("[2-3/6] không có tiếng — bỏ gỡ băng")

    print("[4/6] dò chuyển cảnh + độ sáng…")
    sc = scenes(src)
    y = luma(src)

    fc = None
    if not a.khong_mat:
        print("[5/6] bám mặt người…")
        fc = faces(src, info)
        if fc is None:
            print("    (python này không có OpenCV — bỏ qua bám mặt; dùng python trong tools/.venv để có)")

    print("[6/6] lưới khung hình…")
    contact_sheet(src, info["dur"], wd / "luoi.jpg")
    if sc:  # mỗi cảnh 1 ảnh (giữa cảnh) có ghi giây — để chọn cảnh đẹp khi dựng không lời
        bounds = [0.0] + sc + [info["dur"]]
        mids = [(a + b) / 2 for a, b in zip(bounds, bounds[1:]) if b - a > 0.6][:48]
        cdir = wd / "canh"; cdir.mkdir(exist_ok=True)
        for i, m in enumerate(mids):
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{m:.2f}", "-i", src, "-frames:v", "1", "-vf",
                 f"scale=360:-2,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='{m:.1f}s':x=6:y=6:fontsize=24:fontcolor=yellow:box=1:boxcolor=black@0.6",
                 "-q:v", "4", cdir / f"c{i:02d}.jpg"])
        run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", cdir / "c%02d.jpg", "-vf", "tile=6x8:padding=4", "-frames:v", "1", "-q:v", "3", wd / "luoi_canh.jpg"])

    talk = sum(s["t1"] - s["t0"] for s in sents)
    ratio = talk / info["dur"] if info["dur"] else 0
    face_ratio = (len(fc) / max(1, int(info["dur"] / 0.5))) if fc else 0
    kieu = doan_kieu(info, ratio, len(sc), face_ratio if fc is not None else 1.0)
    data = {"nguon": str(src), "thong_so": info, "ngon_ngu": lang, "kieu_doan": kieu,
            "ti_le_noi": round(ratio, 2), "ti_le_co_mat": round(face_ratio, 2),
            "do_sang_tb": y, "do_to_lufs": lufs, "chuyen_canh": sc, "khoang_lang": sil,
            "cau": sents, "mat": fc or []}
    (wd / "phan_tich.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))

    L = [f"# Phân tích: {src.name}", "",
         f"- Khung {info['w']}x{info['h']} · {info['fps']} fps · {info['dur']} s · tiếng: {'có' if info['co_tieng'] else 'KHÔNG'}",
         f"- Ngôn ngữ: {lang} · thời lượng nói {talk:.1f}s ({ratio:.0%}) · mặt người xuất hiện {face_ratio:.0%} mẫu",
         f"- Độ sáng TB (0-255): {y} {'→ TỐI, cần nâng sáng' if y and y < 75 else ''} · độ to: {lufs} LUFS",
         f"- Chuyển cảnh: {len(sc)} lần · khoảng lặng ≥0,25s: {len(sil)} đoạn",
         f"- Máy đoán loại: **{kieu}** (noi = nói trước máy · dai = video dài cắt nhiều short · canh = cảnh không lời · thuyet_minh = giọng đọc trên hình, không mặt người)", "",
         "## Lời thoại theo câu (mốc giây gốc)", ""]
    for s in sents:
        L.append(f"[{s['id']:>3}] {s['t0']:7.2f}–{s['t1']:7.2f}  {s['text']}")
    if sc:
        L += ["", "## Điểm chuyển cảnh (giây)", ", ".join(f"{x:.1f}" for x in sc[:200])]
    (wd / "phan_tich.md").write_text("\n".join(L))
    print(f"Xong → {wd/'phan_tich.md'}  ·  XEM {wd/'luoi.jpg'}")


if __name__ == "__main__":
    main()
