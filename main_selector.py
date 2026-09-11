import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

import i18n

# 以本脚本所在目录为基准，确保在任何工作目录下都能正确启动子脚本
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _launch(script_name, lang):
    """使用当前解释器启动同目录下的子脚本，并把语言通过环境变量传给子进程。

    使用 subprocess.Popen 的参数列表形式（不经过 shell），
    避免中文/空格路径在 cmd 引号解析时被破坏。
    """
    os.environ["APP_LANG"] = lang
    subprocess.Popen([sys.executable, os.path.join(BASE_DIR, script_name)], cwd=BASE_DIR)


def current_lang():
    return "en" if "Eng" in lang_var.get() else "zh"


def refresh_language(event=None):
    i18n.set_language(current_lang())
    window.title(i18n.t("app_title"))
    lang_label.config(text=i18n.t("language_label"))
    label.config(text=i18n.t("select_defect_type"))
    PO_button.config(text=i18n.t("defect_po"))
    LP_button.config(text=i18n.t("defect_lp"))
    CR_button.config(text=i18n.t("defect_cr"))


def po():
    window.destroy()
    _launch("label_PO.py", current_lang())


def lp():
    window.destroy()
    _launch("label_LP.py", current_lang())


def cr():
    window.destroy()
    _launch("label_CR.py", current_lang())


window = tk.Tk()
window.title(i18n.t("app_title"))
#---------------------------------
width = 480
heigh = 420
screenwidth = window.winfo_screenwidth()
screenheight = window.winfo_screenheight()
window.geometry('%dx%d+%d+%d' % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 2))
window.resizable(False, False)

# 顶部语言切换栏
top_frame = tk.Frame(window)
top_frame.pack(fill="x", padx=12, pady=8)

lang_label = tk.Label(top_frame, text=i18n.t("language_label"), font=("Arial", 10))
lang_label.pack(side="left")

lang_var = tk.StringVar(
    value=i18n.LANGUAGE_OPTIONS[1] if i18n.get_language() == "en" else i18n.LANGUAGE_OPTIONS[0])
lang_combo = ttk.Combobox(top_frame, textvariable=lang_var, state="readonly",
                          values=i18n.LANGUAGE_OPTIONS, width=10)
lang_combo.pack(side="right")
lang_combo.bind("<<ComboboxSelected>>", refresh_language)

label = tk.Label(window, text=i18n.t("select_defect_type"), font=("Arial", 20, "bold"))
label.pack(pady=(10, 5))

PO_button = tk.Button(window, text=i18n.t("defect_po"), font=("Arial", 15),
                      width=18, height=2, command=po)
PO_button.pack(pady=4)

LP_button = tk.Button(window, text=i18n.t("defect_lp"), font=("Arial", 15),
                      width=18, height=2, command=lp)
LP_button.pack(pady=4)

CR_button = tk.Button(window, text=i18n.t("defect_cr"), font=("Arial", 15),
                      width=18, height=2, command=cr)
CR_button.pack(pady=4)

window.mainloop()