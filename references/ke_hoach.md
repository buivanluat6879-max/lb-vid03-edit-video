# ke_hoach.json — lược đồ đầy đủ

Đường dẫn tương đối tính từ thư mục chứa ke_hoach.json (thường là `lam/`, nên gốc là `../goc/…`, thành phẩm `../ra`). Chỉ `nguon`, `doan` là bắt buộc; mọi thứ khác có mặc định theo `phong_cach`.

```json
{
  "nguon": "../goc/clip.mp4",          // video gốc
  "phan_tich": "phan_tich.json",       // do phan_tich.py ghi
  "ra": "../ra",                       // thư mục thành phẩm (cạnh goc/ và lam/)
  "ten": "dat-yen-so-tang-30",         // tên file, không dấu, gạch nối
  "phong_cach": "viral",               // viral | chuyen_gia | dien_anh  (xem phong_cach.md)

  "khung": {"reframe": "mat"},
  "cat_khung": [0, 0, 1920, 924],      // tuỳ chọn: cắt video gốc trước (x, y, rộng, cao — pixel gốc) để bỏ phụ đề cứng/logo kênh khác/viền đen         // mat = bám mặt · giua = cắt giữa · nen_mo = giữ nguyên khung ngang trên nền mờ
  "doan": [                            // giây GỐC, theo thứ tự PHÁT (được đảo thứ tự, ví dụ kéo câu đắt nhất lên đầu làm hook)
    {"t0": 8.70, "t1": 12.35},
    {"t0": 1.45, "t1": 5.05, "zoom": 1.0},          // zoom: ép cỡ (1.0 = rộng, 1.15 = cận). Bỏ trống = tự xen kẽ theo phong cách
    {"t0": 40.0, "t1": 46.0, "toc_do": 1.1},        // nói chậm quá -> tăng 1.05–1.15 (giữ cao độ)
    {"t0": 60.0, "t1": 66.0, "day": true},          // đẩy máy chậm (Ken Burns) — hợp cảnh không lời
    {"t0": 70.0, "t1": 75.0, "reframe": "nen_mo"},  // riêng đoạn này giữ khung ngang (bảng, màn hình, cảnh rộng)
    {"t0": 80.0, "t1": 84.0, "cx": 0.3},            // ép tâm cắt ngang (0..1) khi có 2 người / mặt bị nhận sai
    {"t0": 90.0, "t1": 95.0, "giu_lang": true}      // không cắt khoảng lặng trong đoạn này (khoảnh khắc cảm xúc)
  ],
  "cat_lang": 0.3,                     // cắt mọi khoảng lặng dài hơn x giây bên trong đoạn (null = không cắt)
  "bo_tu": ["ờ", "ừm", "à"],           // từ đệm cắt khỏi tiếng và phụ đề
  "sua_chu": {"Gia đất": "Giá đất", "yên sở": "Yên Sở"},   // sửa lỗi Whisper cho phụ đề (khớp cụm chữ liền nhau)

  "hook": {                            // hiện ngay khung đầu tiên = ảnh bìa; không mờ từ đen
    "kicker": "BĐS PHÍA NAM HÀ NỘI",   // dòng nhỏ vàng phía trên (tuỳ chọn)
    "dong1": "ĐẤT YÊN SỞ",             // chữ trắng nền đen
    "dong2": "TĂNG 30% / NĂM",         // chữ đen nền vàng — chỗ đặt con số/điểm gây tò mò
    "dur": 3.0, "y": 0.17              // y = vị trí theo chiều cao khung
  },
  "bia": {"t_goc": 12.4},              // tuỳ chọn: lấy khung đẹp nhất ở giây gốc này làm 3 khung đầu (ảnh bìa)

  "phu_de": {
    "bat": true,
    "tu_khoa": ["30%", "Metro số 3", "2027"],  // tô màu riêng suốt câu
    "so_chu": 3,                       // số chữ mỗi khung (viral 2–4, chuyên gia 5–7)
    "viet_hoa": true, "co": 84,        // cỡ chữ ở 1080p
    "cach_day": 0.25                   // khoảng cách mép dưới (0.25 = né thanh tương tác TikTok/Reels)
  },
  "the": [                             // thẻ số liệu bật ra (ding)
    {"khi_noi": "Metro số 3", "dong1": "METRO 3", "dong2": "khởi công 2027", "dur": 2.4, "y": 0.2}
  ],
  "chu_dong": [                        // KEY TEXT động (kinetic) — chữ to giữa màn hình, nền tối lại
    {"khi_noi": "30%", "kieu": "dem_so", "chu": "+30%", "phu": "chỉ trong 12 tháng", "dur": 1.9},   // số chạy 0 -> 30%, ding
    {"khi_noi": "năm 2027", "kieu": "dap", "chu": "2027", "phu": "Metro 3 khởi công", "dur": 1.6}, // đập vào + rung, thump
    {"khi_noi": "phải cẩn thận", "kieu": "xep_chu", "chu": "PHẢI CẨN THẬN", "dur": 1.8},         // từng chữ bay vào đúng lúc nói
    {"t": 30.0, "kieu": "go_chu", "chu": "Mua để ở thì OK", "dur": 2.0}                          // đánh máy
  ],                                   // tuỳ chọn mỗi mục: "y" (0.40), "co" (170), "mau" (&H0000E1FF&), "toi_nen" (true), "som" (0.05s đi trước lời)
  "chen": [                            // B-roll THẬT (tìm bằng tim_broll.py): ảnh/video phủ lên trong khi tiếng vẫn chạy
    {"khi_noi": "tuyến Metro số 3", "file": "broll/metro/03_commons.jpg", "dur": 2.4, "kieu": "full"},
    {"khi_noi": "công viên Yên Sở", "file": "broll/cong-vien/01_may.jpg", "dur": 2.6, "kieu": "the_anh"},
    {"khi_noi": "thanh khoản", "file": "broll/pho/04.jpg", "dur": 2.2, "kieu": "chia_doi"},
    {"t_goc": 50.0, "file": "flycam.mp4", "tu": 4.0, "dur": 3.0, "kieu": "full", "chuyen_dong": "ra"}
  ],
  // kieu: full = phủ kín, đẩy máy (chuyen_dong: vao | ra | trai | phai, mặc định xoay vòng) — cảnh đẹp, flycam, video
  //       the_anh = thẻ ảnh viền trắng bật lên nghiêng có bóng, đặt trên đầu người nói; không đủ chỗ thì TỰ chuyển chia_doi
  //       chia_doi = B-roll nửa trên, mặt người nói nửa dưới, phụ đề lên đường phân cách — giữ mặt mà vẫn thấy minh hoạ
  //       khung = ảnh khung nhỏ phía trên (bản đồ, bảng, ảnh chụp màn hình)
  // phong cách viral: tự chớp sáng 1 nhịp khi vào B-roll
  "sfx": [{"ten": "pop", "t": 5.2, "vol": 0.3}],   // tự đặt thêm: whoosh | pop | ding | rise | thump

  "am": {
    "nhac": "auto",                    // auto = tự tổng hợp không bản quyền · đường dẫn mp3/wav · null = không nhạc
    "kieu_nhac": "dien_anh",           // soi_dong | dien_anh | nhe | vui (mặc định theo phong cách)
    "nhac_vol": 0.16,                  // có giọng 0.12–0.2 (tự né giọng) · không giọng 0.8–0.9
    "sfx": true,                       // whoosh ở chỗ chuyển đoạn, thump ở hook (mặc định bật ở viral)
    "tat_tieng_goc": false,            // true khi tiếng gốc vô dụng (gió, ồn, tiếng nước ngoài)
    "long_tieng": {                    // lồng tiếng Việt thay tiếng gốc (video nước ngoài / cảnh không lời có thuyết minh)
      "giong": "bac-nam",              // bac-nam | bac-nam2 | bac-nu | bac-nu2 | nu | nam (tools/tts.sh)
      "toc_do": 1.05,
      "cau": ["Câu đọc thường.", {"doc": "giá tăng ba mươi phần trăm", "chu": "giá tăng 30%"}]
    },
    "giu_tieng_goc": 0.12              // khi lồng tiếng: giữ tiếng gốc nhỏ làm không khí (0 = tắt)
  },
  "mau": "auto",                       // auto | tu_nhien | sang | am | dien_anh | none
  "logo": true,                        // logo nhỏ góc phải trên (ảnh lấy từ khoá logo trong ~/.lbvid03/cau_hinh.json)
  "cta": "THEO DÕI ĐỂ XEM PHẦN 2",     // 2,4 giây cuối; hoặc {"text": "...", "y": 0.1, "dur": 3} — tự né thẻ số liệu đang hiện
  "khop_nhip": true                    // cắt khớp phách nhạc (mặc định bật cho cảnh không lời)
}
```

