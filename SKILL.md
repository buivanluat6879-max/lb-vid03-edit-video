---
name: lb-vid03-edit-video
description: LB.VID03. EDIT VIDEO — Edit video ĐỈNH CAO từ BẤT KỲ video gốc nào thành video dọc 9:16 viral 30–90 giây — clip tự nói trước máy, video dài (livestream/podcast/hội thảo) cắt thành nhiều short, cảnh quay không lời (dự án, flycam, nhà mẫu), video tải từ mạng (TikTok/YouTube/Douyin, lồng tiếng Việt), video thuyết minh/infographic. Tự nghe + xem video, chọn đoạn hay nhất, đưa câu đắt nhất lên làm hook, cắt khoảng lặng và từ đệm, bám mặt chuyển ngang thành dọc, zoom giật giấu vết cắt, phụ đề karaoke từng chữ khớp sóng âm (sửa chính tả), KEY TEXT động (số chạy, chữ đập, chữ xếp tầng), B-ROLL THẬT tự tìm (ảnh dự án, Wikimedia, Openverse, Pexels) dạng phủ kín / thẻ ảnh nghiêng / chia đôi màn hình, chỉnh màu, nhạc né giọng, SFX, chuẩn -14 LUFS, ảnh bìa có hook. Dùng skill này khi người dùng gửi/chỉ tới một file video và muốn "edit", "dựng lại", "cắt ghép", "làm đẹp video", "biến thành reels/tiktok/shorts", "cắt clip hay từ livestream", "thêm phụ đề", "cắt khoảng lặng", "thêm key text, b-roll", "làm video viral từ clip này", "edit giống các kênh triệu view", gọi mã "LB.VID03" / "LB.VID03 edit video", kể cả khi họ chỉ đưa video và nói "làm đi". (Video tạo từ đầu không có footage gốc — bản đồ, infographic, AI — thì ưu tiên skill chuyên cho dạng đó nếu máy có.)
---

# LB.VID03. EDIT VIDEO — edit video đỉnh cao từ bất kỳ video gốc nào

Mục tiêu: thành phẩm khiến người xem dừng lướt ở giây đầu và xem hết — như một người dựng chuyên nghiệp làm tay, nhưng xong trong vài phút. Cái làm nên "đỉnh cao" không phải hiệu ứng, mà là **biên tập**: chọn đúng câu, bỏ đúng chỗ thừa, mở bằng điều đắt nhất, mỗi vài giây có một thay đổi, chữ đúng chính tả, tiếng sạch và đều.

Công cụ (gói trong `scripts/`; máy mới chạy `cai_dat.sh` một lần — xem README.md):
- `phan_tich.py` — nghe + xem: Whisper large-v3-turbo gỡ băng, căn từng chữ theo sóng âm (MMS_FA), khoảng lặng, chuyển cảnh, bám mặt, độ sáng, lưới khung hình.
- `dung_video.py` — dựng từ `ke_hoach.json`: cắt, khung dọc, zoom, màu, B-roll, chữ (ASS), logo, nhạc, SFX, chuẩn âm lượng, ảnh bìa.
- `tim_broll.py` — tìm B-roll THẬT theo ý câu nói: ảnh/video trong dự án của người dùng, Wikimedia Commons, Openverse, Pexels → tải về + bảng xem + credit.
- `nhac_nen.py` — nhạc nền + SFX tự tổng hợp, không bản quyền (dùng khi không có nhạc thật).
- `cau_hinh.py` — đọc `~/.lbvid03/cau_hinh.json`: đường dẫn model, python, logo, giọng đọc, thư mục dự án/ảnh, nhạc mặc định. Không có đường dẫn riêng nào nằm trong code.

```
SK=~/.claude/skills/lb-vid03-edit-video/scripts
python3 $SK/cau_hinh.py          # kiểm tra máy đủ công cụ chưa (lần đầu trong phiên). Thiếu -> báo người dùng chạy cai_dat.sh
```

## Quy trình

