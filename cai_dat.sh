#!/usr/bin/env bash
# LB.VID03. EDIT VIDEO — cài đặt một lần.
#   git clone https://github.com/buivanluat6879-max/lb-vid03-edit-video.git
#   cd lb-vid03-edit-video && bash cai_dat.sh
# Hỗ trợ macOS (Homebrew) và Ubuntu/Debian. Windows: dùng WSL (Ubuntu).
# Tải về khoảng 3 GB (model Whisper 1,6 GB + PyTorch). Chạy lại nhiều lần không sao: cái gì có rồi sẽ bỏ qua.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
LBV="${LBV_HOME:-$HOME/.lbvid03}"
SKILL_DIR="$HOME/.claude/skills/lb-vid03-edit-video"
xanh() { printf "\033[32m%s\033[0m\n" "$*"; }
vang() { printf "\033[33m%s\033[0m\n" "$*"; }

xanh "[1/6] Chép skill vào Claude Code: $SKILL_DIR"
if [ "$HERE" != "$SKILL_DIR" ]; then
  mkdir -p "$SKILL_DIR"
  (cd "$HERE" && tar --exclude .git -cf - .) | (cd "$SKILL_DIR" && tar -xf -)
fi

xanh "[2/6] Công cụ hệ thống: ffmpeg, whisper-cli, python3"
OS="$(uname -s)"
if [ "$OS" = "Darwin" ]; then
  command -v brew >/dev/null || { vang "Cần Homebrew: https://brew.sh — cài xong chạy lại."; exit 1; }
  command -v ffmpeg >/dev/null || brew install ffmpeg
  command -v whisper-cli >/dev/null || brew install whisper-cpp
  command -v python3 >/dev/null || brew install python@3.12
else
  sudo apt-get update -y && sudo apt-get install -y ffmpeg python3 python3-venv git cmake build-essential curl
  if ! command -v whisper-cli >/dev/null; then
    vang "Biên dịch whisper.cpp (vài phút)…"
    rm -rf "$LBV/whisper.cpp" && git clone --depth 1 https://github.com/ggml-org/whisper.cpp "$LBV/whisper.cpp"
    (cd "$LBV/whisper.cpp" && cmake -B build -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build build -j --config Release >/dev/null)
    sudo install -m 755 "$LBV/whisper.cpp/build/bin/whisper-cli" /usr/local/bin/whisper-cli
  fi
fi
ffmpeg -hide_banner -filters 2>/dev/null | grep -q " ass " || vang "ffmpeg thiếu bộ lọc 'ass' (libass) — phụ đề sẽ không vẽ được. macOS: brew reinstall ffmpeg"

xanh "[3/6] Môi trường Python riêng: $LBV/venv (OpenCV, PyTorch, edge-tts)"
mkdir -p "$LBV/models"
[ -x "$LBV/venv/bin/python" ] || python3 -m venv "$LBV/venv"
"$LBV/venv/bin/pip" install -q --upgrade pip
"$LBV/venv/bin/pip" install -q numpy pillow opencv-python edge-tts "torch>=2.1,<2.9" "torchaudio>=2.1,<2.9"

xanh "[4/6] Model nghe (Whisper large-v3-turbo, 1,6 GB) + model dò mặt (YuNet)"
W="$LBV/models/ggml-large-v3-turbo.bin"
[ -s "$W" ] && [ "$(wc -c <"$W")" -gt 1600000000 ] || curl -L -C - --retry 5 -o "$W" \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
Y="$LBV/models/face_detection_yunet_2023mar.onnx"
[ -s "$Y" ] || curl -L --retry 5 -o "$Y" \
  https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx

xanh "[5/6] Model căn chữ theo sóng âm (MMS_FA, tải lần đầu ~1,2 GB)"
"$LBV/venv/bin/python" -c "from torchaudio.pipelines import MMS_FA as B; B.get_model(); print('  MMS_FA sẵn sàng')" 2>/dev/null \
  || vang "  Chưa tải được MMS_FA — phụ đề vẫn chạy bằng mốc Whisper (kém khớp hơn). Thử lại sau."

xanh "[6/6] File cấu hình: $LBV/cau_hinh.json"
if [ ! -f "$LBV/cau_hinh.json" ]; then
  cat > "$LBV/cau_hinh.json" <<EOF
{
 "python": "$LBV/venv/bin/python",
 "whisper_model": "$W",
 "yunet_model": "$Y",
 "tts_lenh": "",
 "logo": "",
 "thu_muc_du_an": "$HOME/Movies/LBVID03",
 "thu_muc_anh": [],
 "nhac_mac_dinh": "",
 "ten_kenh": "",
 "watermark_lenh": ""
}
EOF
fi
mkdir -p "$HOME/Movies/LBVID03" 2>/dev/null || true
python3 "$SKILL_DIR/scripts/cau_hinh.py" | tail -3
echo
xanh "XONG. Mở Claude Code và nói: \"edit video này thành reels: <đường dẫn video>\""
echo "Tuỳ chỉnh logo / tên kênh / nhạc mặc định / giọng đọc: sửa $LBV/cau_hinh.json (xem README.md)."
