import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

import i18n


# 定义全局变量存储检测结果（供其他函数调用）
#detection_result = None
folder_path=None
original_width=None
original_height=None
wall_thickness=None
val = ""


def create_gui(type):

    global folder_path, original_width, original_height,wall_thickness,val
    window = tk.Tk()
    window.title(i18n.t("app_title"))
    # ---------------------------------
    width = 380
    heigh = 340
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

    def current_lang():
        return "en" if "Eng" in lang_var.get() else "zh"

    # ————————————————
    # 版权声明：本文为CSDN博主「右耳朵耗子」的原创文章，遵循CC 4.0 BY-SA版权协议，转载请附上原文出处链接及本声明。
    # 原文链接：https://blog.csdn.net/ZQHCSD/article/details/102907370

    #告诉用户现在在判定哪种缺陷
    if type=="PO":
        val=i18n.t("title_po")
    elif type=="LP":
        val=i18n.t("title_lp")
    else:
        window.destroy()
        messagebox.showerror(i18n.t("error_title"), i18n.t("error_no_caller"))
        return
    label = tk.Label(window, text=val,font=("Arial", 16), fg="white", bg="black")
    label.pack(fill="x")

    def select_image_folder():
        # 无需再创建新的tk.Tk()，复用主窗口即可，避免多窗口问题
        global folder_path
        folder_path = filedialog.askdirectory(title=i18n.t("select_image_folder"))

    # 选择图片文件夹按钮
    button_image_folder = tk.Button(window, text=i18n.t("select_image_folder"), command=select_image_folder)
    button_image_folder.pack(pady=10)

    # 原图像宽度输入
    label_width = tk.Label(window, text=i18n.t("label_width"))
    label_width.pack()
    original_width_entry = tk.Entry(window)
    original_width_entry.pack()

    # 原图像高度输入
    label_height = tk.Label(window, text=i18n.t("label_height"))
    label_height.pack()
    original_height_entry = tk.Entry(window)
    original_height_entry.pack()

    #容器壁厚输入
    label_thick=tk.Label(window,text=i18n.t("label_thickness"))
    label_thick.pack()
    wall_thickness_entry = tk.Entry(window)
    wall_thickness_entry.pack()

    def start():
            global folder_path, original_width, original_height,wall_thickness
            # 可选：校验文件夹是否选择、宽高是否输入
            if not folder_path:
                messagebox.showwarning(i18n.t("warn_title"), i18n.t("warn_select_folder"))
                return
            if not (original_width_entry.get() and original_height_entry.get()):
                messagebox.showwarning(i18n.t("warn_title"), i18n.t("warn_input_wh"))
                return
            if not wall_thickness_entry.get():
                messagebox.showwarning(i18n.t("warn_title"), i18n.t("warn_input_thickness"))
                return
            original_width=original_width_entry.get()
            original_height=original_height_entry.get()
            wall_thickness=wall_thickness_entry.get()

            window.destroy()  # 关闭GUI窗口
            return







    # 开始检测按钮（移除了多余的文件夹选择代码）
    button_start = tk.Button(window, text=i18n.t("btn_start"), command=start)
    button_start.pack(pady=10)

    def refresh_language(event=None):
        i18n.set_language(current_lang())
        window.title(i18n.t("app_title"))
        lang_label.config(text=i18n.t("language_label"))
        label.config(text=i18n.t("title_po") if type == "PO" else i18n.t("title_lp"))
        button_image_folder.config(text=i18n.t("select_image_folder"))
        label_width.config(text=i18n.t("label_width"))
        label_height.config(text=i18n.t("label_height"))
        label_thick.config(text=i18n.t("label_thickness"))
        button_start.config(text=i18n.t("btn_start"))

    lang_combo.bind("<<ComboboxSelected>>", refresh_language)

    window.mainloop()

