#!/usr/bin/env python3
"""Cấu hình máy cho LB.VID03. EDIT VIDEO — mọi đường dẫn riêng của từng máy nằm ở đây, KHÔNG nằm trong code.

File cấu hình: ~/.lbvid03/cau_hinh.json (cai_dat.sh tự tạo). Có thể trỏ chỗ khác bằng biến môi trường LBV_CAU_HINH.
Mọi khoá đều tuỳ chọn; thiếu thì dùng mặc định trong ~/.lbvid03/.

  python3 cau_hinh.py              # in toàn bộ cấu hình đang dùng + kiểm tra thiếu gì
  python3 cau_hinh.py <khoa>       # in 1 giá trị (vd: python, thu_muc_du_an) — dùng trong lệnh shell

Khoá:
  python          python có OpenCV + torch + torchaudio (bám mặt, căn chữ)  [~/.lbvid03/venv/bin/python]
  whisper_model   model ggml cho whisper-cli                                  [~/.lbvid03/models/ggml-large-v3-turbo.bin]
  yunet_model     model dò mặt YuNet (.onnx)                                  [~/.lbvid03/models/face_detection_yunet_2023mar.onnx]
  tts_lenh        lệnh lồng tiếng riêng: <lenh> <giong> "<câu>" <out.wav> [tốc độ] — bỏ trống = dùng edge-tts (Microsoft, cần mạng)
  logo            ảnh logo PNG nền trong suốt đóng góc phải trên — bỏ trống = không đóng logo
  thu_muc_du_an   nơi tạo thư mục dự án video                                  [~/Movies/LBVID03]
  thu_muc_anh     danh sách thư mục ảnh/video của bạn để tim_broll tìm B-roll  [[thu_muc_du_an]]
  nhac_mac_dinh   file nhạc thật (CC) dùng mặc định cho video có lời — bỏ trống = tự tổng hợp
  ten_kenh        tên kênh/thương hiệu (để gợi ý CTA, caption)
  watermark_lenh  lệnh đóng watermark chống copy (chỉ chạy khi người dùng yêu cầu)
"""
import json, os, shutil, sys
from pathlib import Path

GOC = Path(os.environ.get("LBV_HOME", Path.home() / ".lbvid03"))
FILE = Path(os.environ.get("LBV_CAU_HINH", GOC / "cau_hinh.json"))

MAC_DINH = {
    "python": str(GOC / "venv/bin/python"),
    "whisper_model": str(GOC / "models/ggml-large-v3-turbo.bin"),
    "yunet_model": str(GOC / "models/face_detection_yunet_2023mar.onnx"),
    "tts_lenh": "",
    "logo": "",
    "thu_muc_du_an": str(Path.home() / "Movies/LBVID03"),
    "thu_muc_anh": [],
    "nhac_mac_dinh": "",
    "ten_kenh": "",
    "watermark_lenh": "",
}


def doc():
    c = dict(MAC_DINH)
    if FILE.exists():
        try:
            c.update({k: v for k, v in json.loads(FILE.read_text()).items() if v not in (None,)})
        except Exception as e:
            print(f"(cau_hinh.json lỗi: {e} — dùng mặc định)", file=sys.stderr)
    for k in c:  # biến môi trường LBV_<KHOA> ghi đè
        ev = os.environ.get("LBV_" + k.upper())
        if ev:
            c[k] = ev
    if not c["thu_muc_anh"]:
        c["thu_muc_anh"] = [c["thu_muc_du_an"]]
    elif isinstance(c["thu_muc_anh"], str):
        c["thu_muc_anh"] = [x for x in c["thu_muc_anh"].split(os.pathsep) if x]
    for k in ("python", "whisper_model", "yunet_model", "logo", "thu_muc_du_an", "nhac_mac_dinh"):
        if c[k]:
            c[k] = str(Path(os.path.expanduser(c[k])))
    c["thu_muc_anh"] = [str(Path(os.path.expanduser(x))) for x in c["thu_muc_anh"]]
    return c


C = doc()


def kiem_tra():
    loi = []
    for tool in ("ffmpeg", "ffprobe", "whisper-cli"):
        if not shutil.which(tool):
            loi.append(f"thiếu lệnh `{tool}` — chạy cai_dat.sh")
    for k in ("whisper_model", "yunet_model", "python"):
        if not Path(C[k]).exists():
            loi.append(f"thiếu {k}: {C[k]} — chạy cai_dat.sh")
    if C["logo"] and not Path(C["logo"]).exists():
        loi.append(f"logo không tồn tại: {C['logo']}")
    return loi


if __name__ == "__main__":
    if len(sys.argv) > 1:
        v = C.get(sys.argv[1], "")
        print(os.pathsep.join(v) if isinstance(v, list) else v)
    else:
        print(f"# {FILE} {'(có)' if FILE.exists() else '(chưa có — đang dùng mặc định)'}")
        print(json.dumps(C, ensure_ascii=False, indent=1))
        loi = kiem_tra()
        print("\n".join(["", "THIẾU:"] + ["  - " + x for x in loi]) if loi else "\nĐủ công cụ ✔")
