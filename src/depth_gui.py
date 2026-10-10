# -*- coding: utf-8 -*-
"""
视频深度图工具（GUI 版）
=========================
拖入视频 → 自动生成黑白深度视频 → 结果在 output/ 目录。
关闭窗口时自动结束所有后台进程。

本工具是一个图形界面外壳，底层深度估计由 reshot（Apache-2.0）完成：
    https://github.com/maosika-ai/reshot
"""
import os
import sys
import shutil
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

# ---------------------------------------------------------------- 路径定位
# 打包成 exe 后，__file__ 指向临时解包目录，必须用 exe 自身位置定位工具目录
if getattr(sys, "frozen", False):
    TOOL_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    TOOL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OUT_DIR = os.path.join(TOOL_DIR, "output")

# 模型权重缓存到工具目录；国内直连 HuggingFace 慢，默认走镜像。
# 若使用者在系统里已设置 HF_ENDPOINT / HF_HOME，则尊重其设置。
os.environ.setdefault("HF_HOME", os.path.join(TOOL_DIR, "models"))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ---------------------------------------------------------------- 拖拽支持
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except Exception:
    HAS_DND = False


def resolve_reshot_cmd():
    """找到可用的 reshot 入口，返回命令前缀（list）。"""
    candidates = [
        os.path.join(TOOL_DIR, "venv", "Scripts", "reshot.exe"),
        os.path.join(TOOL_DIR, ".venv", "Scripts", "reshot.exe"),
        os.path.join(TOOL_DIR, "venv", "bin", "reshot"),
        os.path.join(TOOL_DIR, ".venv", "bin", "reshot"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return [c]
    found = shutil.which("reshot")
    if found:
        return [found]
    # 兜底：用当前解释器以模块方式调用
    return [sys.executable, "-m", "reshot"]


RESHOT = resolve_reshot_cmd()

VIDEO_EXT = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v")

# 下游视频模型的输出规格预设（reshot --target）
TARGETS = {
    "Seedance 2.0/2.5（默认）": "seedance",
    "MiniMax H3": "h3",
    "Wan VACE": "wan",
}

BG = "#1e1e1e"
FG = "#e8e8e8"
ACCENT = "#4a9eff"
OK = "#4caf50"
ERR = "#f44336"
SUB = "#9e9e9e"


class App:
    def __init__(self, root):
        self.root = root
        self.queue = queue.Queue()
        self.proc = None
        self.running = False

        root.title("视频深度图工具")
        root.geometry("640x500")
        root.configure(bg=BG)
        root.resizable(False, False)
        self._center()

        tk.Label(root, text="视频深度图工具", font=("Microsoft YaHei UI", 20, "bold"),
                 bg=BG, fg=FG).pack(pady=(20, 4))
        tk.Label(root, text="把视频拖进来，自动生成黑白深度视频", font=("Microsoft YaHei UI", 10),
                 bg=BG, fg=SUB).pack()

        # 输出规格
        row = tk.Frame(root, bg=BG)
        row.pack(fill="x", padx=44, pady=(12, 0))
        tk.Label(row, text="输出规格：", font=("Microsoft YaHei UI", 10), bg=BG, fg=SUB).pack(side="left")
        self.target_var = tk.StringVar(value=list(TARGETS.keys())[0])
        combo = ttk.Combobox(row, textvariable=self.target_var, values=list(TARGETS.keys()),
                             state="readonly", width=26)
        combo.pack(side="left")

        # 拖拽区
        self.drop = tk.Label(root, text="\n\n把视频拖到这里\n\n或点击选择文件\n\n支持 mp4 / mov / avi / mkv\n",
                             font=("Microsoft YaHei UI", 13), bg="#2a2a2a", fg=FG,
                             relief="solid", bd=2, justify="center", cursor="hand2")
        self.drop.pack(fill="both", expand=True, padx=40, pady=16)
        self.drop.bind("<Button-1>", lambda e: self.choose_file())
        if HAS_DND:
            try:
                self.drop.drop_target_register(DND_FILES)
                self.drop.dnd_bind("<<Drop>>", self.on_drop)
            except Exception:
                pass

        # 状态栏
        self.status = tk.Label(root, text="就绪 —— 等待视频", font=("Microsoft YaHei UI", 10),
                               bg=BG, fg=SUB, anchor="w")
        self.status.pack(fill="x", padx=44)

        # 进度条
        self.bar = tk.Canvas(root, height=8, bg="#2a2a2a", highlightthickness=0)
        self.bar.pack(fill="x", padx=40, pady=(6, 14))
        self.bar_fill = self.bar.create_rectangle(0, 0, 0, 8, fill=ACCENT, width=0)

        # 底部
        bar2 = tk.Frame(root, bg=BG)
        bar2.pack(fill="x", padx=40, pady=(0, 16))
        tk.Button(bar2, text="打开输出文件夹", command=self.open_out,
                  font=("Microsoft YaHei UI", 10), bg="#333333", fg=FG,
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  activebackground="#444444", activeforeground=FG).pack(side="left")
        tk.Label(bar2, text="关闭窗口即全部退出", font=("Microsoft YaHei UI", 9),
                 bg=BG, fg=SUB).pack(side="right")

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self.poll)

    def _center(self):
        self.root.update_idletasks()
        w, h = 640, 500
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def set_status(self, text, color=SUB):
        self.status.config(text=text, fg=color)

    def set_progress(self, frac):
        w = self.bar.winfo_width() or 560
        self.bar.coords(self.bar_fill, 0, 0, max(0, int(w * frac)), 8)

    # ------------------------------------------------------------ 交互
    def on_drop(self, event):
        if self.running:
            return
        files = self.root.tk.splitlist(event.data)
        vids = [f for f in files if f.lower().endswith(VIDEO_EXT)]
        if not vids:
            self.set_status("拖入的不是视频文件", ERR)
            return
        self.start(vids)

    def choose_file(self):
        if self.running:
            return
        f = filedialog.askopenfilename(
            title="选择视频",
            filetypes=[("视频文件", " ".join("*" + e for e in VIDEO_EXT)), ("所有文件", "*.*")])
        if f:
            self.start([f])

    def start(self, vids):
        self.running = True
        self.drop.config(bg="#232a33")
        self.set_status(f"开始处理 {len(vids)} 个视频...", ACCENT)
        self.set_progress(0)
        threading.Thread(target=self.work, args=(vids,), daemon=True).start()

    # ------------------------------------------------------------ 处理
    def work(self, vids):
        os.makedirs(OUT_DIR, exist_ok=True)
        target = TARGETS.get(self.target_var.get(), "seedance")
        total = len(vids)
        ok = 0
        for i, v in enumerate(vids):
            name = os.path.splitext(os.path.basename(v))[0]
            out = os.path.join(OUT_DIR, f"{name}_depth.mp4")
            self.queue.put(("status", (f"[{i+1}/{total}] 处理中：{os.path.basename(v)}", ACCENT)))
            cmd = RESHOT + [v, "-o", out, "--control", "depth", "--target", target]
            try:
                self.proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                for line in self.proc.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    if "%|" in line:
                        try:
                            pct = float(line.split("%|")[0].strip().split()[-1]) / 100.0
                            self.queue.put(("progress", ((i + pct) / total,)))
                        except Exception:
                            pass
                self.proc.wait()
                if self.proc.returncode == 0 and os.path.exists(out):
                    ok += 1
                else:
                    self.queue.put(("status", (f"[{i+1}/{total}] 失败：{os.path.basename(v)}", ERR)))
            except Exception as e:
                self.queue.put(("status", (f"错误：{e}", ERR)))
            finally:
                self.proc = None
            self.queue.put(("progress", ((i + 1) / total,)))

        if ok:
            self.queue.put(("status", (f"完成！{ok}/{total} 个视频已生成深度图", OK)))
            self.queue.put(("open",))
        else:
            self.queue.put(("status", ("处理失败，请检查视频格式与依赖是否装好", ERR)))
        self.queue.put(("done",))

    def poll(self):
        try:
            while True:
                item = self.queue.get_nowait()
                kind, val = (item + (None,))[:2] if isinstance(item, tuple) else (item, None)
                if kind == "status":
                    self.set_status(*val) if isinstance(val, tuple) else self.set_status(val)
                elif kind == "progress":
                    self.set_progress(val[0])
                elif kind == "open":
                    self.open_out()
                elif kind == "done":
                    self.running = False
                    self.drop.config(bg="#2a2a2a")
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def open_out(self):
        os.makedirs(OUT_DIR, exist_ok=True)
        if os.name == "nt":
            os.startfile(OUT_DIR)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", OUT_DIR])
        else:
            subprocess.Popen(["xdg-open", OUT_DIR])

    def on_close(self):
        # 关闭窗口时杀掉所有子进程，避免残留后台计算
        if self.proc and self.proc.poll() is None:
            try:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.proc.pid)],
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    self.proc.kill()
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        self.root.destroy()
        os._exit(0)


def main():
    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
