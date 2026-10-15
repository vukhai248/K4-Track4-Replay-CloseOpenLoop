# REPORT — Lab Day 12

> Điền **bằng lời và số liệu của chính bạn** (lấy từ màn hình và từ `evidence/*.json`). Mỗi câu 4–8 dòng là đủ. Số không có trong bằng chứng của bạn sẽ bị trừ điểm. Báo cáo công khai trên GitHub; giảng viên đối chiếu với `evidence/` và với bài của các bạn khác.

| | |
|---|---|
| Họ và tên | Vũ Gia Khải |
| MSSV (đúng bằng `--student-id` bạn đã chạy) | 2313473 |
| GitHub | vukhai248 |
| Seed chia dữ liệu / seed mô hình (xem `evidence/closedloop.json`, mục `student`) | 7111 / 2279, 2280, 2281 |
| Số seed huấn luyện bạn dùng (`--seeds`) | 3 |

## Kết quả cuối

Điền từ `evidence/closedloop.json`, `openloop.json`, `gate.json` (cho mỗi mô hình học, lấy **dải qua các seed**).

| Bộ điều khiển | L2 vòng hở (m) | Va chạm vòng kín trên log (%) | Quyết định cổng |
|---|---|---|---|
| constant-velocity | 1.248 | 19.6 (CI95 [18.2, 21.1], 1 seed) | BLOCK |
| IDM | 1.534 | 0.2 (CI95 [0.1, 0.5]) | (baseline) |
| EgoMLP | 0.757 | 17.4 – 26.1 (seed xấu nhất 26.1, CI95 [24.5, 27.8]) | BLOCK |
| PercMLP | 0.623 | 0.6 – 1.1 (seed xấu nhất 1.1, CI95 [0.8, 1.6]) | BLOCK |
| PercMLP+ (sau khi sửa) | 0.804 | 0.3 – 0.5 (seed xấu nhất 0.5, CI95 [0.3, 0.8]) | RELEASE |

## Câu 1 · Dữ liệu
Bước 0 bạn phát hiện những vấn đề gì ở dữ liệu? Vì sao không dùng cột `Acc_LV`, và bạn thay bằng gì? Bao nhiêu quỹ đạo bị loại vì trùng, và vì sao chia theo quỹ đạo?

Ba vấn đề trong `evidence/data_audit.json`. (1) `Acc_LV` vô dụng: hệ số tương quan với đạo hàm `Speed_LV` chỉ **0.045**, trong khi cột xe theo sau `Acc_FAV` tương quan **0.929** với đạo hàm `Speed_FAV` — tức cột gia tốc xe dẫn gần như nhiễu thuần, nên tôi bỏ nó và tự suy gia tốc xe dẫn từ `Speed_LV` đã làm mượt (trung bình trượt rộng 5 + sai phân tích trung tâm), dùng chính giá trị đó để khai thác ca phanh (p50 −2.5, p99 −4.2 m/s²). (2) **383 quỹ đạo trùng hệt** (9.993 → 9.610), chúng nằm rải rác ở các id xa nhau: nếu chia theo khung hình, cùng một cặp xe sẽ nằm ở cả train và test, mô hình chỉ cần "nhớ" là đạt điểm — test không còn là held-out. (3) `Spatial_Gap = Pos_LV − Pos_FAV − 4.5` đúng gần như tuyệt đối (lệch trung bình 4.499999999999993 m, sai lệch tuyệt đối tối đa 3.6e-11 m): 4.5 m chiều dài xe đã bị trừ sẵn, nên khoảng cách bumper-to-bumper phải trừ tiếp 4.5 m khi mô phỏng. Vì vậy tôi chia theo **quỹ đạo** (seed 7111: 6.727 train / 2.883 test, không giao nhau); các khung hình lân cận trong một quỹ đạo (7–11 s ở 10 Hz) gần như giống nhau nên chia theo khung hình sẽ rò rỉ.

## Câu 2 · Phát lại
Bản refactor float32 khác bit ở bao nhiêu đoạn, vượt dung sai ở bao nhiêu? Thay đổi AEB làm lệch bao nhiêu đoạn, và vì sao lệch ở đúng những khung đó (mở một đoạn ra xem)? Phát theo thời gian thật làm lộ ra điều gì mà phát nhanh nhất che đi?

