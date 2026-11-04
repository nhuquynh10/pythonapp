# Ứng dụng web đồ thị tri thức cây thuốc

Chuyển từ chương trình Tkinter sang FastAPI, giữ các chức năng đọc CSV, lọc Head/Tail, vẽ Neighbours, hiển thị ảnh và tìm đường đi k.

## Chạy trên máy tính

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Mở http://127.0.0.1:8000

## Render.com (Web Service / Python)

- Root Directory: để trống nếu đặt toàn bộ nội dung thư mục này tại gốc repository.
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Dữ liệu

- Thay file `Edges.csv` mẫu bằng dữ liệu thật, đúng tên 3 cột `Head,Predicate,Tail`.
- Để dùng **Show Image**, thêm `SachCayThuocGSDoTatLoi.jpg` vào cùng thư mục với `main.py`. Ảnh này không được cung cấp trong file Python gốc nên không có sẵn trong gói.
- Ứng dụng đọc dữ liệu ở chế độ chỉ đọc; không cho phép upload hoặc ghi file trên máy chủ.
- Đường đi k được giới hạn k <= 8 và tối đa 3000 kết quả để tránh quá tải server. Với đồ thị lớn, phép tìm đường đi có thể tốn tài nguyên.
