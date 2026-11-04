import csv
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk  # Cần cài đặt thư viện Pillow: pip install Pillow
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx

# --- Tạo thư mục Data và file edges.csv tự động nếu chưa có ---
# os.makedirs("Data", exist_ok=True)
default_kg_path = "Edges.csv"

if not os.path.exists(default_kg_path):
  with open(default_kg_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Head", "Predicate", "Tail"])
    writer.writerow(["Nhục quế", "Trị", "Tỳ vị hư hàn"])
    writer.writerow(["Nhục quế", "Chữa_Triệu_Chứng", "Đau bụng"])
    writer.writerow(["Phụ tử", "Trị", "Hàn thấp bại liệt"])
    writer.writerow(["Phụ tử", "Chữa_Triệu_Chứng", "Ho hen"])

# Biến toàn cục lưu đường dẫn tệp KG hiện tại
current_kg_file = default_kg_path

# Khởi tạo cửa sổ chính
root = tk.Tk()
root.title(
    "Đồ thị tri thức về Cây thuốc được tạo từ cuốn sách 'Những cây thuốc và vị thuốc Việt Nam' của GS.TS. Đỗ Tất Lợi"
)
root.geometry("1100x750")

# --- Tùy chỉnh Style cho Treeview (Header: nền cyan, chữ blue) ---
style = ttk.Style()
style.theme_use("clam")  # Dùng theme clam để dễ tùy biến màu sắc header
style.configure(
    "Treeview.Heading",
    background="cyan",
    foreground="blue",
    font=("Arial", 9, "bold"),
)

# Tiêu đề màn hình chính màu đỏ
title_label = tk.Label(
    root,
    text=(
        "Đồ thị tri thức được tạo từ cuốn sách 'Những cây thuốc và vị thuốc Việt Nam' của GS.TS. Đỗ Tất Lợi\n Được phát triển bởi Prof Happy AI Research Group, 2026"
    ),
    font=("Arial", 16, "bold"),
    fg="red",
)
title_label.pack(pady=5)


# --- Đưa các nút điều khiển ra ngoài góc trái phía trên (Đã lược bỏ nút Choose KG Folder) ---
top_control_frame = tk.Frame(root)
top_control_frame.pack(fill=tk.X, padx=10, pady=5)

# Biến toàn cục lưu trữ tham chiếu ảnh để tránh bị Garbage Collection của Python xóa mất
image_label_widget = None
img_tk = None


# Khai báo các hàm chức năng trước khi tạo nút
def clear_all():
  global canvas_widget, image_label_widget, img_tk
  if canvas_widget:
    canvas_widget.get_tk_widget().destroy()
    canvas_widget = None

  if image_label_widget:
    image_label_widget.destroy()
    image_label_widget = None
    img_tk = None

  # Xóa nội dung trong cửa sổ 4 (Text widget)
  text_output.config(state=tk.NORMAL)
  text_output.delete("1.0", tk.END)
  text_output.config(state=tk.DISABLED)

  source_entry.delete(0, tk.END)
  k_entry.delete(0, tk.END)
  k_entry.insert(0, "2")


def load_data_to_tree(file_path):
  global current_kg_file
  current_kg_file = file_path

  # Xóa dữ liệu cũ trên treeview
  for item in tree.get_children():
    tree.delete(item)

  heads_set = set()
  tails_set = set()

  try:
    with open(file_path, mode="r", encoding="utf-8") as f:
      reader = csv.DictReader(f)
      for row in reader:
        tree.insert("", tk.END, values=(row["Head"], row["Predicate"], row["Tail"]))
        heads_set.add(row["Head"])
        tails_set.add(row["Tail"])

    head_combobox["values"] = ["All"] + sorted(list(heads_set))
    tail_combobox["values"] = ["All"] + sorted(list(tails_set))

    head_combobox.set("All")
    tail_combobox.set("All")

    # Hiển thị tên file phía trên Cửa sổ 1
    file_name = os.path.basename(file_path)
    file_name_label.config(text=f"Tệp KG hiện tại: {file_name}")
  except Exception as e:
    messagebox.showerror("Lỗi", f"Không đọc được file:\n{e}")


def draw_neighbours():
  global canvas_widget, image_label_widget
  # Xóa hiển thị ảnh ở cửa sổ 3 nếu đang có
  if image_label_widget:
    image_label_widget.destroy()
    image_label_widget = None

  source_val = source_entry.get().strip()
  if not source_val:
    messagebox.showerror("Lỗi", "Vui lòng chọn hoặc nhập giá trị Source!")
    return

  G = nx.Graph()
  edge_predicates = {}  # Lưu trữ Predicate giữa các cặp node
  try:
    with open(current_kg_file, mode="r", encoding="utf-8") as f:
      reader = csv.DictReader(f)
      for row in reader:
        h, t, p = row["Head"], row["Tail"], row["Predicate"]
        G.add_edge(h, t)
        edge_predicates[(h, t)] = p
        edge_predicates[(t, h)] = p  # Đồ thị vô hướng lưu cả 2 chiều
  except Exception as e:
    messagebox.showerror("Lỗi", f"Không đọc được file KG: {e}")
    return

  if source_val not in G:
    messagebox.showwarning(
        "Cảnh báo", f"Node '{source_val}' không tồn tại trong đồ thị!"
    )
    return

  neighbors = list(G.neighbors(source_val))

  # Hiển thị thông tin hàng xóm kèm Predicate ở cửa sổ 4
  text_output.config(state=tk.NORMAL)
  text_output.delete("1.0", tk.END)
  text_output.insert(
      tk.END, f"--- Các hàng xóm trực tiếp của '{source_val}' ---\n"
  )
  for n in neighbors:
    pred = edge_predicates.get((source_val, n), "")
    text_output.insert(tk.END, f"- {source_val} --[{pred}]--> {n}\n")
  text_output.config(state=tk.DISABLED)

  if canvas_widget:
    canvas_widget.get_tk_widget().destroy()

  sub_nodes = [source_val] + neighbors
  subG = G.subgraph(sub_nodes)

  fig, ax = plt.subplots(figsize=(5, 3))
  pos = nx.spring_layout(subG)
  node_colors = [
      "orange" if node == source_val else "lightblue" for node in subG.nodes()
  ]

  nx.draw(
      subG,
      pos,
      ax=ax,
      with_labels=True,
      node_color=node_colors,
      node_size=700,
      font_size=8,
  )
  edge_labels = {
      (u, v): edge_predicates.get((u, v), "") for u, v in subG.edges()
  }
  nx.draw_networkx_edge_labels(subG, pos, edge_labels=edge_labels, font_size=6)
  fig.tight_layout()

  canvas = FigureCanvasTkAgg(fig, master=win3_frame)
  canvas.draw()
  canvas_widget = canvas
  canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


# Hàm hiển thị ảnh SachCayThuocGSDoTatLoi.jpg lên cửa sổ 3
def show_image():
  global canvas_widget, image_label_widget, img_tk

  # Đường dẫn file ảnh mặc định yêu cầu
  default_image_path = "SachCayThuocGSDoTatLoi.jpg"

  # Kiểm tra xem file có tồn tại không, nếu không cho phép chọn file khác
  if os.path.exists(default_image_path):
    file_path = default_image_path
  else:
    # Nếu không tìm thấy file mặc định, bật hộp thoại để người dùng chọn
    file_path = filedialog.askopenfilename(
        title="Chọn file ảnh dược liệu",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png"), ("All Files", "*.*")],
    )

  if not file_path:
    return  # Người dùng bấm hủy

  try:
    # Xóa đồ thị matplotlib cũ nếu đang hiển thị ở cửa sổ 3
    if canvas_widget:
      canvas_widget.get_tk_widget().destroy()
      canvas_widget = None

    # Xóa ảnh cũ nếu có
    if image_label_widget:
      image_label_widget.destroy()
      image_label_widget = None

    # Đọc kích thước hiện tại của Cửa sổ 3 để làm giới hạn tối đa
    win3_frame.update_idletasks()
    max_w = win3_frame.winfo_width() - 20
    max_h = win3_frame.winfo_height() - 40
    if max_w < 100:
      max_w = 450
    if max_h < 100:
      max_h = 300

    # Mở ảnh gốc bằng Pillow
    img = Image.open(file_path)
    orig_w, orig_h = img.size

    # Tính toán tỷ lệ co giãn để giữ nguyên aspect ratio (không bị méo ảnh)
    ratio = min(max_w / orig_w, max_h / orig_h)
    new_w = int(orig_w * ratio)
    new_h = int(orig_h * ratio)

    # Co giãn ảnh theo kích thước mới đã tính
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    img_tk = ImageTk.PhotoImage(img_resized)

    # Tạo Label chứa hình ảnh và đặt vào cửa sổ 3
    image_label_widget = tk.Label(win3_frame, image=img_tk, bg="#E6F2FF")
    image_label_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    messagebox.showinfo("Thành công", f"Đã hiển thị ảnh: {file_path}")

  except Exception as e:
    messagebox.showerror("Lỗi", f"Không thể mở file ảnh:\n{e}")


# Hàm tìm tất cả đường đi có độ dài k kèm theo Predicate
def find_k_path():
  k_val_str = k_entry.get().strip()
  if not k_val_str.isdigit():
    messagebox.showerror("Lỗi", "Giá trị k phải là một số nguyên hợp lệ!")
    return
  k = int(k_val_str)

  G = nx.Graph()
  edge_predicates = {}
  try:
    with open(current_kg_file, mode="r", encoding="utf-8") as f:
      reader = csv.DictReader(f)
      for row in reader:
        h, t, p = row["Head"], row["Tail"], row["Predicate"]
        G.add_edge(h, t)
        edge_predicates[(h, t)] = p
        edge_predicates[(t, h)] = p
  except Exception as e:
    messagebox.showerror("Lỗi", f"Không đọc được file KG: {e}")
    return

  if len(G.nodes) == 0:
    messagebox.showwarning("Cảnh báo", "Đồ thị trống!")
    return

  # Tìm tất cả các đường đi đơn có độ dài k trong toàn bộ đồ thị
  all_paths = set()
  for node in G.nodes():
    queue = [[node]]
    while queue:
      path = queue.pop(0)
      if len(path) == k + 1:
        p_tuple = tuple(path)
        p_rev_tuple = tuple(reversed(path))
        if p_tuple not in all_paths and p_rev_tuple not in all_paths:
          all_paths.add(p_tuple)
        continue
      last_node = path[-1]
      for neighbor in G.neighbors(last_node):
        if neighbor not in path:
          queue.append(path + [neighbor])

  # Hiển thị kết quả lên cửa sổ 4 dạng text kèm Predicate
  text_output.config(state=tk.NORMAL)
  text_output.delete("1.0", tk.END)

  text_output.insert(
      tk.END,
      f"Danh sách tất cả các con đường có độ dài k = {k} (kèm Predicate):\n",
  )
  text_output.insert(tk.END, "=" * 65 + "\n")

  if all_paths:
    for idx, p in enumerate(sorted(all_paths), 1):
      path_parts = [p[0]]
      for i in range(len(p) - 1):
        u, v = p[i], p[i + 1]
        pred = edge_predicates.get((u, v), "")
        path_parts.append(f"--[{pred}]--> {v}")
      path_str = " ".join(path_parts)
      text_output.insert(tk.END, f"{idx}. {path_str}\n")
  else:
    text_output.insert(
        tk.END, f"Không tìm thấy con đường nào có độ dài k = {k}!\n"
    )

  text_output.config(state=tk.DISABLED)


# Các nút điều khiển trên cùng (Đã loại bỏ Choose KG Folder)
draw_top_btn = tk.Button(
    top_control_frame,
    text="Draw Neighbours",
    command=draw_neighbours,
    bg="lightgreen",
    font=("Arial", 9, "bold"),
)
draw_top_btn.pack(side=tk.LEFT, padx=2)

show_img_btn = tk.Button(
    top_control_frame,
    text="Show Image",
    command=show_image,
    bg="plum",
    font=("Arial", 9, "bold"),
)
show_img_btn.pack(side=tk.LEFT, padx=2)

find_k_btn = tk.Button(
    top_control_frame,
    text="Find k path",
    command=find_k_path,
    bg="orange",
    font=("Arial", 9, "bold"),
)
find_k_btn.pack(side=tk.LEFT, padx=5)

clear_top_btn = tk.Button(
    top_control_frame,
    text="Clear All",
    command=clear_all,
    bg="red",
    fg="white",
    font=("Arial", 9, "bold"),
)
clear_top_btn.pack(side=tk.LEFT, padx=2)


# Sử dụng PanedWindow để các cửa sổ có thể thay đổi kích thước bằng cách kéo (drag)
main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Khung bên trái chứa Cửa sổ 1 và Cửa sổ 2
left_pane = tk.PanedWindow(main_pane, orient=tk.VERTICAL, sashrelief=tk.RAISED)
main_pane.add(left_pane)

# Khung bên phải chứa Cửa sổ 3 và Cửa sổ 4
right_pane = tk.PanedWindow(main_pane, orient=tk.VERTICAL, sashrelief=tk.RAISED)
main_pane.add(right_pane)

# ================= CỬA SỔ 1 =================
win1_frame = tk.Frame(
    left_pane,
    bg="#E6F2FF",
    highlightbackground="darkblue",
    highlightthickness=2,
    bd=2,
)
left_pane.add(win1_frame, height=400)

win1_header = tk.Frame(win1_frame, bg="yellow")
win1_header.pack(fill=tk.X)
tk.Label(
    win1_header,
    text="Cửa sổ 1: Dữ liệu Tri thức",
    bg="yellow",
    fg="red",
    font=("Arial", 10, "bold"),
).pack(anchor="w", padx=5, pady=2)

# Nhãn hiển thị tên tệp nằm phía trên Cửa sổ 1
file_name_label = tk.Label(
    win1_frame,
    text=f"Tệp KG hiện tại: {os.path.basename(current_kg_file)}",
    bg="#E6F2FF",
    fg="darkgreen",
    font=("Arial", 9, "bold"),
)
file_name_label.pack(anchor="w", padx=5, pady=2)

# Khung chứa Combobox lọc Head, Tail và nút Filter
filter_frame = tk.Frame(win1_frame, bg="#E6F2FF")
filter_frame.pack(fill=tk.X, padx=5, pady=5)

tk.Label(
    filter_frame, text="Head:", bg="#E6F2FF", fg="red", font=("Arial", 9, "bold")
).pack(side=tk.LEFT, padx=2)
head_combobox = ttk.Combobox(filter_frame, width=15, state="normal")
head_combobox.pack(side=tk.LEFT, padx=2)

tk.Label(
    filter_frame, text="Tail:", bg="#E6F2FF", fg="red", font=("Arial", 9, "bold")
).pack(side=tk.LEFT, padx=2)
tail_combobox = ttk.Combobox(filter_frame, width=15, state="normal")
tail_combobox.pack(side=tk.LEFT, padx=2)


def filter_data():
  selected_head = head_combobox.get().strip()
  selected_tail = tail_combobox.get().strip()

  for item in tree.get_children():
    tree.delete(item)

  try:
    with open(current_kg_file, mode="r", encoding="utf-8") as f:
      reader = csv.DictReader(f)
      for row in reader:
        match_head = (
            (not selected_head)
            or (selected_head.lower() == "all")
            or (row["Head"] == selected_head)
        )
        match_tail = (
            (not selected_tail)
            or (selected_tail.lower() == "all")
            or (row["Tail"] == selected_tail)
        )
        if match_head and match_tail:
          tree.insert(
              "", tk.END, values=(row["Head"], row["Predicate"], row["Tail"])
          )
  except Exception as e:
    print("Lỗi lọc file:", e)


filter_btn = tk.Button(
    filter_frame,
    text="Filter",
    command=filter_data,
    bg="lightblue",
    font=("Arial", 9, "bold"),
)
filter_btn.pack(side=tk.LEFT, padx=5)


# Khung chứa Source và ô nhập k= mặc định giá trị 2
source_frame = tk.Frame(win1_frame, bg="#E6F2FF")
source_frame.pack(fill=tk.X, padx=5, pady=2)

tk.Label(
    source_frame, text="Source:", bg="#E6F2FF", fg="red", font=("Arial", 9, "bold")
).pack(side=tk.LEFT, padx=2)
source_entry = tk.Entry(source_frame, width=18)
source_entry.pack(side=tk.LEFT, padx=2)

tk.Label(
    source_frame, text="k=", bg="#E6F2FF", fg="red", font=("Arial", 9, "bold")
).pack(side=tk.LEFT, padx=5)
k_entry = tk.Entry(source_frame, width=5)
k_entry.pack(side=tk.LEFT, padx=2)
k_entry.insert(0, "2")  # Giá trị mặc định là 2

# Treeview hiển thị file CSV ở cửa sổ 1
tree_frame = tk.Frame(win1_frame, bg="#E6F2FF")
tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

tree_scroll = ttk.Scrollbar(tree_frame)
tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

tree = ttk.Treeview(
    tree_frame,
    columns=("Head", "Predicate", "Tail"),
    show="headings",
    yscrollcommand=tree_scroll.set,
)
tree_scroll.config(command=tree.yview)

tree.heading("Head", text="Head")
tree.heading("Predicate", text="Predicate")
tree.heading("Tail", text="Tail")

tree.column("Head", width=120, anchor="w")
tree.column("Predicate", width=120, anchor="w")
tree.column("Tail", width=150, anchor="w")
tree.pack(fill=tk.BOTH, expand=True)

# Tự động tải dữ liệu từ file Data/edges.csv khi khởi động
load_data_to_tree(current_kg_file)


def on_row_select(event):
  selected_items = tree.selection()
  if selected_items:
    item = selected_items[0]
    values = tree.item(item, "values")
    if values:
      source_entry.delete(0, tk.END)
      source_entry.insert(0, values[0])


tree.bind("<<TreeviewSelect>>", on_row_select)


# ================= CỬA SỔ 2 =================
win2_frame = tk.Frame(
    left_pane,
    bg="#E6F2FF",
    highlightbackground="darkblue",
    highlightthickness=2,
    bd=2,
)
left_pane.add(win2_frame, height=200)

win2_header = tk.Frame(win2_frame, bg="yellow")
win2_header.pack(fill=tk.X)
tk.Label(
    win2_header,
    text="Cửa sổ 2: Hướng dẫn & Giới thiệu",
    bg="yellow",
    fg="red",
    font=("Arial", 10, "bold"),
).pack(anchor="w", padx=5, pady=2)

win2_text_frame = tk.Frame(win2_frame, bg="#E6F2FF")
win2_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

win2_scroll = ttk.Scrollbar(win2_text_frame)
win2_scroll.pack(side=tk.RIGHT, fill=tk.Y)

guide_text = tk.Text(
    win2_text_frame,
    wrap=tk.WORD,
    yscrollcommand=win2_scroll.set,
    bg="#E6F2FF",
    font=("Arial", 9),
    bd=0,
)
win2_scroll.config(command=guide_text.yview)
guide_text.pack(fill=tk.BOTH, expand=True)

intro_content = (
    "📖 GIỚI THIỆU SÁCH 'Những cây thuốc và vị thuốc Việt Nam'\n"
    "• Tác giả: Giáo sư Tiến Sĩ Đỗ Tất Lợi.\n"
    "Sách hệ thống hóa đồ sộ các kiến thức về cây thuốc, vị thuốc, động vật và khoáng vật \n"
    "làm thuốc ở Việt Nam. Nội dung bao gồm các phần chung về lý luận y học cổ truyền \n"
    "(âm dương, ngũ hành, phương pháp bào chế), phân loại chi tiết các nhóm cây thuốc theo tác dụng \n"
    " chữa bệnh (như chữa mụn nhọt, bệnh phụ nữ, tiêu hóa, cảm sốt, tim mạch...),\n"
    " >----> Trong phần này sẽ mô tả chi tiết về cây thuốc kèm hình ảnh cây thuốc.\n\n"
    "🛠 HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:\n"
    "1. Chương trình tự động đọc tệp tri thức từ đường dẫn 'edges.csv'.\n"
    "2. Dùng Combobox Head/Tail (chọn 'All' để xem tất cả) và nhấn 'Filter'.\n"
    "3. Nhấn 'Draw Neighbours' để vẽ đồ thị node kề của một dược liệu (Source).\n"
    "4. Nhấn 'Show Image' để tự động hiển thị file ảnh 'SachCayThuocGSDoTatLoi.jpg' lên Cửa sổ 3.\n"
    "5. Nhấn 'Find k path' để tìm tất cả đường đi chiều dài k kèm Predicate ở Cửa sổ 4.\n"
    "6. Nhấn nút 'Clear All' (màu đỏ) để làm sạch toàn bộ màn hình."
)

guide_text.insert(tk.END, intro_content)
guide_text.config(state=tk.DISABLED)


# ================= CỬA SỔ 3 =================
win3_frame = tk.Frame(
    right_pane,
    bg="#E6F2FF",
    highlightbackground="darkblue",
    highlightthickness=2,
    bd=2,
)
right_pane.add(win3_frame, height=400)

win3_header = tk.Frame(win3_frame, bg="yellow")
win3_header.pack(fill=tk.X)
tk.Label(
    win3_header,
    text="Cửa sổ 3: Đồ thị Node kề / Hiển thị Ảnh",
    bg="yellow",
    fg="red",
    font=("Arial", 10, "bold"),
).pack(anchor="w", padx=5, pady=2)


# ================= CỬA SỔ 4 =================
win4_frame = tk.Frame(
    right_pane,
    bg="#E6F2FF",
    highlightbackground="darkblue",
    highlightthickness=2,
    bd=2,
)
right_pane.add(win4_frame, height=200)

win4_header = tk.Frame(win4_frame, bg="yellow")
win4_header.pack(fill=tk.X)
tk.Label(
    win4_header,
    text="Cửa sổ 4: Kết quả văn bản (k-path kèm Predicate)",
    bg="yellow",
    fg="red",
    font=("Arial", 10, "bold"),
).pack(anchor="w", padx=5, pady=2)

text_frame = tk.Frame(win4_frame, bg="#E6F2FF")
text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

text_scroll = ttk.Scrollbar(text_frame)
text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

text_output = tk.Text(
    text_frame,
    wrap=tk.WORD,
    yscrollcommand=text_scroll.set,
    bg="white",
    font=("Courier New", 9),
)
text_scroll.config(command=text_output.yview)
text_output.pack(fill=tk.BOTH, expand=True)
text_output.config(state=tk.DISABLED)

canvas_widget = None

root.mainloop()