So hai lần phát lại của 600 đoạn với dung sai `atol = 1e-3, rtol = 1e-3`: chạy lại cùng mã cho **0/600** đoạn lệch và **0** đoạn không giống từng bit. Bản "refactor float32" (cùng công thức, thứ tự phép tính khác) **không giống từng bit ở 600/600 đoạn** nhưng lệch tối đa chỉ **4.0e-04** và **0 đoạn vượt dung sai** — đây chính là lý do phải so với **cùng một dung sai**: so bằng nhau tuyệt đối sẽ báo 100% sai ở bản chỉ đổi thứ tự cộng float (demo `(0.1+0.2)+0.3 = 0.6000000000000001` khác `0.1+(0.2+0.3) = 0.6`), còn dung sai quá lỏng lại che mất thay đổi hành vi thật. Thêm AEB (phanh −6 m/s² khi TTC < 1.5 s) làm lệch **11/600 đoạn**; mở đoạn 113 ra, các khung lệch (34–38) là đúng các khung có TTC **1.48 → 1.42 s** (khoảng cách 4.46 → 3.45 m, tiến gần 3.01 → 2.44 m/s), nơi lệnh bị chặn xuống −6.0 thay vì −5.3 … −5.7 của IDM; trong cả đoạn chỉ có 12 khung TTC < 1.5 s nên AEB chỉ chạm đúng vùng nguy hiểm — một bản diff chỉ ra **một số ít** đoạn là dấu hiệu của thay đổi luật có thật, không phải nhiễu. Cuối cùng, phát "nhanh nhất" báo **0 late, 0 dropped** trên toàn bộ 59.732 khung (không có deadline nên khung rớt không tồn tại), còn phát theo thời gian thật (chi phí 6 ms, 1 % số lần là 140 ms > 100 ms) cho **582 late + 574 dropped**, làm **377/600 đoạn** đổi lệnh (giữ lệnh cũ khi khung bị rớt hay trễ hạn). Phát nhanh nhất che đi cả một lớp lỗi — lỗi hạn thời gian — chỉ vì nó không mô phỏng được chúng.

## Câu 3 · Kịch bản
Lưới của bạn (tốc độ cruise, giới hạn khoảng cách, số ô): bao nhiêu % ô **không ai tránh được**? Độ trễ phản ứng 0 → 0,6 s làm vùng đâm của IDM tăng bao nhiêu? Log có phủ vùng khó không? (dẫn giới hạn phanh mạnh nhất của người lái trong log, và phần lưới đòi hỏi hơn thế)

Lưới của tôi: cruise `v_ego = 14.0` m/s, khoảng cách **2.76 – 59.31 m** (p2…p98 của gap trong log), tốc độ tiến gần 0 – 14 m/s → **60 × 45 = 2.700 ô**. Biên bất khả thi (`gap < dv·t_react + dv²/(2·b_max)`, `b_max = 9`) chiếm **3.6 %** ô ở độ trễ 0 và **10.2 %** ở 0.6 s: độ trễ phản ứng làm vùng "ai cũng đâm" gấp gần 3 lần mà không bộ điều khiển nào sửa được — nên tổng diện tích đâm của một bộ điều khiển phải được trừ phần đó mới nói lên nó dở ra sao. Tôi kiểm chứng hàm `unavoidable` bằng chính bộ mô phỏng: xe phanh hết cỡ đụng **3.6 %** và **10.2 %** ô, **0 ô lệch** so với vật lý ở cả hai độ trễ; đường đỏ (đâm) của IDM nằm đúng trên đường cyan (bất khả thi), diện tích **attributable của IDM = 0.0 %** ở cả hai độ trễ, tức IDM gần như phanh hết cỡ. Log không phủ vùng khó: khai thác được **614/9.610 quỹ đạo (6.4 %)** có xe dẫn phanh, phanh mạnh nhất của người lái trong log (p99.9 của đạo hàm `Speed_FAV`) chỉ **3.6 m/s²** trong khi bộ truyền động làm được 9 m/s², và **12.7 %** ô của lưới đòi phanh mạnh hơn con số đó. Vậy một mô hình học từ log **không thể từng thấy** 12.7 % trạng thái trên lưới, dù điểm vòng hở của nó rất đẹp.