## Cách neo thời điểm cho `the`, `chen`, `chu_dong`

- `"khi_noi": "cụm chữ"` — tốt nhất: tự tìm lúc cụm đó được nói trong thành phẩm (sau khi đã cắt/đảo). Viết đúng như phụ đề sau khi đã `sua_chu`.
- `"t_goc": 50.0` — giây trong video gốc (phải nằm trong một đoạn được giữ).
- `"t": 12.0` — giây trong thành phẩm (chỉ khi đã biết, ví dụ dựng lại lần 2 sau khi xem `dong_thoi_gian.json`).

## Ghi chú kỹ thuật

- `sua_chu` áp cho toàn bộ lời: dùng cụm 2–3 chữ làm mốc để khỏi sửa nhầm chỗ khác ("rẻ" sẽ dính cả "rẻ nhất"). Chữ mới có dấu câu cuối thì thay dấu cũ ("đâu?" → "đâu."). Thêm dấu chấm/viết hoa đầu câu cũng làm bằng `sua_chu`.
- `nen_mo`: zoom tự động bị tắt (sẽ xén mất nội dung hai bên); hook mặc định đặt cao hơn (y 0.10) để không đè khung hình giữa.

- Thời lượng thành phẩm ≈ tổng các đoạn trừ khoảng lặng/từ đệm bị cắt. Tổng gốc 1,2–1,4 lần thời lượng mong muốn là vừa.
- Muốn 1 video dài thành nhiều short: viết nhiều file `ke_hoach_01.json`, `ke_hoach_02.json`… rồi `dung_video.py ke_hoach_*.json`.
- `ra/tam/<ten>/dong_thoi_gian.json` ghi mốc từng mảnh, từng chữ của thành phẩm: dùng để chỉnh `t` chính xác khi sửa.
