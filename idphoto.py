#!/usr/bin/env python3
# idphoto.py
# 电子证件照处理：换底色（蓝/白/红/灰/黑）、裁切到一寸/两寸、可调分辨率与文件大小(KB)。
# ID photo tool: change background (blue/white/red/gray/black), crop to 1-inch/2-inch,
# adjustable DPI resolution and output file size (KB). Pillow only.
#
# 用法 / Usage:
#   py idphoto.py                 # 图形界面 / GUI
#   py idphoto.py input.jpg --color 蓝 --size 一寸 --dpi 300 --kb 50
#
# 依赖 / Deps:  pip install pillow

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageFilter

BG_COLORS = {  # 常用证件照底色 / common ID photo backgrounds
    "蓝": (67, 142, 219),
    "白": (255, 255, 255),
    "红": (216, 28, 28),
    "灰": (128, 128, 128),
    "黑": (0, 0, 0),
}
SIZES_MM = {  # (宽, 高) 单位 mm / (width, height) in mm
    "一寸": (25, 35),
    "两寸": (35, 49),
}
MM_PER_INCH = 25.4

# 让 rembg 模型从 D 盘加载（不占 C 盘）/ load rembg model from D: drive
_U2 = r"D:\codeby\u2net"
if os.path.isdir(_U2) and "U2NET_HOME" not in os.environ:
    os.environ["U2NET_HOME"] = _U2


# ----------------------------- 背景处理 / Background -----------------------------