## Câu 4 · Vòng hở và vòng kín
Dán bảng L2 và tỷ lệ va chạm của bốn bộ điều khiển (kèm hạng ở mỗi cách chấm). Cặp nào đổi thứ tự? Vì sao IDM có L2 như vậy mà vẫn lái tốt? Vì sao EgoMLP có L2 tốt hơn constant-velocity mà vẫn đâm?

| Bộ điều khiển | L2 vòng hở (m) | hạng | va chạm vòng kín (trung bình seed) | hạng |
|---|---|---|---|---|
| const-vel | 1.248 | 3 | 19.6 % | 3 |
| IDM | 1.534 | 4 | 0.2 % | 1 |
| EgoMLP | 0.757 | 2 | 22.9 % | 4 |
| PercMLP | 0.623 | 1 | 0.8 % | 2 |

Các cặp đổi thứ hạng giữa hai cách chấm: `(const-vel, IDM)`, `(const-vel, EgoMLP)`, `(IDM, EgoMLP)`, `(IDM, PercMLP)` (`evidence/closedloop.json`, mục `ranking.order_flips`). IDM có **L2 tệ nhất (1.534 m)** nhưng **va chạm thấp nhất (0.2 %, CI95 [0.1, 0.5])**: điểm vòng hở chỉ hỏi "dự báo của bạn có giống quỹ đạo người lái không", mà người lái chỉ là **một** mẫu trong cả họ lái hợp lệ; luật IDM cuộn xe dẫn với giả định xe dẫn giữ tốc độ nên dự báo mở của nó lệch, nhưng khi tự lái, nó **tự sửa** qua phản hồi khoảng cách. Ngược lại EgoMLP có L2 **0.757 m** tốt hơn const-vel **1.248 m** nhưng đâm **22.9 %** so với 19.6 %: nó chỉ thấy lịch sử tốc độ của chính nó, **không thấy xe dẫn**, nên chỉ học "tôi thường làm gì" — đúng cho đến khi có xe cắt vào, lúc đó nó tiếp tục đi như thường. Đây là cơ chế: L2 đo độ gần một chuỗi hành vi, vòng kín đo khả năng tự sửa. Trung bình toàn cục còn che lỗi — lát cắt "xe dẫn sắp phanh trong 3 s" chỉ chiếm **4.4 %** cửa sổ test nhưng L2 trên đó tệ hơn trung bình ở mọi bộ (PercMLP **0.853 vs 0.623**, EgoMLP **1.054 vs 0.757**, const-vel **1.826 vs 1.248**). Ngoài ra với nhiễu quan sát (gap ±1 m, v xe dẫn ±0.5 m/s), PercMLP chỉ tăng 0.6 → 1.0 %.

## Câu 5 · Một lần chạy chưa đủ
EgoMLP dao động bao nhiêu giữa các seed? Khoảng tin cậy Wilson nói gì? Nếu bạn chỉ chạy đúng một seed thì có thể báo kết quả nào, và vì sao điều đó nguy hiểm?

Với 3 seed huấn luyện (2279/2280/2281), EgoMLP cho **17.4 %, 25.1 %, 26.1 %** — chênh **8.7 điểm phần trăm** trên cùng một bộ dữ liệu, cùng một mã; seed xấu nhất 26.1 % có CI95 Wilson **[24.5, 27.8]**, seed tốt nhất 17.4 % có **[16.1, 18.8]**, hai khoảng **không chồng nhau chút nào**. Nếu chỉ chạy một seed, tôi hoàn toàn có thể báo "EgoMLP đâm 17.4 %" (một con số nghe không tệ) hoặc "26.1 %" (tệ) — cả hai đúng về mặt kỹ thuật, và cùng một kết luận phát hành sẽ thay đổi theo seed nào tình cờ được chọn. Chính vì thế cổng R5 giới hạn biên độ qua seed ≤ 1 điểm: EgoMLP rớt R5 (17.4 – 26.1), còn PercMLP (0.6 – 1.1 %) và PercMLP+ (0.3 – 0.5 %) qua. Đối chiếu thêm với ngưỡng: kể cả khi dải hẹp, CI95 của n = 2.883 vẫn rộng ±0.6 – 0.7 điểm (PercMLP seed xấu nhất **[0.8, 1.6]**), nên gate chọn **cận trên 95 % của seed xấu nhất** chứ không lấy điểm số đẹp nhất.

