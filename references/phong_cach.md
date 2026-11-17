# Chọn phong cách + biên tập như người dựng giỏi

## 1. Chọn phong cách theo nội dung (luôn nói lý do cho người dùng)

| Phong cách | Hợp với | Cảm giác | Mặc định kỹ thuật |
|---|---|---|---|
| `viral` | Tin nóng, con số sốc, mẹo, tranh luận, người nói năng lượng cao, giới trẻ | Nhanh, dồn dập, không thở | Cắt lặng >0,28s, zoom giật 1,14 ở mỗi vết cắt, phụ đề 3 chữ VIẾT HOA nảy từng chữ, từ khoá xanh lá, whoosh + thump, nhạc sôi động, màu tươi |
| `chuyen_gia` | Phân tích BĐS/tài chính, giải thích quy hoạch, chuyên gia nói điềm tĩnh, khách hàng trung niên | Tin cậy, rõ ràng, có nhịp thở | Cắt lặng >0,45s, zoom 1,08 xen kẽ theo đoạn, phụ đề 6 chữ thường, chữ đang đọc vàng, nhạc nhẹ dưới giọng, thẻ số liệu |
| `dien_anh` | Giới thiệu dự án cao cấp, flycam, nhà mẫu, câu chuyện cảm xúc, thương hiệu | Sang, chậm, nhiều không khí | Giữ khoảng lặng có chủ ý, đẩy máy chậm, phụ đề nhỏ, màu điện ảnh (teal-orange + vignette), nhạc pad ấm |

Dấu hiệu để quyết định: tốc độ nói (chữ/giây trong phan_tich), mức năng lượng giọng, chủ đề, đối tượng xem, chất lượng hình. Lẫn lộn → chọn `chuyen_gia` cho BĐS/tài chính/giáo dục, `viral` cho nội dung đại chúng.

## 2. Ba giây đầu quyết định tất cả

- **Mở bằng câu đắt nhất**, không mở bằng "Xin chào cả nhà". Tìm câu có con số / mâu thuẫn / lời hứa / câu hỏi gây tò mò, kéo nó lên làm đoạn 1 (đảo thứ tự `doan` là bình thường). Lời chào: cắt bỏ hoặc để sau hook.
- **Hook chữ** 2 dòng, ≤ 22 ký tự/dòng, viết hoa. Dòng 2 (nền vàng) mang con số hoặc chỗ gây tò mò. Không lặp y nguyên câu nói — bổ sung ý: nói "giá tăng ba mươi phần trăm", hook ghi "ĐẤT YÊN SỞ / TĂNG 30% / NĂM".
- **Khung đầu tiên là ảnh bìa**: phải có mặt/cảnh đẹp nhất + hook đủ chữ, tuyệt đối không đen, không mờ dần. Nếu khung đầu đoạn 1 xấu (nhắm mắt, mờ, đang quay đầu) → đặt `bia.t_goc` vào khung đẹp nhất (xem luoi.jpg).
- Các mẫu hook hiệu quả: "Sai lầm X người mắc…", "Con số khiến…", "Đừng mua … trước khi xem", "… tăng X% chỉ trong Y tháng", "Sự thật về …", câu hỏi trực diện.

## 3. Nhịp và cắt

- Một ý = một đoạn. Bỏ: lời chào dài, lặp ý, nói vấp, câu "như mình đã nói", đoạn kỹ thuật lạc đề. Giữ: con số, ví dụ cụ thể, câu kết luận, câu cảm xúc.
- Thời lượng đích: 30–60s (viral), 45–90s (chuyên gia). Dài hơn 90s chỉ khi nội dung thật sự giữ người xem.
- Mỗi 3–5 giây phải có một thay đổi thị giác: vết cắt + zoom, thẻ số liệu, B-roll, đổi cỡ. Đoạn > 6s không thay đổi gì → thêm `chen` hoặc `the`, hoặc chia đoạn.
- Kết: câu chốt mạnh hoặc câu hỏi kéo bình luận + CTA ngắn. Không kết bằng "cảm ơn đã xem" lê thê.

## 4. Phụ đề

