#!/usr/bin/env python3
"""Nhạc nền + hiệu ứng âm thanh TỰ TỔNG HỢP (không bản quyền, mỗi seed 1 bản khác).

  python3 nhac_nen.py nhac out.wav --dur 45 --kieu soi_dong|dien_anh|vui|nhe [--seed 3] [--bpm 124]
  python3 nhac_nen.py sfx <thu_muc>      → whoosh.wav, pop.wav, ding.wav, rise.wav, thump.wav

Kiểu nhạc:
  soi_dong  124 bpm, trống 4/4, bass nảy, pluck — viral nhịp nhanh, cảnh dự án, flycam
  dien_anh   92 bpm, pad ấm + piano rải + nhịp tim nhẹ — sang trọng, chuyên gia, BĐS cao cấp
  nhe       100 bpm, piano + pad mỏng, gần như không trống — nằm dưới giọng nói dài
  vui       ukulele/marimba dễ thương (gọi nhac_vui.py của skill sao chép kênh nếu có)
In ra 1 dòng JSON {"bpm":..., "dur":...} để bộ dựng khớp nhịp cắt.
"""
import argparse, json, subprocess, sys, wave
from pathlib import Path
import numpy as np

SR = 44100
KEYS = [57, 60, 62, 64, 65, 67]          # A C D E F G
MINOR_PROGS = [[1, 6, 3, 7], [1, 4, 6, 5], [6, 4, 1, 5], [1, 7, 6, 7]]
MAJOR_PROGS = [[1, 5, 6, 4], [4, 1, 5, 6], [1, 6, 4, 5], [6, 4, 1, 5]]
MAJ = [0, 2, 4, 5, 7, 9, 11]
MIN = [0, 2, 3, 5, 7, 8, 10]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a=0.005, r=0.2, sustain=1.0):
    e = np.ones(n) * sustain
    na, nr = max(1, int(a * SR)), max(1, min(n, int(r * SR)))
    e[:na] = np.linspace(0, sustain, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def chord(deg, scale, root):
    i = deg - 1
    return [root + scale[(i + k) % 7] + 12 * ((i + k) // 7) for k in (0, 2, 4)]


def add(buf, sig, at):
    i = int(at * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def saw(f, n, det=0.0):
    t = np.arange(n) / SR
    s = 0
    for d in (-det, 0, det) if det else (0,):
        ph = (t * f * (1 + d)) % 1.0
        s = s + (2 * ph - 1)
    return s / (3 if det else 1)


def lowpass(x, cut):
    a = np.exp(-2 * np.pi * cut / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # đủ nhanh cho vài chục giây
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def lp_fast(x, cut):
    # lọc 1 cực bằng FFT (nhanh cho tín hiệu dài)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / cut) ** 4), len(x))


def kick(n=int(0.35 * SR)):
    t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def snare(rng, n=int(0.22 * SR)):
    t = np.arange(n) / SR
    return (rng.standard_normal(n) * 0.6 + np.sin(2 * np.pi * 190 * t) * 0.4) * np.exp(-t * 18)


def hat(rng, n=int(0.05 * SR)):
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))  # thông cao thô
    return x * np.exp(-np.arange(n) / SR * 70) * 0.5


def piano(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * k * t) * (0.6 / k ** 1.4) for k in range(1, 6))
    return s * np.exp(-t * 2.2) * env(n, 0.003, 0.15)


def pad(freqs, dur):
    n = int(dur * SR)
    s = sum(saw(f, n, 0.004) for f in freqs) / len(freqs)
    s = lp_fast(s, 900)
    return s * env(n, 0.6, 0.8)


def pluck(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = saw(f, n) * np.exp(-t * 9)
    return lp_fast(s, 2500) * env(n, 0.002, 0.05)


def song(kieu, dur, seed, bpm=None):
    rng = np.random.default_rng(seed)
    bpm = bpm or {"soi_dong": 124, "dien_anh": 92, "nhe": 100}[kieu]
    beat = 60 / bpm
    bar = beat * 4
    root = int(rng.choice(KEYS))
    minor = kieu == "dien_anh" or (kieu == "soi_dong" and rng.random() < 0.6)
    scale = MIN if minor else MAJ
    prog = (MINOR_PROGS if minor else MAJOR_PROGS)[int(rng.integers(4))]
    total = dur + 1.0
    N = int(total * SR)
    L = {k: np.zeros(N) for k in ("drum", "bass", "harm", "lead")}
    nbars = int(np.ceil(total / bar))
    arp_pat = rng.permutation([0, 1, 2, 1, 2, 0, 2, 1])
    for b in range(nbars):
        t0 = b * bar
        ch = chord(prog[b % 4], scale, root)
        intro = b < 1
        # hoà âm
        if kieu in ("dien_anh", "nhe"):
            add(L["harm"], pad([hz(m) for m in ch], bar + 0.5) * 0.5, t0)
            step = beat / 2
            for k in range(8):
                m = ch[arp_pat[k] % 3] + 12
                add(L["lead"], piano(hz(m), beat * 1.5) * (0.35 if kieu == "dien_anh" else 0.45), t0 + k * step)
        else:
            for k in range(8):  # pluck offbeat
                m = ch[arp_pat[k] % 3] + 12
                add(L["lead"], pluck(hz(m), beat * 0.45) * 0.35, t0 + k * beat / 2 + (beat / 4 if k % 2 else 0) * 0)
            add(L["harm"], pad([hz(m) for m in ch], bar) * 0.25, t0)
        # bass
        if kieu == "soi_dong":
            for k in range(8):
                f = hz(ch[0] - 24)
                add(L["bass"], pluck(f, beat * 0.4) * (0.9 if k % 2 else 0.6), t0 + k * beat / 2 + beat / 4)
        elif kieu == "dien_anh":
            add(L["bass"], np.sin(2 * np.pi * hz(ch[0] - 24) * np.arange(int(bar * SR)) / SR) * env(int(bar * SR), 0.2, 0.6) * 0.5, t0)
        # trống
        if intro:
            continue
        for k in range(4):
            tb = t0 + k * beat
            if kieu == "soi_dong":
                add(L["drum"], kick() * 0.9, tb)
                if k in (1, 3):
                    add(L["drum"], snare(rng) * 0.35, tb)
                add(L["drum"], hat(rng) * 0.5, tb + beat / 2)
            elif kieu == "dien_anh":
                if k == 0:
                    add(L["drum"], kick() * 0.55, tb)
                    add(L["drum"], kick() * 0.35, tb + beat * 0.5)
            elif kieu == "nhe" and k == 0 and b % 2 == 0:
                add(L["drum"], kick() * 0.3, tb)
    mix = L["drum"] * 0.9 + L["bass"] * 0.7 + L["harm"] * 0.6 + L["lead"] * 0.7
    # nén mềm + chuẩn hoá + fade
    mix = np.tanh(mix * 1.4)
    mix = mix[: int(dur * SR)]
    mix /= max(1e-6, np.abs(mix).max()) / 0.85
    fi, fo = int(0.05 * SR), int(min(2.0, dur / 4) * SR)
    mix[:fi] *= np.linspace(0, 1, fi)
    mix[-fo:] *= np.linspace(1, 0, fo)
    return mix, bpm


def write(path, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], 1) if x.ndim == 1 else x
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def sfx(dir_):
    d = Path(dir_); d.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    # whoosh: nhiễu quét lọc, to dần rồi tắt
    n = int(0.45 * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    X = np.fft.rfft(noise); f = np.fft.rfftfreq(n, 1 / SR)
    w = np.fft.irfft(X * np.exp(-((f - 1800) / 1500) ** 2), n)
    e = np.sin(np.pi * np.clip(t / 0.45, 0, 1)) ** 2
    write(d / "whoosh.wav", w / np.abs(w).max() * e * 0.8)
    # pop: chấm tròn khi bật chữ
    n = int(0.09 * SR); t = np.arange(n) / SR
    fr = 900 * np.exp(-t * 25) + 300
    write(d / "pop.wav", np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 45) * 0.8)
    # ding: chuông số liệu
    n = int(0.9 * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * 1318.5 * k * t) * a for k, a in ((1, 1), (2.76, .4), (5.4, .2))) * np.exp(-t * 6)
    write(d / "ding.wav", s / np.abs(s).max() * 0.6)
    # rise: lên dần trước điểm nhấn
    n = int(1.2 * SR); t = np.arange(n) / SR
    s = saw(1, n) * 0
    fr = 200 + 1400 * (t / 1.2) ** 2
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * 0.3 + rng.standard_normal(n) * 0.15 * (t / 1.2)
    write(d / "rise.wav", s * (t / 1.2) ** 1.5 * 0.8)
    # thump: tiếng dội trầm cho hook/tiêu đề
    write(d / "thump.wav", kick(int(0.6 * SR)) * 0.95)
    print(json.dumps({"sfx": [p.name for p in sorted(d.glob('*.wav'))]}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lenh", choices=["nhac", "sfx"])
    ap.add_argument("out")
    ap.add_argument("--dur", type=float, default=45)
    ap.add_argument("--kieu", default="dien_anh", choices=["soi_dong", "dien_anh", "nhe", "vui"])
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--bpm", type=int)
    a = ap.parse_args()
    if a.lenh == "sfx":
        return sfx(a.out)
    if a.kieu == "vui":
        nv = Path.home() / ".claude/skills/lb-vid-mxh-sao-chep-kenh/scripts/nhac_vui.py"
        if nv.exists():
            cmd = [sys.executable, str(nv), a.out, "--dur", str(a.dur), "--seed", str(a.seed)] + (["--bpm", str(a.bpm)] if a.bpm else [])
            subprocess.run(cmd, check=True, capture_output=True)
            print(json.dumps({"bpm": a.bpm or 116, "dur": a.dur}))
            return
        a.kieu = "soi_dong"
    x, bpm = song(a.kieu, a.dur, a.seed, a.bpm)
    write(a.out, x)
    print(json.dumps({"bpm": bpm, "dur": a.dur}))


if __name__ == "__main__":
    main()
