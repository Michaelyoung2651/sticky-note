import json
import os
import re
import sys
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox
import winreg


DATA_FILE = "schedule_data.json"
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class StickyScheduleApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sticky Note")
        self.root.resizable(False, False)
        self.root.configure(bg="#FFF8C6")
        # 去掉窗口边框和标题栏
        self.root.overrideredirect(True)
        # 设置为工具窗口，固定在桌面（不挡其他窗口）
        self.root.attributes("-toolwindow", True)
        self.root.attributes("-alpha", 0.95)

        self.width = 620
        self.height = 300
        self._place_top_right()

        self.columns = ("index", "time", "task", "done")
        self.tree = None
        self.grid_lines = []
        self.context_menu = None
        self.edit_widget = None
        self.edit_item = None
        self.edit_column = None
        self.time_options = self._build_time_options()

        self._build_ui()
        self._load_data()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_time_options(self):
        options = []
        for hour in range(24):
            for minute in (0, 30):
                options.append(f"{hour:02d}:{minute:02d}")
        return options

    def _place_top_right(self):
        screen_w = self.root.winfo_screenwidth()
        x = max(screen_w - self.width - 20, 0)
        y = 20
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Sticky.Treeview",
            rowheight=24,
            font=("Microsoft YaHei UI", 8),
            background="#FFFDF1",
            fieldbackground="#FFFDF1",
            foreground="#2D2D2D",
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "Sticky.Treeview.Heading",
            font=("Microsoft YaHei UI", 11, "bold"),
            background="#F4E79E",
            foreground="#3A3422",
            borderwidth=0,
            relief="flat",
            padding=(4, 0, 4, 0),
        )
        style.map("Sticky.Treeview", background=[("selected", "#FFE89A")], foreground=[("selected", "#1D1D1D")])
        style.configure("Sticky.TFrame", background="#FFF5BF")
        style.configure("Sticky.TLabel", background="#FFF5BF", foreground="#5A5230", font=("Microsoft YaHei UI", 9))
        style.configure("StickyTitle.TLabel", background="#FFFBEA", foreground="#4A422A", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("StickyDate.TLabel", background="#FFFBEA", foreground="#5E5536", font=("Microsoft YaHei UI", 9))

        container = ttk.Frame(self.root, style="Sticky.TFrame", padding=(14, 8, 14, 8))
        container.pack(fill=tk.BOTH, expand=True)

        shadow = tk.Frame(container, bg="#D9CF93", bd=0, highlightthickness=0)
        shadow.pack(fill=tk.BOTH, expand=True, padx=(2, 0), pady=(2, 0))

        card = tk.Frame(shadow, bg="#FFFBEA", bd=0, highlightthickness=1, highlightbackground="#DED39A")
        card.pack(fill=tk.BOTH, expand=True)

        top_bar = tk.Frame(card, bg="#F2E396", height=4, bd=0, highlightthickness=0)
        top_bar.pack(fill=tk.X)

        title_box = tk.Frame(card, bg="#FFFBEA", bd=0, highlightthickness=0)
        title_box.pack(fill=tk.X, padx=10, pady=(4, 2))
        title = ttk.Label(title_box, text="Sticky Note", style="StickyTitle.TLabel")
        title.pack(side=tk.LEFT)
        today_str = datetime.now().strftime("%Y-%m-%d")
        date_label = ttk.Label(title_box, text=today_str, style="StickyDate.TLabel")
        date_label.pack(side=tk.RIGHT)

        table_frame = ttk.Frame(card, style="Sticky.TFrame", padding=(8, 0, 8, 0))
        table_frame.pack(fill=tk.BOTH, expand=True)

        # 用固定宽度的 frame 包裹 treeview，防止右侧空白
        tree_container = tk.Frame(table_frame, bg="#FFFDF1")
        tree_container.pack(side=tk.LEFT, fill=tk.BOTH)

        self.tree = ttk.Treeview(
            tree_container,
            columns=self.columns,
            show="headings",
            selectmode="browse",
            style="Sticky.Treeview",
        )
        self.tree.tag_configure("row_odd", background="#FFFDF1")
        self.tree.tag_configure("row_even", background="#FFFDF1")
        self.tree.tag_configure("done_yes", foreground="#188043")
        self.tree.tag_configure("done_no", foreground="#C33B2E")
        self.tree.tag_configure("done_pending", foreground="#9B6B1A")

        headings = {"index": "序号", "time": "时间", "task": "事项", "done": "完成情况"}
        widths = {"index": 38, "time": 80, "task": 342, "done": 120}
        for col in self.columns:
            self.tree.heading(col, text=headings[col], anchor=tk.CENTER)
            self.tree.column(col, width=widths[col], minwidth=40, stretch=False, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self._on_tree_scroll)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.context_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#FFFBEA",
            fg="#3A3422",
            activebackground="#F4E79E",
            activeforeground="#2A2418",
            bd=1,
            relief="solid",
        )
        self.context_menu.add_command(label="新增一行", command=self.add_row)
        self.context_menu.add_command(label="删除选中", command=self.delete_selected)
        self.context_menu.add_command(label="一键刷新", command=self.refresh_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="开机启动", command=self.toggle_startup)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="退出", command=self._on_close)

        # 检查开机启动状态
        self._check_startup_status()

        self.root.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Double-1>", self._start_edit_cell)
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")
        self.tree.bind("<Configure>", lambda _e: self._schedule_grid_redraw(), add="+")
        self.tree.bind("<ButtonRelease-1>", lambda _e: self._schedule_grid_redraw(), add="+")
        self.tree.bind("<MouseWheel>", lambda _e: self._schedule_grid_redraw(), add="+")
        self.tree.bind("<Button-4>", lambda _e: self._schedule_grid_redraw(), add="+")
        self.tree.bind("<Button-5>", lambda _e: self._schedule_grid_redraw(), add="+")
        # 阻止列宽调整 - 只在表头区域阻止
        self.tree.bind("<B1-Motion>", self._block_header_resize, add="+")
        self.root.bind("<Button-1>", self._clear_selection_on_outside_click, add="+")
        self.root.after(50, self._draw_grid_lines)

    def _block_header_resize(self, event):
        # 只在表头区域（y < 30）阻止拖动
        if event.y < 30:
            return "break"
        return None

    def _on_tree_click(self, event):
        # 处理树形控件点击
        self._handle_single_click(event)

    def _insert_row(self, index, time_value="", task="", done="-"):
        row_tag = "row_odd" if int(index) % 2 == 1 else "row_even"
        if done == "√":
            tags = (row_tag, "done_yes")
        elif done == "×":
            tags = (row_tag, "done_no")
        else:
            tags = (row_tag, "done_pending")
        self.tree.insert("", tk.END, values=(index, time_value, task, done), tags=tags)
        self._schedule_grid_redraw()

    def add_row(self):
        next_index = len(self.tree.get_children()) + 1
        self._insert_row(next_index)
        self.save_data()

    def refresh_all(self):
        # 清空所有行，重新初始化 10 行
        self.tree.delete(*self.tree.get_children())
        for i in range(1, 11):
            self._insert_row(i, "", "", "-")
        self.save_data()

    def _get_exe_path(self):
        # 获取程序路径（兼容打包后和源码运行）
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
            return os.path.abspath(sys.argv[0])

    def _get_startup_key_path(self):
        return r"Software\Microsoft\Windows\CurrentVersion\Run"

    def _check_startup_status(self):
        # 检查是否已设置开机启动
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._get_startup_key_path())
            try:
                value, _ = winreg.QueryValueEx(key, "桌面便利贴")
                self.startup_enabled = (value == f'"{self._get_exe_path()}"')
            except FileNotFoundError:
                self.startup_enabled = False
            winreg.CloseKey(key)
        except Exception:
            self.startup_enabled = False

    def toggle_startup(self):
        # 切换开机启动状态
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._get_startup_key_path(), 0, winreg.KEY_SET_VALUE)
            exe_path = self._get_exe_path()
            if self.startup_enabled:
                # 取消开机启动
                winreg.DeleteValue(key, "桌面便利贴")
                self.startup_enabled = False
                messagebox.showinfo("提示", "已取消开机启动")
            else:
                # 设置开机启动
                winreg.SetValueEx(key, "桌面便利贴", 0, winreg.REG_SZ, f'"{exe_path}"')
                self.startup_enabled = True
                messagebox.showinfo("提示", "已设置开机启动")
            winreg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("错误", f"设置失败：{e}")

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        self.tree.delete(selected[0])
        self._reindex()
        self.save_data()
        self._schedule_grid_redraw()

    def _on_tree_scroll(self, *args):
        if self.tree:
            self.tree.yview(*args)
        self._schedule_grid_redraw()

    def _handle_single_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item or column != "#4":
            return
        self._toggle_done_item(item)

    def _toggle_done_item(self, item):
        values = list(self.tree.item(item, "values"))
        current = values[3]
        row_tag = "row_odd" if int(values[0]) % 2 == 1 else "row_even"
        if current == "-":
            values[3] = "√"
            tags = (row_tag, "done_yes")
        elif current == "√":
            values[3] = "×"
            tags = (row_tag, "done_no")
        else:
            values[3] = "-"
            tags = (row_tag, "done_pending")
        self.tree.item(item, values=values, tags=tags)
        self.save_data()

    def _clear_selection_on_outside_click(self, event):
        if not self.tree:
            return
        widget_path = str(event.widget)
        tree_path = str(self.tree)
        if widget_path == tree_path or widget_path.startswith(f"{tree_path}."):
            return
        self.tree.selection_remove(self.tree.selection())

    def _show_context_menu(self, event):
        if not self.tree or not self.context_menu:
            return
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
        else:
            self.tree.selection_remove(self.tree.selection())

        has_selection = bool(self.tree.selection())
        self.context_menu.entryconfig("删除选中", state=tk.NORMAL if has_selection else tk.DISABLED)
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def _clear_grid_lines(self):
        for line in self.grid_lines:
            try:
                line.destroy()
            except tk.TclError:
                pass
        self.grid_lines = []

    def _schedule_grid_redraw(self):
        self.root.after_idle(self._draw_grid_lines)

    def _draw_grid_lines(self):
        if not self.tree:
            return
        self._clear_grid_lines()

        line_color = "#CFC58A"
        total_w = self.tree.winfo_width()
        total_h = self.tree.winfo_height()
        if total_w <= 2 or total_h <= 2:
            return

        # Header-bottom separator line.
        first_visible_y = None
        for item in self.tree.get_children(""):
            bbox = self.tree.bbox(item, "#1")
            if bbox:
                first_visible_y = bbox[1]
                break
        header_bottom_y = first_visible_y - 1 if first_visible_y is not None else 33
        if 0 < header_bottom_y < total_h:
            header_line = tk.Frame(self.tree, bg=line_color, width=total_w, height=1, bd=0, highlightthickness=0)
            header_line.place(x=0, y=header_bottom_y)
            self.grid_lines.append(header_line)

        # Vertical inner lines based on actual visible cell geometry.
        first_visible_item = None
        for item in self.tree.get_children(""):
            if self.tree.bbox(item, "#1"):
                first_visible_item = item
                break

        if first_visible_item:
            # 画列与列之间的分隔线（每列的右边界）
            for col_index in range(1, len(self.columns)):
                prev_col = f"#{col_index}"
                prev_bbox = self.tree.bbox(first_visible_item, prev_col)
                if not prev_bbox:
                    continue
                # 当前列的右边界 = 列起始位置 + 列宽度
                x = prev_bbox[0] + prev_bbox[2]
                line = tk.Frame(self.tree, bg=line_color, width=1, height=total_h, bd=0, highlightthickness=0)
                line.place(x=x, y=0)
                self.grid_lines.append(line)
        else:
            # Fallback before rows are ready.
            x = 0
            for col in self.columns[:-1]:
                x += int(self.tree.column(col, "width"))
                line = tk.Frame(self.tree, bg=line_color, width=1, height=total_h, bd=0, highlightthickness=0)
                line.place(x=x, y=0)
                self.grid_lines.append(line)

        # Horizontal inner lines (follow visible rows while scrolling).
        for item in self.tree.get_children(""):
            bbox = self.tree.bbox(item, "#1")
            if not bbox:
                continue
            row_y = bbox[1] + bbox[3] - 1
            if row_y <= 0 or row_y >= total_h:
                continue
            line = tk.Frame(self.tree, bg=line_color, width=total_w, height=1, bd=0, highlightthickness=0)
            line.place(x=0, y=row_y)
            self.grid_lines.append(line)

    def _start_edit_cell(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item or not column:
            return

        col_index = int(column[1:]) - 1
        col_name = self.columns[col_index]
        if col_name in ("index", "done"):
            return

        x, y, w, h = self.tree.bbox(item, column)
        old_value = self.tree.item(item, "values")[col_index]

        if self.edit_widget:
            self.edit_widget.destroy()

        self.edit_item = item
        self.edit_column = col_index

        if col_name == "time":
            editor = ttk.Spinbox(self.tree, values=self.time_options, state="normal", wrap=True)
            editor.delete(0, tk.END)
            editor.insert(0, old_value if old_value else self.time_options[0])
            editor.select_range(0, tk.END)
            editor.bind("<MouseWheel>", self._spin_time_with_wheel)
            editor.bind("<Button-4>", self._spin_time_with_wheel)
            editor.bind("<Button-5>", self._spin_time_with_wheel)
        else:
            editor = ttk.Entry(self.tree)
            editor.insert(0, old_value)
            editor.select_range(0, tk.END)

        self.edit_widget = editor
        self.edit_widget.place(x=x, y=y, width=w, height=h)
        self.edit_widget.focus_set()
        self.edit_widget.bind("<Return>", self._commit_edit)
        self.edit_widget.bind("<FocusOut>", self._commit_edit)
        self.edit_widget.bind("<Escape>", self._cancel_edit)

    def _spin_time_with_wheel(self, event):
        if not self.edit_widget or self.edit_column is None:
            return "break"
        if self.columns[self.edit_column] != "time":
            return "break"
        delta = getattr(event, "delta", 0)
        if delta > 0 or getattr(event, "num", None) == 4:
            self.edit_widget.invoke("buttonup")
        else:
            self.edit_widget.invoke("buttondown")
        return "break"

    def _validate_time_value(self, value):
        if value == "":
            return True, value
        if not TIME_PATTERN.match(value):
            return False, value
        hour, minute = value.split(":")
        return True, f"{int(hour):02d}:{int(minute):02d}"

    def _commit_edit(self, _event=None):
        if not self.edit_widget or not self.edit_item or self.edit_column is None:
            return
        new_value = self.edit_widget.get().strip()
        if self.columns[self.edit_column] == "time":
            valid, normalized = self._validate_time_value(new_value)
            if not valid:
                messagebox.showwarning("时间格式不正确", "请输入有效时间，格式为 HH:MM（例如 09:30 或 14:10）。")
                self.edit_widget.focus_set()
                self.edit_widget.select_range(0, tk.END)
                return
            new_value = normalized
        values = list(self.tree.item(self.edit_item, "values"))
        values[self.edit_column] = new_value
        self.tree.item(self.edit_item, values=values)

        self.edit_widget.destroy()
        self.edit_widget = None
        self.edit_item = None
        self.edit_column = None
        self.save_data()
        self._schedule_grid_redraw()

    def _cancel_edit(self, _event=None):
        if self.edit_widget:
            self.edit_widget.destroy()
        self.edit_widget = None
        self.edit_item = None
        self.edit_column = None

    def _reindex(self):
        for i, item in enumerate(self.tree.get_children(), start=1):
            values = list(self.tree.item(item, "values"))
            values[0] = i
            done = values[3]
            row_tag = "row_odd" if i % 2 == 1 else "row_even"
            if done == "√":
                tags = (row_tag, "done_yes")
            elif done == "×":
                tags = (row_tag, "done_no")
            else:
                tags = (row_tag, "done_pending")
            self.tree.item(item, values=values, tags=tags)

    def save_data(self):
        rows = []
        for item in self.tree.get_children():
            index, time_value, task, done = self.tree.item(item, "values")
            rows.append({"index": index, "time": time_value, "task": task, "done": done})

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    def _load_data(self):
        if not os.path.exists(DATA_FILE):
            for i in range(1, 11):
                self._insert_row(i, "", "", "-")
            return

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                rows = json.load(f)
        except (json.JSONDecodeError, OSError):
            messagebox.showwarning("提示", "读取历史数据失败，将使用空白表格。")
            rows = []

        self.tree.delete(*self.tree.get_children())
        for row in rows:
            done_value = row.get("done", "-")
            if done_value in ("□", ""):
                done_value = "-"
            if done_value not in ("-", "√", "×"):
                done_value = "-"
            self._insert_row(
                row.get("index", ""),
                row.get("time", ""),
                row.get("task", ""),
                done_value,
            )
        self._reindex()
        self._schedule_grid_redraw()

    def _on_close(self):
        self.save_data()
        self.root.destroy()


if __name__ == "__main__":
    app_root = tk.Tk()
    StickyScheduleApp(app_root)
    app_root.mainloop()
