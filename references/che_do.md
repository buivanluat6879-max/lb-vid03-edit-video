# 5 loại video gốc — cách lên kế hoạch cho từng loại

`phan_tich.md` ghi "Máy đoán loại" (noi / dai / canh / thuyet_minh). Đó chỉ là gợi ý: tự xem luoi.jpg + lời thoại rồi quyết.

## A. `noi` — clip nói trước máy (điện thoại, webcam, phỏng vấn)

1. Đọc lời theo câu. Đánh dấu: câu đắt nhất (làm hook), câu bỏ (chào hỏi, vấp, lặp, lạc đề), câu giữ.
2. Sắp `doan`: câu đắt nhất lên đầu → bối cảnh → luận điểm 1, 2, 3 → chốt + câu hỏi/CTA. Mỗi đoạn = 1 câu hoặc 1 ý, ranh giới lấy theo mốc câu trong phan_tich.md, nới mỗi bên 0,05–0,1s để không cụt âm đầu/cuối.
3. Nói vấp giữa câu (lặp lại cụm, sửa lời): tách thành 2 đoạn, bỏ phần vấp. Đây là chỗ làm nên khác biệt giữa người dựng giỏi và máy cắt lặng.
4. Khung ngang: `reframe: mat`. Có 2 người: dùng `cx` cho từng đoạn để cắt về người đang nói. Có màn hình/bảng cần thấy rõ: đoạn đó `reframe: nen_mo` hoặc chèn ảnh chụp màn hình bằng `chen` kiểu `khung`.
5. Hình tối/mờ: `mau: auto` tự nâng sáng; báo người dùng nếu hình quá xấu.

## B. `dai` — video dài (livestream, podcast, hội thảo, video YouTube 10–60 phút) → nhiều short

1. Đọc toàn bộ phan_tich.md. Tìm 3–10 "khoảnh khắc" tự đứng được một mình, mỗi cái 30–75s. Chấm điểm 1–10 theo:
   - **Hook** (có câu mở đủ mạnh trong 3s đầu không?) ×3
   - **Trọn vẹn** (người chưa xem video gốc hiểu được không?) ×2
   - **Giá trị/cảm xúc** (con số, bí quyết, tranh cãi, câu chuyện) ×2
   - **Kết** (có câu chốt hoặc câu hỏi kéo bình luận) ×1
2. Trình bảng: thứ hạng, điểm, giây gốc, câu hook, tiêu đề đề xuất. Người dùng chọn → mỗi clip 1 file `ke_hoach_NN.json` (tên `NN-slug`), dựng một lượt: `dung_video.py ke_hoach_*.json`.
3. Một clip có thể ghép 2–3 đoạn xa nhau nếu cùng một ý (ví dụ câu hỏi của khán giả ở phút 12 + câu trả lời ở phút 14).
4. Không cắt giữa câu. Không để clip phụ thuộc "như tôi nói ở trên".
5. Video gốc rất dài (> 30 phút): phan_tich vẫn chạy được (Whisper ~ 1/10 thời gian thực); báo người dùng thời gian chờ.

## C. `canh` — cảnh quay không lời (dự án, flycam, nhà mẫu, công trường, sự kiện)

1. XEM `luoi_canh.jpg` (mỗi cảnh 1 ảnh có ghi giây) và `luoi.jpg`. Chọn 8–20 cảnh đẹp nhất: sắc nét, sáng, có chuyển động máy mượt, có điểm nhấn. Bỏ cảnh rung, mờ nét, cháy sáng, trùng lặp. Chỉ dùng cảnh đẹp nhất — không lấp chỗ trống.
2. Mỗi cảnh 1,5–3s (viral) hoặc 3–5s (điện ảnh). Lấy phần giữa cảnh (né 0,3s đầu/cuối hay bị rung). `khop_nhip` tự kéo độ dài mỗi đoạn về bội số phách nhạc.
3. Thứ tự kể chuyện: toàn cảnh gây choáng (hook) → tiếp cận → chi tiết đẹp → con người/tiện ích → toàn cảnh kết + CTA.
4. Cảnh ngang rộng (flycam): `reframe: giua` cắt dọc thường đẹp; cảnh mà cắt dọc mất chủ thể → `nen_mo`. Cảnh tĩnh → `day: true` để có chuyển động.
5. Không lời → tắt tiếng gốc (`tat_tieng_goc: true`) trừ khi tiếng gốc có giá trị (tiếng sóng, tiếng cười), nhạc `soi_dong` to 0,85, `phong_cach: viral` hoặc `dien_anh`. Chữ: hook + 2–4 thẻ thông tin (vị trí, giá, tiện ích) thay cho phụ đề.
6. Muốn có thuyết minh: viết lời Việt vào `am.long_tieng` (xem D) — video thành "cảnh + giọng đọc".