def sample_bg(im):
    """采样四边背景色（取中值，抗噪）/ Sample border color (median)."""
    w, h = im.size
    m = max(3, int(min(w, h) * 0.06))
    pts = []
    for c in [im.crop((0, 0, w, m)), im.crop((0, h - m, w, h)),
             im.crop((0, 0, m, h)), im.crop((w - m, 0, w, h))]:
        pts.extend(c.getdata())
    rs = sorted(p[0] for p in pts)
    gs = sorted(p[1] for p in pts)
    bs = sorted(p[2] for p in pts)
    n = len(rs)
    med = (rs[n // 2], gs[n // 2], bs[n // 2])
    return med


def replace_bg(im, target, thr):
    """把接近背景色的像素替换为目标底色（带轻微羽化）/ Replace bg, slight feather."""
    src = im.convert("RGB")
    bg = sample_bg(src)
    px = src.getdata()
    br, bgc, bb = bg
    tr, tg, tb = target
    out = []
    for (r, g, b) in px:
        d = abs(r - br) + abs(g - bgc) + abs(b - bb)  # 0..765
        if d <= thr:
            out.append((tr, tg, tb))
        elif d >= thr * 2:
            out.append((r, g, b))
        else:
            t = (d - thr) / thr  # 0..1 羽化过渡 / feather
            out.append((int(r * (1 - t) + tr * t),
                        int(g * (1 - t) + tg * t),
                        int(b * (1 - t) + tb * t)))
    res = Image.new("RGB", src.size)
    res.putdata(out)
    res = res.filter(ImageFilter.SMOOTH)
    return res


def crop_to_aspect(im, aspect):
    """居中裁切到目标宽高比 / Center-crop to target aspect ratio."""
    w, h = im.size
    cur = w / h
    if cur > aspect:
        nw = int(h * aspect)
        x = (w - nw) // 2
        return im.crop((x, 0, x + nw, h))
    else:
        nh = int(w / aspect)
        y = (h - nh) // 2
        return im.crop((0, y, w, y + nh))


def resize_to_dpi(im, size_mm, dpi):
    pw = max(1, round(size_mm[0] / MM_PER_INCH * dpi))
    ph = max(1, round(size_mm[1] / MM_PER_INCH * dpi))
    return im.resize((pw, ph), Image.LANCZOS)


def fit_kb(im, out_path, target_kb, dpi):
    """按目标 KB 调节 JPEG 质量保存 / Save JPEG, adjust quality to meet KB target."""
    for q in range(95, 19, -3):
        im.save(out_path, "JPEG", quality=q, dpi=(dpi, dpi), optimize=True)
        if target_kb is None or os.path.getsize(out_path) <= target_kb * 1024:
            break
    return os.path.getsize(out_path)


def remove_bg_ai(im, target=None):
    """AI 人像抠图（rembg），可选合成到目标底色 / rembg matting, optional bg color."""
    from rembg import remove
    rgba = remove(im.convert("RGBA"))
    if target:
        bg = Image.new("RGBA", rgba.size, tuple(target) + (255,))
        return Image.alpha_composite(bg, rgba).convert("RGB")
    return rgba


def process(input_path, color, size_name, dpi, target_kb, out_path=None,
            custom_color=None, threshold=70, ai=False):
    im = Image.open(input_path).convert("RGB")
    if ai:
        target = custom_color if custom_color else (
            BG_COLORS.get(color) if color in BG_COLORS else None)
        im = remove_bg_ai(im, target)
    elif color and color != "无" and (color in BG_COLORS or custom_color):
        target = custom_color if custom_color else BG_COLORS[color]
        im = replace_bg(im, target, threshold)
    size_mm = SIZES_MM.get(size_name, SIZES_MM["一寸"])
    im = crop_to_aspect(im, size_mm[0] / size_mm[1])
    im = resize_to_dpi(im, size_mm, dpi)
    transparent = ai and (color == "无" or (not custom_color and color not in BG_COLORS))
    if out_path is None:
        base, _ = os.path.splitext(input_path)
        suffix = (color if color and color != "无" else "orig")
        out_path = f"{base}_idphoto_{suffix}_{size_name}{'.png' if transparent else '.jpg'}"
    if transparent:
        im.save(out_path, "PNG", dpi=(dpi, dpi))
        size = os.path.getsize(out_path)
    else:
        size = fit_kb(im, out_path, target_kb, dpi)
    return out_path, size


# ----------------------------- 图形界面 / GUI -----------------------------

def hide_console():
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def gui():
    hide_console()
    root = tk.Tk()
    root.title("电子证件照处理 / ID Photo")
    root.configure(bg="#1e1f22")
    root.geometry("560x600")

    state = {"path": None, "thumb": None}

    tk.Label(root, text="电子证件照：换底色 / 裁切尺寸 / 调分辨率与文件大小",
             bg="#1e1f22", fg="#e6e6e6", font=("", 11, "bold")).pack(pady=8)

    frm = tk.Frame(root, bg="#1e1f22")
    frm.pack(fill="x", padx=16)

    path_var = tk.StringVar()

    def choose():
        p = filedialog.askopenfilename(
            filetypes=[("图片", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if not p:
            return
        state["path"] = p
        path_var.set(p)
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((180, 180))
            state["thumb"] = ImageTk.PhotoImage(im)
            pv.config(image=state["thumb"])
        except Exception as e:
            messagebox.showerror("错误", str(e))

    tk.Button(frm, text="选择照片 / Open", bg="#e6a23c", fg="#1e1f22",
              command=choose).grid(row=0, column=0, padx=4, pady=4)
    pv = tk.Label(frm, bg="#2b2d30", width=26, height=10, text="预览 / preview")
    pv.grid(row=0, column=1, padx=8)
    tk.Entry(frm, textvariable=path_var, bg="#2b2d30", fg="#e6e6e6",
             width=30).grid(row=1, column=0, columnspan=2, pady=4, sticky="w")

    # 底色 / background
    tk.Label(root, text="底色 / Background", bg="#1e1f22", fg="#9e9e9e").pack(
        anchor="w", padx=16, pady=(8, 0))
    color_var = tk.StringVar(value="蓝")
    colors = list(BG_COLORS.keys()) + ["无"]
    tk.OptionMenu(root, color_var, *colors).pack(anchor="w", padx=16)

    ai_var = tk.BooleanVar(value=False)
    tk.Checkbutton(root, text="AI 智能抠图(rembg) / AI matting",
                   variable=ai_var, bg="#1e1f22", fg="#e6e6e6",
                   selectcolor="#2b2d30").pack(anchor="w", padx=16)

    # 尺寸 / size
    tk.Label(root, text="尺寸 / Size", bg="#1e1f22", fg="#9e9e9e").pack(
        anchor="w", padx=16, pady=(8, 0))
    size_var = tk.StringVar(value="一寸")
    tk.OptionMenu(root, size_var, *SIZES_MM.keys()).pack(anchor="w", padx=16)

    # 分辨率 / DPI
    tk.Label(root, text="分辨率 DPI（默认 300）/ Resolution", bg="#1e1f22",
             fg="#9e9e9e").pack(anchor="w", padx=16, pady=(8, 0))
    dpi_var = tk.StringVar(value="300")
    tk.Entry(root, textvariable=dpi_var, bg="#2b2d30", fg="#e6e6e6",
             width=10).pack(anchor="w", padx=16)

    # 目标 KB / target size
    tk.Label(root, text="目标文件大小 KB（留空=不限制）/ Target size KB",
             bg="#1e1f22", fg="#9e9e9e").pack(anchor="w", padx=16, pady=(8, 0))
    kb_var = tk.StringVar(value="50")
    tk.Entry(root, textvariable=kb_var, bg="#2b2d30", fg="#e6e6e6",
             width=10).pack(anchor="w", padx=16)

    # 容差 / threshold
    tk.Label(root, text="背景容差 / BG tolerance (越大替换越多)",
             bg="#1e1f22", fg="#9e9e9e").pack(anchor="w", padx=16, pady=(8, 0))
    thr_var = tk.IntVar(value=70)
    tk.Scale(root, variable=thr_var, from_=20, to=160, orient="horizontal",
             bg="#1e1f22", fg="#e6e6e6", length=300).pack(anchor="w", padx=16)

    def runproc():
        if not state["path"]:
            messagebox.showinfo("提示", "先选择照片 / choose a photo first")
            return
        # 后台线程处理，避免 AI 模型推理卡死界面 / run in thread, keep UI alive
        btn.config(state="disabled", text="处理中… / processing…")
        status.config(text="正在处理，AI 抠图首次约需 30-60 秒 / working…", fg="#e6a23c")

        def worker():
            try:
                dpi = int(dpi_var.get() or 300)
                kb = int(kb_var.get()) if kb_var.get().strip() else None
                out, size = process(state["path"], color_var.get(),
                                    size_var.get(), dpi, kb, None, None,
                                    thr_var.get(), ai_var.get())
                root.after(0, lambda: done(out, size))
            except Exception as e:
                root.after(0, lambda: failed(e))

        def done(out, size):
            btn.config(state="normal", text="处理 / Process")
            status.config(text="完成 / done", fg="#8bc34a")
            messagebox.showinfo("完成 / Done",
                                f"已保存 / saved:\n{out}\n大小 / size: {size//1024} KB")
            try:
                os.startfile(os.path.dirname(out))
            except OSError:
                pass

        def failed(e):
            btn.config(state="normal", text="处理 / Process")
            status.config(text="失败 / failed", fg="#ef5350")
            messagebox.showerror("处理失败 / Failed", str(e))

        threading.Thread(target=worker, daemon=True).start()

    btn = tk.Button(root, text="处理 / Process", bg="#e6a23c", fg="#1e1f22",
                    font=("", 12, "bold"), command=runproc)
    btn.pack(pady=14)
    status = tk.Label(root, text="", bg="#1e1f22", fg="#9e9e9e")
    status.pack()

    root.mainloop()


# ----------------------------- 命令行 / CLI -----------------------------

def cli(argv):
    import argparse
    ap = argparse.ArgumentParser(description="电子证件照处理 / ID photo tool")
    ap.add_argument("input")
    ap.add_argument("--color", default="蓝", choices=list(BG_COLORS.keys()) + ["无"])
    ap.add_argument("--size", default="一寸", choices=list(SIZES_MM.keys()))
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--kb", type=int, default=None, help="目标 KB，0=不限制")
    ap.add_argument("--thr", type=int, default=70)
    ap.add_argument("--ai", action="store_true", help="AI 抠图(rembg) / AI matting")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    kb = a.kb if (a.kb and a.kb > 0) else None
    out, size = process(a.input, a.color, a.size, a.dpi, kb, a.out, None, a.thr, a.ai)
    print(f"已保存 / saved: {out}")
    print(f"大小 / size: {size/1024:.1f} KB, 尺寸 / size: {Image.open(out).size}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1].endswith((".jpg", ".png", ".jpeg",
                                                        ".bmp", ".webp")):
        # 第一个参数不是图片 → 当作 CLI 模式（argparse 接管）
        cli(sys.argv[1:])
    else:
        gui()