- Luôn sửa lỗi Whisper bằng `sua_chu` — đọc kỹ phan_tich.md: tên riêng (Yên Sở, Vinhomes, Metro), dấu thanh (Gia/Giá, cài/cải), số. Phụ đề sai chính tả là lỗi nặng nhất về độ tin cậy.
- `tu_khoa`: 3–8 cụm quan trọng nhất (con số, tên dự án, mốc năm, động từ mạnh). Đừng tô quá nhiều — tô mọi thứ là không tô gì.

## 5. Key text động + B-roll thật — BẮT BUỘC, đây là thứ làm video "đắt"

Một video chỉ có người nói + phụ đề là video bình thường. Video đỉnh cao cứ 3–5 giây có một "sự kiện thị giác". Với mỗi video 30–60s, đặt tối thiểu:
- **3–5 key text (`chu_dong`)**: mọi con số đắt → `dem_so`; mốc thời gian, tên riêng, khẳng định mạnh → `dap`; lời cảnh báo, kết luận, câu chốt → `xep_chu`; lời khuyên ngắn → `go_chu`. `chu` ≤ 14 ký tự (viết hoa với viral), `phu` giải thích ≤ 26 ký tự. Không đặt 2 key text cách nhau < 2,5s, không đặt trong 1s đầu (để hook làm bìa).
- **3–6 B-roll thật (`chen`)**: mỗi khi lời nói nhắc tới thứ NHÌN THẤY ĐƯỢC (địa danh, dự án, công trình, đường, metro, công viên, sản phẩm, con người, hoạt động) → tìm và chèn hình thật của đúng thứ đó. Xen kẽ kiểu: `full` (choáng), `the_anh` / `chia_doi` (vẫn giữ mặt người nói). Tổng B-roll 25–45% thời lượng.
- Key text và B-roll có thể chồng lên nhau (chữ "2027" đập trên ảnh Metro) — rất mạnh.

### Tìm B-roll thật
```
python3 $SK/tim_broll.py "<tiếng Việt có dấu>|<tiếng Anh>" lam/broll/<ten-y> --n 8 [--video]
```
Rồi XEM `lam/broll/<ten-y>/bang.jpg` và chọn ảnh thật sự đẹp, đúng nội dung (đúng địa danh, không phải nơi khác cùng tên). Thứ tự ưu tiên: ảnh/video người dùng gửi hoặc có trong dự án của họ > Wikimedia/Openverse (ảnh thật, giấy phép mở — ghi tác giả vào caption khi đăng, xem `nguon.json`) > Pexels (cần khoá API, xem SKILL.md).
Ý trừu tượng (lãi suất, tâm lý, "thanh khoản chậm"): dùng ảnh khung cảnh liên quan (phố xá, toà nhà, người đi xem nhà) hoặc thay bằng key text — đừng chèn ảnh lạc đề.
Không có ảnh đủ đẹp → bỏ, dùng key text. Chất lượng hơn số lượng.

## 5b. Thẻ số liệu tĩnh (`the`)

- Thẻ (`the`) cho con số người xem cần nhớ: "+30%", "2027", "3,2 TỶ". `dong1` ngắn (≤ 10 ký tự), `dong2` giải thích ≤ 28 ký tự.
- B-roll (`chen`) khi người nói nhắc tới thứ nhìn thấy được: dự án, bản đồ, đường, công viên. `full` cho ảnh đẹp/flycam; `khung` cho bản đồ, bảng, ảnh chụp màn hình (để người nói vẫn lộ phía dưới). 2,5–4 giây mỗi lần, không quá 40% thời lượng.
- Nguồn ảnh: ảnh người dùng gửi > ảnh trong thư mục dự án > ảnh chính chủ dự án tìm trên mạng (kiểm tra trước khi dùng). Chỉ dùng ảnh đẹp nhất, không dùng ảnh lấp chỗ trống.

## 6. Âm thanh

- Có lời: nhạc nhỏ dưới giọng (0,12–0,2, tự né giọng). Không lời: tắt tiếng gốc nếu chỉ là ồn, nhạc to 0,85, nhạc sôi động.
- Giọng luôn được lọc ù, giảm ồn nhẹ, làm rõ (EQ 3 kHz), nén, rồi cả bài chuẩn -14 LUFS — không cần chỉnh tay.