### 0. Dựng thư mục dự án
`$(python3 $SK/cau_hinh.py thu_muc_du_an)/<YYYY-MM-DD>_<TenNgan>/` gồm `goc/` (chép/ln video gốc vào), `lam/` (phân tích + kế hoạch), `ra/` (thành phẩm). Không sửa file gốc của người dùng.

### 1. Phân tích
```
python3 $SK/phan_tich.py goc/<video> lam [--ngon-ngu auto]   # tự chuyển sang python có OpenCV+torch trong cấu hình; tiếng nước ngoài: auto
```
~15 giây cho clip 1 phút. Rồi **đọc `lam/phan_tich.md` và XEM `lam/luoi.jpg`** (và `lam/luoi_canh.jpg` nếu có nhiều cảnh). Không lên kế hoạch khi chưa nhìn thấy video trông thế nào.

### 2. Lên kế hoạch
Đọc `references/che_do.md` (phần đúng loại video — A nói trước máy, B video dài, C cảnh không lời, D video mạng, E thuyết minh không mặt người) và `references/phong_cach.md`. Lược đồ đầy đủ: `references/ke_hoach.md`. Viết `lam/ke_hoach.json`:
- chọn `phong_cach` theo nội dung (viral / chuyen_gia / dien_anh) — có lý do;
- `doan` theo thứ tự phát, câu đắt nhất lên đầu;
- `sua_chu` cho mọi lỗi Whisper thấy được (tên riêng, dấu thanh, số);
- `hook` 2 dòng, `tu_khoa`, `cta`;
- **key text động** (`chu_dong`, 3–5 cái) cho mọi con số / mốc / câu chốt, và **B-roll thật** (`chen`, 3–6 cái) cho mọi thứ nhìn thấy được trong lời nói — tìm bằng `tim_broll.py` rồi xem `bang.jpg` để chọn (phong_cach.md mục 5). Đây là phần làm video "đắt"; video chỉ có người nói + phụ đề là chưa đạt.

### 3. Trình kịch bản cắt — CHỜ DUYỆT
Người dùng muốn duyệt trước khi dựng (dựng sai tốn thời gian của họ hơn là đọc 1 bảng). Trình ngắn gọn:

```
Phong cách: chuyên gia — vì … 
Hook (3s đầu, cũng là ảnh bìa):  ĐẤT YÊN SỞ / TĂNG 30% / NĂM
Thời lượng dự kiến: ~42s (gốc 3 phút 10s)

| # | Giây gốc | Lời (đã sửa chính tả) | Ghi chú |
| 1 | 8.7–12.4 | Giá đất khu Yên Sở đã tăng khoảng 30%… | HOOK, kéo lên đầu |
| 2 | …        | …                                     | KEY "2027" đập · B-roll ảnh Metro thật (full) |
Bỏ: lời chào (1.5–5.0), đoạn vấp (40–44)…
Nhạc: nhẹ dưới giọng · Logo góc: có · Watermark trôi: không
```
Video dài → trình bảng xếp hạng các clip đề xuất (che_do.md mục B), người dùng chọn clip nào làm.
Người dùng sửa → cập nhật kế hoạch, trình lại phần thay đổi. Người dùng đã nói "tự làm luôn"/"không cần duyệt" → bỏ qua bước chờ.

### 4. Dựng
```
cd lam && python3 $SK/dung_video.py ke_hoach.json            # 1080x1920, ~30–60s cho 1 phút thành phẩm
python3 $SK/dung_video.py ke_hoach_*.json                    # nhiều short một lượt
python3 $SK/dung_video.py ke_hoach.json --nhap               # bản nháp 540p nhanh nếu cần soát bố cục
```
Lệnh dài (video dài, nhiều clip) → chạy nền.

