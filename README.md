# LB.VID03. EDIT VIDEO

**Skill cho Claude Code: edit video dọc 9:16 viral từ BẤT KỲ video gốc nào.** Bạn đưa video, Claude tự nghe, tự xem, lên kịch bản cắt cho bạn duyệt, rồi dựng thành phẩm như một editor chuyên nghiệp.

| Video gốc | Skill làm gì |
|---|---|
| Clip tự nói trước máy | Cắt khoảng lặng, cắt "ờ, ừm", câu đắt nhất lên đầu làm hook, bám mặt chuyển ngang thành dọc, zoom giấu vết cắt |
| Video dài (livestream, podcast, hội thảo) | Chấm điểm, xếp hạng các đoạn hay, cắt thành nhiều short tự đứng được |
| Cảnh quay không lời (dự án, flycam, nhà mẫu) | Chọn cảnh đẹp nhất, cắt khớp nhịp nhạc, đẩy máy, chữ thông tin |
| Video tải từ mạng (TikTok, YouTube, Douyin) | Gỡ băng tiếng nước ngoài, viết lại lời Việt, lồng tiếng, che phụ đề cứng |
| Video thuyết minh / infographic | Giữ trọn khung trên nền mờ, phụ đề mới, key text |

**Mọi video đều có:**
- **Phụ đề karaoke** từng chữ, khớp sóng âm, đã sửa chính tả.
- **Key text động:** số chạy, chữ đập, chữ xếp tầng, đánh máy.
- **B-roll ảnh thật tự tìm** từ thư mục của bạn, Wikimedia, Openverse và Pexels, chèn kiểu phủ kín, thẻ ảnh nghiêng hoặc chia đôi màn hình (không che mặt).
- **Màu và âm thanh:** chỉnh màu; nhạc tự nhỏ lại khi có giọng; hiệu ứng âm thanh; chuẩn -14 LUFS.
- **Ảnh bìa** có hook ngay khung đầu.
- **3 file thành phẩm:** 1080p, bản nhẹ 720p, file phụ đề `.srt`.

## Cài đặt

Cần có [Claude Code](https://claude.com/claude-code). Máy Mac cần thêm [Homebrew](https://brew.sh). Ubuntu chạy được. Windows chạy qua WSL.

```bash
git clone https://github.com/buivanluat6879-max/lb-vid03-edit-video.git
cd lb-vid03-edit-video
bash cai_dat.sh
```

Bộ cài làm 6 việc, tải khoảng 3 GB trong lần đầu. Chạy lại nhiều lần không sao, cái gì có rồi sẽ được bỏ qua.
1. Chép skill vào `~/.claude/skills/lb-vid03-edit-video`.
2. Cài `ffmpeg` và `whisper-cli`.
3. Tạo môi trường Python riêng có OpenCV, PyTorch và edge-tts.
4. Tải model nghe Whisper large-v3-turbo (1,6 GB) và model dò mặt YuNet.
5. Tải sẵn model căn chữ MMS_FA.
6. Tạo file cấu hình `~/.lbvid03/cau_hinh.json`.

## Dùng

Mở Claude Code rồi nói tự nhiên, ví dụ:

> edit video này thành reels: ~/Downloads/clip.mp4

> cắt livestream ~/Movies/live-12-11.mp4 thành 5 short hay nhất

> LB.VID03 làm video này, tự làm luôn không cần duyệt

Claude trình kịch bản cắt gồm: phong cách, hook, các đoạn giữ và bỏ, chỗ đặt key text và B-roll. Bạn duyệt xong, Claude dựng và tự soát rồi mới giao. Thành phẩm nằm trong `~/Movies/LBVID03/<ngày>_<tên>/ra/`.

## Tuỳ chỉnh: `~/.lbvid03/cau_hinh.json`

| Khoá | Ý nghĩa |
|---|---|
| `logo` | Ảnh PNG nền trong suốt, đóng ở góc phải trên. Bỏ trống thì không đóng logo. |
| `ten_kenh` | Tên kênh, dùng cho câu kêu gọi cuối video (CTA) và caption. |
| `nhac_mac_dinh` | File nhạc thật (giấy phép CC) cho video có lời. Bỏ trống thì skill tự tổng hợp nhạc không bản quyền. |
| `tts_lenh` | Lệnh lồng tiếng riêng: `<lệnh> <giọng> "<câu>" <out.wav> [tốc độ]`. Bỏ trống thì dùng edge-tts (giọng Microsoft Hoài My / Nam Minh, cần mạng). |
| `thu_muc_du_an` | Nơi tạo thư mục dự án. Mặc định `~/Movies/LBVID03`. |
| `thu_muc_anh` | Danh sách thư mục ảnh/video của bạn để skill tìm B-roll trước khi lên mạng. |
| `watermark_lenh` | Lệnh đóng watermark chống copy. Chỉ chạy khi bạn yêu cầu. |
| `python`, `whisper_model`, `yunet_model` | Đường dẫn công cụ. Bộ cài đã điền sẵn. |

Muốn B-roll là **video stock** (người, tiền, văn phòng…): lấy khoá API miễn phí ở [pexels.com/api](https://www.pexels.com/api/) rồi thêm `export PEXELS_API_KEY=...` vào `~/.zshrc`.

Kiểm tra máy đã đủ công cụ chưa: `python3 ~/.claude/skills/lb-vid03-edit-video/scripts/cau_hinh.py`

## Cấu trúc

```
SKILL.md              quy trình Claude làm theo
references/           chế độ theo loại video, phong cách, lược đồ ke_hoach.json
scripts/phan_tich.py  nghe + xem video (Whisper, căn chữ MMS_FA, khoảng lặng, cảnh, mặt)
scripts/dung_video.py dựng video từ ke_hoach.json (ffmpeg + phụ đề ASS)
scripts/tim_broll.py  tìm B-roll ảnh/video thật + ghi nguồn
scripts/nhac_nen.py   nhạc nền + SFX tự tổng hợp
scripts/cau_hinh.py   cấu hình từng máy
cai_dat.sh            bộ cài
```

## Giấy phép và ghi công

- **Code:** MIT (xem `LICENSE`).
- **Font Be Vietnam Pro:** SIL Open Font License 1.1 (`assets/fonts/OFL.txt`).
- **Model:**
  - Whisper (OpenAI, MIT) chạy qua whisper.cpp.
  - YuNet (OpenCV Zoo, MIT).
  - **MMS_FA** (Meta) dùng giấy phép **CC-BY-NC 4.0, chỉ cho mục đích phi thương mại**. Dùng cho mục đích thương mại thì xoá model này. Phụ đề khi đó dùng mốc thời gian của Whisper, kém khớp hơn một chút.
- **B-roll và nhạc tải về:** giữ đúng giấy phép của từng nguồn. `tim_broll.py` lưu tác giả và giấy phép vào `nguon.json`; hãy ghi nguồn trong caption khi đăng.
- **Video gốc của người khác:** chỉ dùng khi đã biến đổi đáng kể (bình luận, phân tích, lồng tiếng kèm góc nhìn riêng) và có ghi nguồn. Đăng lại nguyên bản có thể bị gỡ hoặc khoá kênh.