## Câu 6 · Tác nhân phản ứng
Dán bảng "xe sau phát lại" và "xe sau phản ứng". `T` bạn hiệu chỉnh là bao nhiêu, xe sau chân thực đến mấy so với xe không phản ứng? Vì sao IDM bị tính "va chạm giả" khi xe sau chỉ phát lại, và điều này làm đổi kết luận về bộ điều khiển ra sao?

| Bộ điều khiển (`t_react = 0.6 s`) | xe sau phát lại: va chạm phía sau / tổng | xe sau phản ứng: va chạm phía sau / tổng |
|---|---|---|
| const-vel | 0.0 % / 80.6 % | 0.0 % / 80.6 % |
| IDM | 70.6 % / 80.9 % | 0.0 % / 10.2 % |
| EgoMLP | 0.0 % / 82.3 % | 0.0 % / 82.3 % |
| PercMLP | 51.1 % / 78.6 % | 0.0 % / 27.7 % |
| PercMLP+ | 70.1 % / 80.8 % | 0.0 % / 10.7 % |

`T` hiệu chỉnh = **1.4 s** (khoảng cách Wasserstein-1 nhỏ nhất, 0.34, trong bảng T = 0.6…2.4; người lái trong log giữ headway trung vị **1.86 s**), trong khi một xe sau không bao giờ phản ứng chỉ đạt W1 = **0.89**, tệ hơn ~2,6 lần. Với xe sau **phát lại** (không biết xe phía trước vừa phanh), IDM bị tính **70.6 %** va chạm phía sau và tổng **80.9 %** — gần như toàn bộ lưới; sang xe sau **phản ứng**, cả hai chỉ còn **0.0 %** va chạm phía sau và IDM chỉ còn **10.2 %** (một mình phần mặt trước bất khả thi). Đây là "va chạm giả": xe sau log đang giữ tốc độ cũ trong khi ego đã phanh đúng, nên nó tông vào đuôi một bộ điều khiển **đang lái đúng** — IDM có diện tích attributable phía trước **0.0 %** mà vẫn bị coi là thảm họa. Hậu quả là đảo kết luận: trong thế giới phát lại IDM (80.9 %) tệ hơn cả EgoMLP (82.3 %), còn trong thế giới phản ứng IDM (10.2 %) lại gần bằng PercMLP+ (10.7 %) và tốt hơn nhiều so với PercMLP (27.7 %). Vì thế cổng dùng luôn quy tắc R6 với xe phía sau phản ứng — và lưu ý artefact này chỉ trừng phạt đúng những bộ **biết phanh**: const-vel và EgoMLP không bao giờ bị tông từ sau.

## Câu 7 · Cổng phát hành và sửa
Quy tắc nào chặn PercMLP và nguyên nhân gốc là gì (dẫn số)? Bạn sửa bằng gì và vì sao nó chữa đúng nguyên nhân? Sau khi qua cổng, PercMLP+ có **tốt hơn** IDM không? Nó có nên được phát hành không, và bạn đề xuất làm gì trước khi quyết định?