### 5. Tự soát trước khi giao (bắt buộc)
- XEM `ra/<ten>_bia.jpg`: mặt/cảnh đẹp, hook đủ dấu, không đen, không che mặt. Xấu → đặt `bia.t_goc` hoặc đổi đoạn 1.
- XEM `ra/kiem_tra/<ten>_luoi.jpg`: khung bám đúng người, phụ đề không đè mặt/thẻ, B-roll đúng chỗ, không khung đen.
- Trích khung đúng lúc có key text / B-roll (`ffmpeg -ss <giây> -i ra/<ten>.mp4 -frames:v 1 …`) và XEM: chữ không che mắt, không chồng hook, ảnh không che mặt.
- Đọc `ra/<ten>.srt`: chính tả, tên riêng. Còn lỗi → thêm `sua_chu`, dựng lại.
- Thời lượng hợp lý (30–90s), không cụt chữ đầu/cuối đoạn (nới `t0`/`t1` 0,1s nếu cụt).
Sửa rồi dựng lại cho tới khi đạt — người dùng chỉ nên thấy bản đã đạt.

### 6. Giao
Gửi `ra/<ten>.mp4` (SendUserFile) + đường dẫn bản `_gui-nhanh.mp4` (720p, nhẹ, < 10MB để tải lên nhanh) và ảnh bìa. Kèm 1 caption ngắn có hook + 3–5 hashtag. Nói rõ những gì đã bỏ và vì sao, để người dùng bổ sung nếu muốn giữ.

## Mặc định (mỗi máy chỉnh trong `~/.lbvid03/cau_hinh.json`)
- Khung đầu = ảnh bìa đẹp nhất có hook, không bao giờ đen hay mờ từ đen (dung_video đã làm sẵn, chỉ cần chọn khung đẹp).
- Logo nhỏ góc phải: đóng khi cấu hình có `logo` (tắt riêng 1 video bằng `"logo": false`). Watermark chống copy: chỉ chạy `watermark_lenh` khi người dùng yêu cầu cho video đó.
- Nhạc: có lời → nhạc nhỏ dưới giọng (tự né giọng). Cấu hình có `nhac_mac_dinh` (nhạc thật CC, ví dụ nhạc epic) thì video có lời dùng bản đó ở 0,13 và tắt whoosh tự động — nghe chuyên nghiệp hơn nhạc tổng hợp; nhớ ghi credit tác giả trong caption. Không lời → tắt tiếng gốc, nhạc sôi động to.
- Chỉ dùng hình đẹp nhất; không dùng ảnh/cảnh lấp chỗ trống.
- Giọng lồng tiếng: `tts_lenh` trong cấu hình (giọng riêng của máy), không có thì edge-tts giọng Microsoft (`bac-nu` → HoaiMy, `bac-nam` → NamMinh). Giọng nhân bản của một người thật chỉ dùng khi chính người đó yêu cầu.
- Tên kênh (`ten_kenh`) dùng cho CTA và caption.

## B-roll video stock (tuỳ chọn)
Muốn có video stock chân thực (người, tiền, văn phòng, gia đình…) cho ý chung: cần khoá API Pexels miễn phí của người dùng (`export PEXELS_API_KEY=...` hoặc ghi vào ~/.zshrc). Không có khoá thì tim_broll vẫn chạy với ảnh dự án + Wikimedia + Openverse.

## Khi gặp sự cố
- Whisper gỡ thiếu/lặp câu: phan_tich đã chia cụm theo khoảng lặng để tránh; nếu vẫn thiếu, kiểm tra tiếng gốc (quá nhỏ/ồn) — tăng âm hoặc báo người dùng.
- Mặt bám sai (2 người, mặt trên poster): đặt `cx` cho đoạn đó.
- Phụ đề lệch: mốc chữ căn theo sóng âm với tiếng Việt; tiếng nước ngoài dùng mốc Whisper (kém hơn) — với video lồng tiếng thì phụ đề lấy theo lời Việt nên không bị ảnh hưởng.
- ffmpeg báo lỗi: thông báo in ra lệnh + 2500 ký tự lỗi cuối; thường do đường dẫn ảnh `chen` sai hoặc `t0 ≥ t1`.
