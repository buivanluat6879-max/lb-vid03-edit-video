# Bộ dựng video giá vàng 22/11 (giọng Hải Đăng + nhạc The Epic 2)

Chạy trên máy đã cài lb-vid03 (`~/.lbvid03`):

```
cd du_an/gia-vang-22-11/lam
python3 ~/.claude/skills/lb-vid03-edit-video/scripts/dung_video.py ke_hoach.json
```

- `goc/nen_infographic.mp4`: 8 trang infographic, 64,2s, đã khớp thời lượng 16 câu giọng Hải Đăng.
- `goc/epic2.ogg`: "The Epic 2" – Rafael Krux (CC BY 4.0), ghi credit trong caption.
- Giọng: `long_tieng.giong = "bac-nam"` → qua `tts_lenh` của máy (VieNeu Hải Đăng).
- Thành phẩm ra ở `du_an/gia-vang-22-11/ra/`.