PercMLP bị chặn bởi 4 quy tắc: **R2** (cận trên 95 % **1.6 %** > 0.2 % + 1 điểm), **R3** (lát cắt phanh **3.2 %**, cận trên **6.9 %** > 1.6 % + 5 điểm), **R4** (**17.5 %** ô tránh được mà vẫn đâm, so với 0.0 % + 2 điểm) và **R6** (**27.7 %** lưới vs 10.2 %). Bốn quy tắc này đến từ hai nguyên nhân gốc khác nhau. (a) **Kịch bản log không chứa**: R4/R6 — cắt vào ở 0.6 s cần phanh mạnh hơn mức log từng thấy (12.7 % ô), và ở tốc độ cruise ngoài phạm vi 20 m/s mà huấn luyện chưa từng thấy, PercMLP đâm **23.1 – 28.3 %** ô tránh được; đây là lỗi ở trạng thái **chưa từng xuất hiện**. (b) **Sai số tích lũy**: R2/R3 — trên chính log held-out nó chỉ đâm 1.1 % (seed xấu nhất) nhưng baseline IDM là 0.2 %, và trên lát cắt xe dẫn phanh là 3.2 %; sai lệch nhỏ lúc bắt chước tự cộng dồn khi mô hình tự lái. Cách sửa: thêm **197.090 cửa sổ** từ 20.000 ca cắt vào mô phỏng (nhãn do luật IDM làm) rồi **2 vòng DAgger** — cho mô hình tự lái trên log train, ghi trạng thái **chính nó đi vào**, gán nhãn bằng dự báo 3 s của IDM ở đó (tổng 895.086 cửa sổ). Đúng hai nguyên nhân: cửa sổ kịch bản che lỗ (a), DAgger che lỗ (b). Kết quả: R2 **0.5 %** (cận trên 0.8 % ≤ 1.2 %), R3 **2.2 %** (cận trên 5.4 % ≤ 6.6 %), R4 **0.5 % ≤ 2 %**, R6 **10.7 % ≤ 12.2 %**, R5 **0.3 – 0.5 %** → **RELEASE**; ở tốc độ ngoài phạm vi 20 m/s nó còn **0.1 – 1.7 %**. Nhưng bằng chứng chỉ cho thấy nó **không kém hơn** IDM, không phải tốt hơn: trên log **0.3 – 0.5 %** so với 0.2 %, trên lưới **0.5 %** so với **0.0 %** attributable, ở 20 m/s **0.1 – 1.7 %** so với **0.0 %** — và nó học từ chính IDM (mọi nhãn đều là dự báo của IDM) nên tối đa chỉ bắt kịp thầy. Vì vậy **không nên thay IDM ngay**: giữ IDM làm baseline, coi PercMLP+ là phương án "không kém hơn" cần kiểm thêm (dải 0.1 – 1.7 % ở tốc độ ngoài phạm vi, kịch bản bên hông, cảm biến có che khuất, chỉ số thoải mái/jerk), và nhớ L2 vòng hở của nó **tệ đi** (0.804 vs 0.623) — dấu hiệu rõ ràng rằng điểm vòng hở không phải câu hỏi của bài.

## Câu 8 · Bài lab này không chứng minh được gì
Chọn **ít nhất ba** giới hạn quan trọng nhất đối với việc quyết định phát hành và giải thích vì sao mỗi cái làm kết luận của bạn kém chắc chắn. Điều gì cần làm tiếp để thu hẹp khoảng cách đến thế giới thật?

Ba giới hạn tôi cho là quyết định nhất. (1) **Thế giới không phản ứng**: xe dẫn chỉ phát lại log, chỉ có xe sau được phản ứng, nên mọi kết luận về "cắt vào" là tương tác một chiều — trong thực tế xe bị cắt vào cũng phanh/tránh, và chính artefact này làm IDM (80.9 %) tệ hơn EgoMLP (82.3 %) trong khi ở thế giới phản ứng nó lại tốt hơn. (2) **Mô hình thế giới là giả định**: một chiều dọc, chỉ có khoảng cách và tốc độ xe dẫn (nhiễu tối đa 1 m / 0.5 m/s), không có chuyển động ngang, không xe khác, không che khuất, không luật giao thông, không hành khách; bộ điều khiển "không kém hơn IDM" ở đây chẳng nói lên gì trên phố thật. (3) **Họ kịch bản do ta tự chọn và cặp da (gap × dv) trên một tốc độ cruise**: PercMLP+ được sửa trên cắt vào ≤ 16 m/s, nhưng ở **20 m/s** nó vẫn đâm tới **1.7 %** ô tránh được trong khi IDM là **0.0 %** — phần tổng quát hóa vượt khỏi họ đã chọn vẫn là điểm yếu, và các gia đình kịch bản khác (phanh đột ngột, cắt ngang, dừng khẩn cấp) chưa hề được thử. (4) **Thống kê còn nghèo**: 2.883 quỹ đạo cho CI95 rộng ±0.6 điểm, không có ước lượng cho biến cố hiếm, không có chỉ số nào khác ngoài va chạm/gap (không jerk/thoải mái, không tuân luật, không near-miss); và bài lab chọn tiêu chí thành công là "không kém hơn IDM", một mức mà một bản sao thầy chỉ có thể **bằng** chứ không hơn. Để thu hẹp khoảng cách: tác nhân phản ứng hai chiều, mô phỏng 2D có xe lân cận và luật giao thông, quan sát bị che khuất/lỗi, đa nền tảng dữ liệu, khoảng tin cậy cho biến cố hiếm, thêm chỉ số thoải mái/tuân luật, rồi triển khai theo giai đoạn với con người được can thiệp.