## D. `mang` — video tải từ mạng (TikTok, YouTube, Douyin, Facebook)

1. Lấy file: người dùng gửi file thì dùng luôn. Chỉ có link → cần `yt-dlp` (chưa cài trên máy; hỏi người dùng trước khi cài bằng `brew install yt-dlp`). Tải về thư mục riêng của dự án.
2. Bản quyền: video người khác chỉ dùng để **biến đổi đáng kể** (bình luận, phân tích, lồng tiếng Việt kèm góc nhìn riêng), ghi nguồn trong caption. Không đăng lại nguyên bản như của mình. Nếu người dùng muốn re-up nguyên xi, nói rõ rủi ro bị gỡ/khoá kênh.
3. Chạy phan_tich với `--ngon-ngu auto` (tiếng Trung/Anh…). Đọc bản gỡ băng, hiểu nội dung, rồi **viết lại lời Việt tự nhiên** (không dịch từng chữ), thêm góc nhìn cho người Việt. Số viết bằng chữ ở `doc`, hiển thị số ở `chu`.
4. `am.long_tieng` + `tat_tieng_goc: true` (hoặc `giu_tieng_goc: 0.1` nếu có tiếng không khí hay). Hình dài hơn lời → tự cắt bớt; lời dài hơn hình → tự kéo chậm hình (tối đa 1,6×) rồi lặp.
5. Video gốc có phụ đề cứng/logo của kênh khác: dùng `reframe` + `zoom` 1,1–1,2 để cắt bỏ, hoặc `nen_mo` rồi phủ phụ đề mới lên. Báo người dùng nếu không che hết được.
6. Video gốc đã là tiếng Việt → xử lý như A hoặc B.

## E. `thuyet_minh` — giọng đọc trên hình, không có mặt người (infographic, slide, quay màn hình, video bản đồ)

1. Trước hết tìm nguồn tốt hơn: nếu video gốc do chính người dùng làm (thư mục có dự án HyperFrames, `work/vo.wav`, `cues.json`, ảnh gốc…), dựng lại bản dọc từ nguồn gốc sẽ đẹp hơn hẳn letterbox. Đề xuất cách đó với người dùng trước.
2. Không có nguồn gốc → `reframe: nen_mo` (giữ trọn khung ngang trên nền mờ). Cắt dọc giữa chỉ khi nội dung nằm gọn ở giữa.
3. Phụ đề cứng của video gốc → `cat_khung` cắt bỏ dải dưới, rồi phụ đề mới của mình phủ lên.
4. Chọn đoạn như A/B (theo câu), nhưng không zoom giật (đã tự tắt ở `nen_mo`); thay đổi thị giác bằng thẻ số liệu và chính chuyển cảnh của video gốc.

## Video gốc đã có nhạc nền lót dưới giọng
- Đừng thêm nhạc thứ hai (`am.nhac: null`) — hai bài nhạc chồng nhau nghe rất rẻ. Trừ khi tắt tiếng gốc để lồng tiếng.
- Cắt đoạn có nhạc sẽ làm nhạc nhảy ở vết cắt — chấp nhận được với viral (whoosh che bớt); với chuyên gia ưu tiên đoạn dài liền.
- phan_tich tự nâng ngưỡng dò khoảng lặng khi có nhạc lót; nếu lời theo câu vẫn bị dính nhiều câu, chia đoạn theo mốc từng chữ trong phan_tich.json.
