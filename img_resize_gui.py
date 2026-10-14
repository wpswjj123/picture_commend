#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
img_resize_gui.py —— 图片分辨率转换器（图形界面版）

所有输入都在界面中完成，无需命令行参数：
  · 选择图片（单张 / 多张 / 整个文件夹）
  · 设定目标宽 × 高
  · 选择缩放模式：直接拉伸 / 等比留边 / 等比裁剪
  · 留边颜色（仅“等比留边”模式）
  · 输出目录、文件名后缀、输出格式
  · 实时预览「原图」与「效果预览」

依赖：Pillow（pip install pillow）
打包：pyinstaller --onefile --windowed --name img_resize_gui img_resize_gui.py
"""

import os
import sys
import threading
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk

APP_TITLE = "图片分辨率转换器"
SUPPORTED = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".gif")
PREVIEW_SIZE = (260, 200)   # 预览框最大尺寸

# 模式：显示名 -> 内部值
MODES = {
    "直接拉伸 (stretch)": "stretch",
    "等比留边 (fit)": "fit",
    "等比裁剪 (crop)": "crop",
}


# ----------------------------------------------------------------------
# 核心图像处理（与命令行版逻辑一致）
# ----------------------------------------------------------------------
def parse_bg(s):
    """'255,255,255' 或 '#ffffff' -> RGB 元组"""
    s = str(s).strip()
    if s.startswith("#"):
        h = s.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(int(x) for x in s.split(","))


def _fill_for(mode, bg):
    """按图像模式生成合适的填充色"""
    bg = tuple(bg)
    if mode in ("RGBA", "LA"):
        return bg + (255,) if len(bg) == 3 else bg
    if mode == "L":
        return bg[0]
    if mode in ("RGB", "P", "CMYK"):
        return bg[:3]
    return bg


def resize_image(img, W, H, mode, bg=(255, 255, 255)):
    """把 img 缩放为严格 W×H"""
    if mode == "stretch":
        return img.resize((W, H), Image.LANCZOS)

    if mode == "fit":
        tmp = img.copy()
        tmp.thumbnail((W, H), Image.LANCZOS)
        canvas = Image.new(img.mode, (W, H), _fill_for(img.mode, bg))
        canvas.paste(tmp, ((W - tmp.size[0]) // 2, (H - tmp.size[1]) // 2))
        return canvas

    if mode == "crop":
        sw, sh = img.size
        scale = max(W / sw, H / sh)
        nw, nh = round(sw * scale), round(sh * scale)
        tmp = img.resize((nw, nh), Image.LANCZOS)
        left = (nw - W) // 2
        top = (nh - H) // 2
        return tmp.crop((left, top, left + W, top + H))

    raise ValueError(f"未知模式: {mode}")


def make_output_path(src, out_dir, suffix, fmt):
    """根据设置生成输出文件完整路径"""
    base = os.path.splitext(os.path.basename(src))[0]
    src_ext = os.path.splitext(src)[1].lower()
    if fmt == "原格式":
        ext = src_ext if src_ext in SUPPORTED else ".png"
    else:
        ext = "." + fmt.lower()
    if ext == ".jpeg":
        ext = ".jpg"
    return os.path.join(out_dir, f"{base}{suffix}{ext}")


def save_image(img, path):
    """保存，jpeg 自动转 RGB 并给质量参数"""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        img.convert("RGB").save(path, quality=95)
    else:
        img.save(path)


# ----------------------------------------------------------------------
# 图形界面
# ----------------------------------------------------------------------
class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master, padx=10, pady=10)
        self.pack(fill="both", expand=True)

        self.files = []                 # 待处理图片完整路径
        self.bg_color = "#ffffff"       # 留边颜色
        self.busy = False
        self._preview_src = None
        self._preview_out = None
        self._preview_path = None

        self._build_ui()

    # ---------------- UI 构建 ----------------
    def _build_ui(self):
        # 1. 选择图片
        box1 = ttk.LabelFrame(self, text=" 1. 选择图片 ")
        box1.pack(fill="both", expand=True, pady=(0, 8))

        left = ttk.Frame(box1)
        left.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self.lst = tk.Listbox(left, height=8, selectmode="extended",
                              activestyle="none", exportselection=False)
        self.lst.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(left, orient="vertical", command=self.lst.yview)
        sb.pack(side="left", fill="y")
        self.lst.config(yscrollcommand=sb.set)
        self.lst.bind("<<ListboxSelect>>", lambda e: self.show_preview())

        btns = ttk.Frame(box1)
        btns.pack(side="left", fill="y", padx=6, pady=6)
        ttk.Button(btns, text="添加图片…", width=14, command=self.add_files).pack(pady=2)
        ttk.Button(btns, text="添加文件夹…", width=14, command=self.add_folder).pack(pady=2)
        ttk.Button(btns, text="移除选中", width=14, command=self.remove_selected).pack(pady=2)
        ttk.Button(btns, text="清空列表", width=14, command=self.clear_files).pack(pady=2)

        # 预览区
        pv = ttk.Frame(box1)
        pv.pack(side="left", fill="y", padx=6, pady=6)
        ttk.Label(pv, text="原图").grid(row=0, column=0)
        self.lbl_src = tk.Label(pv, width=28, height=9, bg="#f0f0f0",
                                relief="solid", bd=1)
        self.lbl_src.grid(row=1, column=0, padx=2)
        ttk.Label(pv, text="效果预览").grid(row=0, column=1)
        self.lbl_out = tk.Label(pv, width=28, height=9, bg="#f0f0f0",
                                relief="solid", bd=1)
        self.lbl_out.grid(row=1, column=1, padx=2)
        self.lbl_info = ttk.Label(pv, text="未选择图片", foreground="#666")
        self.lbl_info.grid(row=2, column=0, columnspan=2, pady=(4, 0))

        # 2. 输出设置
        box2 = ttk.LabelFrame(self, text=" 2. 输出设置 ")
        box2.pack(fill="x", pady=(0, 8))

        r = 0
        # 目标尺寸
        ttk.Label(box2, text="目标尺寸：").grid(row=r, column=0, sticky="e", padx=4, pady=4)
        sz = ttk.Frame(box2)
        sz.grid(row=r, column=1, columnspan=4, sticky="w")
        ttk.Label(sz, text="宽").pack(side="left")
        self.ent_w = ttk.Entry(sz, width=8)
        self.ent_w.pack(side="left", padx=(2, 8))
        ttk.Label(sz, text="高").pack(side="left")
        self.ent_h = ttk.Entry(sz, width=8)
        self.ent_h.pack(side="left", padx=(2, 8))
        ttk.Label(sz, text="px").pack(side="left")
        self.ent_w.insert(0, "500")
        self.ent_h.insert(0, "300")

        # 模式
        r += 1
        ttk.Label(box2, text="缩放模式：").grid(row=r, column=0, sticky="e", padx=4, pady=4)
        self.cmb_mode = ttk.Combobox(box2, width=22, state="readonly",
                                     values=list(MODES.keys()))
        self.cmb_mode.grid(row=r, column=1, sticky="w", pady=4)
        self.cmb_mode.current(0)
        self.cmb_mode.bind("<<ComboboxSelected>>", lambda e: self.on_mode_change())
        self.lbl_mode_hint = ttk.Label(box2, text="", foreground="#666")
        self.lbl_mode_hint.grid(row=r, column=2, columnspan=3, sticky="w", padx=8)

        # 留边颜色
        r += 1
        self.lbl_bg = ttk.Label(box2, text="留边颜色：")
        self.lbl_bg.grid(row=r, column=0, sticky="e", padx=4, pady=4)
        bgf = ttk.Frame(box2)
        bgf.grid(row=r, column=1, columnspan=4, sticky="w")
        self.btn_bg = tk.Button(bgf, width=4, bg=self.bg_color, command=self.choose_bg)
        self.btn_bg.pack(side="left")
        self.lbl_bg_hex = ttk.Label(bgf, text=self.bg_color)
        self.lbl_bg_hex.pack(side="left", padx=7)
        ttk.Label(bgf, text="（仅“等比留边”生效）", foreground="#999").pack(side="left")

        # 输出目录
        r += 1
        ttk.Label(box2, text="输出目录：").grid(row=r, column=0, sticky="e", padx=4, pady=4)
        od = ttk.Frame(box2)
        od.grid(row=r, column=1, columnspan=4, sticky="we")
        self.var_same = tk.BooleanVar(value=True)
        ttk.Checkbutton(od, text="与源文件同目录", variable=self.var_same,
                        command=self.on_same_toggle).pack(side="left")
        self.ent_dir = ttk.Entry(od, width=40)
        self.ent_dir.pack(side="left", padx=6)
        self.btn_dir = ttk.Button(od, text="浏览…", command=self.choose_dir)
        self.btn_dir.pack(side="left")
        self.on_same_toggle()

        # 后缀 & 格式
        r += 1
        ttk.Label(box2, text="文件名后缀：").grid(row=r, column=0, sticky="e", padx=4, pady=4)
        self.ent_suffix = ttk.Entry(box2, width=12)
        self.ent_suffix.grid(row=r, column=1, sticky="w", pady=4)
        self.ent_suffix.insert(0, "_resized")
        ttk.Label(box2, text="输出格式：").grid(row=r, column=2, sticky="e", padx=4)
        self.cmb_fmt = ttk.Combobox(box2, width=10, state="readonly",
                                    values=["PNG", "JPG", "原格式"])
        self.cmb_fmt.grid(row=r, column=3, sticky="w", pady=4)
        self.cmb_fmt.current(0)

        box2.columnconfigure(4, weight=1)

        # 3. 操作
        box3 = ttk.Frame(self)
        box3.pack(fill="x", pady=(0, 6))
        self.btn_run = ttk.Button(box3, text="开始转换", command=self.start)
        self.btn_run.pack(side="left")
        ttk.Button(box3, text="打开输出目录", command=self.open_outdir).pack(side="left", padx=8)
        self.btn_preview = ttk.Button(box3, text="刷新效果预览", command=self.show_preview)
        self.btn_preview.pack(side="left")

        self.pbar = ttk.Progressbar(box3, mode="determinate", length=220)
        self.pbar.pack(side="right")

        # 4. 日志
        box4 = ttk.LabelFrame(self, text=" 日志 ")
        box4.pack(fill="both", expand=True)
        self.txt = tk.Text(box4, height=7, wrap="word", state="disabled")
        self.txt.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        tsb = ttk.Scrollbar(box4, orient="vertical", command=self.txt.yview)
        tsb.pack(side="left", fill="y")
        self.txt.config(yscrollcommand=tsb.set)

        self.on_mode_change()
        self.log("提示：先「添加图片」，填好目标尺寸与模式，再点「开始转换」。")

    # ---------------- 交互回调 ----------------
    def on_mode_change(self):
        mode = MODES[self.cmb_mode.get()]
        hints = {
            "stretch": "直接拉伸铺满，可能变形",
            "fit": "等比缩放 + 居中留边，不变形",
            "crop": "等比缩放 + 居中裁剪，不变形、无留边",
        }
        self.lbl_mode_hint.config(text=hints.get(mode, ""))
        state = "normal" if mode == "fit" else "disabled"
        self.btn_bg.config(state=state)

    def on_same_toggle(self):
        same = self.var_same.get()
        self.ent_dir.config(state="disabled" if same else "normal")
        self.btn_dir.config(state="disabled" if same else "normal")

    def choose_bg(self):
        from tkinter import colorchooser
        c = colorchooser.askcolor(color=self.bg_color, title="选择留边颜色")
        if c and c[1]:
            self.bg_color = c[1]
            self.btn_bg.config(bg=self.bg_color)
            self.lbl_bg_hex.config(text=self.bg_color)
            self.show_preview()

    def choose_dir(self):
        d = filedialog.askdirectory(title="选择输出目录")
        if d:
            self.ent_dir.delete(0, "end")
            self.ent_dir.insert(0, d)

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff *.gif"),
                       ("所有文件", "*.*")])
        if paths:
            self._add(list(paths))

    def add_folder(self):
        d = filedialog.askdirectory(title="选择文件夹")
        if not d:
            return
        found = []
        for root, _, names in os.walk(d):
            for n in sorted(names):
                if os.path.splitext(n)[1].lower() in SUPPORTED:
                    found.append(os.path.join(root, n))
        if found:
            self._add(found)
        else:
            messagebox.showinfo(APP_TITLE, "该文件夹内没有找到支持的图片。")

    def _add(self, paths):
        added = 0
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.lst.insert("end", os.path.basename(p))
                added += 1
        self.log(f"已添加 {added} 张图片，共 {len(self.files)} 张。")
        if self.lst.size() and not self.lst.curselection():
            self.lst.selection_set(0)
        self.show_preview()

    def remove_selected(self):
        for i in reversed(self.lst.curselection()):
            self.lst.delete(i)
            del self.files[i]
        self.show_preview()

    def clear_files(self):
        self.lst.delete(0, "end")
        self.files.clear()
        self._set_preview(self.lbl_src, None)
        self._set_preview(self.lbl_out, None)
        self.lbl_info.config(text="未选择图片")
        self.log("已清空列表。")

    # ---------------- 预览 ----------------
    def _current_file(self):
        sel = self.lst.curselection()
        if sel:
            idx = sel[0]
            if 0 <= idx < len(self.files):
                return self.files[idx]
        return self.files[0] if self.files else None

    def _set_preview(self, label, im):
        if im is None:
            label.config(image="", text="")
            return
        im = im.copy()
        im.thumbnail(PREVIEW_SIZE, Image.LANCZOS)
        if im.mode == "P":
            im = im.convert("RGBA")
        ref = ImageTk.PhotoImage(im)
        label.config(image=ref, text="")
        if label is self.lbl_src:
            self._preview_src = ref
        else:
            self._preview_out = ref

    def show_preview(self):
        path = self._current_file()
        if not path:
            return
        try:
            img = Image.open(path)
            self._set_preview(self.lbl_src, img.convert("RGBA")
                              if img.mode == "P" else img)

            W, H, mode, bg, ok = self._read_settings(show_error=False)
            if not ok:
                self.lbl_info.config(text=f"原图：{img.size[0]} × {img.size[1]}")
                return
            out = resize_image(img.convert(img.mode), W, H, mode, bg)
            self._set_preview(self.lbl_out, out)
            self.lbl_info.config(
                text=f"原图 {img.size[0]}×{img.size[1]}  →  输出 {out.size[0]}×{out.size[1]}  [{mode}]")
        except Exception as e:
            self.lbl_info.config(text=f"预览失败：{e}")

    # ---------------- 参数读取 ----------------
    def _read_settings(self, show_error=True):
        try:
            W = int(self.ent_w.get())
            H = int(self.ent_h.get())
            if W <= 0 or H <= 0:
                raise ValueError("宽高必须为正整数")
        except ValueError as e:
            if show_error:
                messagebox.showerror(APP_TITLE, f"目标尺寸无效：{e}")
            return None, None, None, None, False

        mode = MODES[self.cmb_mode.get()]
        bg = parse_bg(self.bg_color) if mode == "fit" else (255, 255, 255)
        return W, H, mode, bg, True

    def _resolve_outdir(self, src):
        if self.var_same.get():
            return os.path.dirname(os.path.abspath(src))
        d = self.ent_dir.get().strip()
        return d or os.path.dirname(os.path.abspath(src))

    # ---------------- 执行 ----------------
    def start(self):
        if self.busy:
            return
        if not self.files:
            messagebox.showwarning(APP_TITLE, "请先添加要处理的图片。")
            return
        W, H, mode, bg, ok = self._read_settings()
        if not ok:
            return
        if not self.var_same.get() and not self.ent_dir.get().strip():
            messagebox.showwarning(APP_TITLE, "请选择输出目录，或勾选“与源文件同目录”。")
            return

        self.busy = True
        self.btn_run.config(state="disabled")
        self.pbar.config(maximum=len(self.files), value=0)
        t = threading.Thread(target=self._run_job,
                             args=(W, H, mode, bg), daemon=True)
        t.start()

    def _run_job(self, W, H, mode, bg):
        suffix = self.ent_suffix.get()
        fmt = self.cmb_fmt.get()
        ok_n = 0
        fail = 0
        last_dir = None
        for i, src in enumerate(list(self.files), 1):
            try:
                img = Image.open(src)
                out_img = resize_image(img.convert(img.mode), W, H, mode, bg)
                out_dir = self._resolve_outdir(src)
                os.makedirs(out_dir, exist_ok=True)
                out_path = make_output_path(src, out_dir, suffix, fmt)
                if os.path.abspath(out_path) == os.path.abspath(src):
                    out_path = os.path.splitext(out_path)[0] + "_new" + os.path.splitext(out_path)[1]
                save_image(out_img, out_path)
                last_dir = out_dir
                ok_n += 1
                self.log(f"[{i}/{len(self.files)}] ✓ {os.path.basename(src)}"
                         f"  {img.size[0]}×{img.size[1]} → {out_img.size[0]}×{out_img.size[1]}"
                         f"  →  {out_path}")
            except Exception as e:
                fail += 1
                self.log(f"[{i}/{len(self.files)}] ✗ {os.path.basename(src)}：{e}")
            self.pbar.config(value=i)

        self._last_outdir = last_dir
        self.log(f"完成：成功 {ok_n} 张，失败 {fail} 张。")
        self.busy = False
        self.btn_run.config(state="normal")
        if fail == 0:
            messagebox.showinfo(APP_TITLE, f"全部完成！成功处理 {ok_n} 张。")

    def open_outdir(self):
        d = getattr(self, "_last_outdir", None)
        if not d:
            if self.var_same.get():
                d = os.path.dirname(self._current_file()) if self._current_file() else None
            else:
                d = self.ent_dir.get().strip() or None
        if not d or not os.path.isdir(d):
            messagebox.showinfo(APP_TITLE, "还没有可打开的输出目录。")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(d)          # noqa
            elif sys.platform == "darwin":
                os.system(f'open "{d}"')
            else:
                os.system(f'xdg-open "{d}"')
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"打开目录失败：{e}")

    # ---------------- 日志 ----------------
    def log(self, msg):
        def _append():
            self.txt.config(state="normal")
            self.txt.insert("end", msg + "\n")
            self.txt.see("end")
            self.txt.config(state="disabled")
        try:
            self.after(0, _append)
        except Exception:
            _append()


# ----------------------------------------------------------------------
def main():
    # Windows 高分屏更清晰
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    root.title(APP_TITLE)
    root.minsize(880, 640)
    try:
        root.call("tk", "scaling", 1.2)
    except Exception:
        pass
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()