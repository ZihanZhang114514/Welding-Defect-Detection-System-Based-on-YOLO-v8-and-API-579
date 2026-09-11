# 注：本类只实现了单个裂纹的识别，画框，报告生成以及多裂纹等效裂纹暂未完成，不过以及预留接口

import csv
import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import json
import math

import i18n


# 以本脚本所在目录为基准，定位配置与数据目录，保证在任意工作目录下都能正确读取
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config_and_data")
MATERIAL_CONFIG_JSON = os.path.join(CONFIG_DIR, "abcd_curves_material_config.json")


class CrApiAssisment:
    def __init__(self):
        #---由GUI得到---
        self.ref_temp = 0.0
        self.folder_path=""
        self.original_width=0.0
        self.original_height=0.0
        self.wall_thickness=0.0
        self.mys=0 #最小屈服强度（MPa）
        self.material_curve_type= "" #温度豁免曲线类型（A,B,C,D）.
        self.one_t_material_type="" #1-t评定所需要的材料类型
        self.mys_material="" #确定MYS对比表格的钢材类型
        self.working_temp=0.0 #工作温度（℃）
        self.api_ass_result_list=[] #存储评定结果的列表，元素为字典，字典包含图片路径及是否通过布尔值

        #---解包json---
        with open(MATERIAL_CONFIG_JSON, "r", encoding="utf-8") as json_file:
            self.json_dic_data = json.load(json_file)
            # JSON 中的路径为相对 config_and_data 目录的文件名，此处拼接成绝对路径
            self.low_alloy_csv_path = os.path.join(
                CONFIG_DIR, self.json_dic_data["mys_and_temp_csv_path"]["low_alloy_steels"])
            self.carbon_steels_csv_path = os.path.join(
                CONFIG_DIR, self.json_dic_data["mys_and_temp_csv_path"]["carbon_steels"])
            self.one_t_json_path = os.path.join(
                CONFIG_DIR, self.json_dic_data["one_t_ass_json_path"])

    def _cfg(self, key):
        """按当前语言取配置值：英文取 key_en，中文（或缺失）取 key。"""
        data = self.json_dic_data
        if i18n.get_language() == "en" and (key + "_en") in data:
            return data[key + "_en"]
        return data[key]



    def gui(self):
        #-----创建窗口-----（画布尺寸 800x600，与 JSON 布局描述文件保持一致）
        window = tk.Tk()
        window.title(i18n.t("app_title"))
        # ---------------------------------
        width = 800
        heigh = 600
        screenwidth = window.winfo_screenwidth()
        screenheight = window.winfo_screenheight()
        window.geometry('%dx%d+%d+%d' % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 2))
        window.resizable(False, False)  # 固定画布尺寸，确保绝对坐标像素级还原

        # 已选图片文件夹路径（在 select_image_folder 与 start 之间共享）
        folder_path = ""

        # JSON ID: title_frame（Frame/Label，绝对坐标 x=40,y=20,w=720,h=55）
        title_frame = tk.Frame(window, bg="black")
        title_frame.place(x=40, y=20, width=720, height=55)
        title_label = tk.Label(
            title_frame, text=i18n.t("cr_title"),
            font=("Arial", 16), fg="white", bg="black"
        )
        title_label.place(relx=0.5, rely=0.5, anchor="center")

        # 语言切换下拉（放在标题栏右侧）
        lang_var = tk.StringVar(
            value=i18n.LANGUAGE_OPTIONS[1] if i18n.get_language() == "en" else i18n.LANGUAGE_OPTIONS[0])
        lang_combo = ttk.Combobox(title_frame, textvariable=lang_var, state="readonly",
                                  values=i18n.LANGUAGE_OPTIONS, width=10)
        lang_combo.place(relx=1.0, rely=0.5, x=-15, anchor="e")

        def current_lang():
            return "en" if "Eng" in lang_var.get() else "zh"

        def select_image_folder():
            # 无需再创建新的tk.Tk()，复用主窗口即可，避免多窗口问题
            nonlocal folder_path
            folder_path = filedialog.askdirectory(title=i18n.t("select_image_folder"))

        # JSON ID: describe_01（TextBox，x=60,y=100,w=150,h=30）——1-t评估材料类型说明
        input_desc_1 = tk.Entry(window)
        input_desc_1.insert(0, self._cfg("description_02"))
        input_desc_1.place(x=60, y=100, width=150, height=30)

        # JSON ID: ComboBox_01（ComboBox，x=60,y=138,w=150,h=30）——1-t评估材料类型
        tk_one_t_material_type = tk.StringVar()
        combo_box_1 = ttk.Combobox(window, textvariable=tk_one_t_material_type, state="readonly")
        combo_box_1["value"] = self._cfg("material_type_for_one_t_flaw_assessment")
        combo_box_1.current(0)
        combo_box_1.place(x=60, y=138, width=150, height=30)

        # JSON ID: describe_02（TextBox，x=60,y=195,w=150,h=30）——温度豁免曲线说明
        input_desc_2 = tk.Entry(window)
        input_desc_2.insert(0, self._cfg("description_01"))
        input_desc_2.place(x=60, y=195, width=150, height=30)

        # JSON ID: ComboBox_02（ComboBox，x=60,y=233,w=150,h=30）——温度豁免曲线
        tk_temp_exemp_curve = tk.StringVar()
        combo_box_2 = ttk.Combobox(window, textvariable=tk_temp_exemp_curve, state="readonly")
        combo_box_2["value"] = self._cfg("temperature_exemption_curves")
        combo_box_2.current(0)
        combo_box_2.place(x=60, y=233, width=150, height=30)

        # 挂一个回调函数，根据钢材类型更新mys输入框的内容
        def update_mys_combox(event):
            selected_material = tk_mys_material.get()
            if "低合金钢" in selected_material or "low alloy" in selected_material.lower():
                combo_box_4["value"] = self.json_dic_data["mys_low_alloy_steels"]
                combo_box_4.current(0)
            elif "碳钢" in selected_material or "carbon" in selected_material.lower():
                combo_box_4["value"] = self.json_dic_data["mys_carbon_steels"]
                combo_box_4.current(0)
            else:
                messagebox.showerror(i18n.t("error_title"), i18n.t("error_json_parse"))
                sys.exit()


        # JSON ID: describe_03（TextBox，x=430,y=100,w=150,h=30）——钢材类型说明
        input_desc_3 = tk.Entry(window)
        input_desc_3.insert(0, self._cfg("description_03"))
        input_desc_3.place(x=430, y=100, width=150, height=30)

        # JSON ID: ComboBox_03（ComboBox，x=430,y=138,w=150,h=30）——钢材类型
        tk_mys_material = tk.StringVar()
        combo_box_3 = ttk.Combobox(window, textvariable=tk_mys_material, state="readonly")
        combo_box_3["value"] = self._cfg("type_of_steel")
        combo_box_3.current(0)
        combo_box_3.bind("<<ComboboxSelected>>", update_mys_combox)
        combo_box_3.place(x=430, y=138, width=150, height=30)

        # JSON ID: describe_04（TextBox，x=430,y=195,w=150,h=30）——最小屈服强度（MYS）输入说明
        input_desc_4 = tk.Entry(window)
        input_desc_4.insert(0, self._cfg("description_04"))
        input_desc_4.place(x=430, y=195, width=150, height=30)

        # JSON ID: ComboBox_04（ComboBox，x=430,y=233,w=150,h=30）——最小屈服强度（MYS）输入
        tk_mys = tk.StringVar()
        combo_box_4 = ttk.Combobox(window, textvariable=tk_mys, state="readonly")
        combo_box_4["value"] = self.json_dic_data["mys_low_alloy_steels"]
        combo_box_4.current(0)
        combo_box_4.place(x=430, y=233, width=150, height=30)



        # JSON ID: settings_panel（Panel/Frame，全局 x=100,y=270,w=600,h=325）
        # 说明：JSON 中子控件的 absolute 坐标为 800x600 主窗口的全局坐标；
        #       此处将子控件放入 settings_panel 后，使用局部坐标 = 全局坐标 - 面板原点(100,270)。
        settings_panel = tk.Frame(window, bd=1, relief="groove")
        settings_panel.place(x=100, y=270, width=600, height=325)

        # JSON ID: btn_select_folder（Button，全局 x=320,y=290 → 面板局部 x=220,y=20）
        btn_select_folder = tk.Button(settings_panel, text=i18n.t("select_image_folder"), command=select_image_folder)
        btn_select_folder.place(x=220, y=20, width=160, height=30)

        # JSON ID: label_width（Label，全局 x=300,y=340 → 局部 x=200,y=70）
        label_width = tk.Label(settings_panel, text=i18n.t("label_width"))
        label_width.place(x=200, y=70, width=200, height=20)

        # JSON ID: input_width（TextBox，全局 x=300,y=365 → 局部 x=200,y=95）
        input_width = tk.Entry(settings_panel)
        input_width.place(x=200, y=95, width=200, height=25)

        # JSON ID: label_height（Label，全局 x=300,y=405 → 局部 x=200,y=135）
        label_height = tk.Label(settings_panel, text=i18n.t("label_height"))
        label_height.place(x=200, y=135, width=200, height=20)

        # JSON ID: input_height（TextBox，全局 x=300,y=430 → 局部 x=200,y=160）
        input_height = tk.Entry(settings_panel)
        input_height.place(x=200, y=160, width=200, height=25)

        # JSON ID: label_thickness（Label，全局 x=300,y=470 → 局部 x=200,y=200）
        label_thickness = tk.Label(settings_panel, text=i18n.t("label_thickness"))
        label_thickness.place(x=200, y=200, width=200, height=20)

        # JSON ID: input_thickness（TextBox，全局 x=300,y=495 → 局部 x=200,y=225）
        input_thickness = tk.Entry(settings_panel)
        input_thickness.place(x=200, y=225, width=200, height=25)

        # 输入工作温度
        input_working_temp_label = tk.Label(settings_panel, text=i18n.t("label_working_temp"))
        input_working_temp_label.place(x=200, y=260, width=200, height=20)
        input_working_temp = tk.Entry(settings_panel)
        input_working_temp.place(x=200, y=285, width=200, height=25)

        def start():
                # 可选：校验文件夹是否选择、宽高是否输入
                if not folder_path:
                    messagebox.showwarning(i18n.t("warn_title"), i18n.t("warn_select_folder"))
                    return
                if not (input_width.get() and input_height.get()):
                    messagebox.showwarning(i18n.t("warn_title"), i18n.t("warn_input_wh"))
                    return
                if not input_thickness.get():
                    messagebox.showwarning(i18n.t("warn_title"), i18n.t("warn_input_thickness"))
                    return
                if not tk_one_t_material_type.get():
                    messagebox.showwarning(i18n.t("warn_title"), i18n.t("warn_select_1t_material"))
                    return
                if not tk_temp_exemp_curve.get():
                    messagebox.showwarning(i18n.t("warn_title"), i18n.t("warn_select_curve"))
                    return
                if not tk_mys_material.get():
                    messagebox.showwarning(i18n.t("warn_title"), i18n.t("warn_steel_type"))
                    return
                if not input_working_temp.get():
                    messagebox.showwarning(i18n.t("warn_title"), i18n.t("warn_working_temp"))
                    return

                try:
                    self.original_width = float(input_width.get())
                    self.original_height = float(input_height.get())
                    self.wall_thickness = float(input_thickness.get() or "0")
                    self.folder_path = folder_path
                    self.one_t_material_type=str(tk_one_t_material_type.get()) #1-t评估材料类型
                    self.material_curve_type=str(tk_temp_exemp_curve.get()) #温度豁免曲线类型
                    self.mys_material=str(tk_mys_material.get())  #用于选择mys与Tref对应表格的钢材类型
                    self.mys=int(tk_mys.get())  #最小屈服压力（MYS），单位MPa
                    self.working_temp=float(input_working_temp.get())  #工作温度（℃）


                except ValueError:
                    messagebox.showwarning(i18n.t("warn_title"), i18n.t("warn_numeric"))
                    return

                window.destroy()  # 关闭GUI窗口
                return







        # JSON ID: btn_start（Button，全局 x=360,y=550 → 面板局部 x=260,y=280）
        btn_start = tk.Button(settings_panel, text=i18n.t("btn_start"), command=start)
        btn_start.place(x=260, y=280, width=80, height=30)

        def refresh_language(event=None):
            i18n.set_language(current_lang())
            window.title(i18n.t("app_title"))
            title_label.config(text=i18n.t("cr_title"))
            input_desc_1.delete(0, "end")
            input_desc_1.insert(0, self._cfg("description_02"))
            input_desc_2.delete(0, "end")
            input_desc_2.insert(0, self._cfg("description_01"))
            input_desc_3.delete(0, "end")
            input_desc_3.insert(0, self._cfg("description_03"))
            input_desc_4.delete(0, "end")
            input_desc_4.insert(0, self._cfg("description_04"))
            combo_box_1["value"] = self._cfg("material_type_for_one_t_flaw_assessment")
            combo_box_1.current(0)
            combo_box_2["value"] = self._cfg("temperature_exemption_curves")
            combo_box_2.current(0)
            combo_box_3["value"] = self._cfg("type_of_steel")
            combo_box_3.current(0)
            update_mys_combox(None)
            btn_select_folder.config(text=i18n.t("select_image_folder"))
            label_width.config(text=i18n.t("label_width"))
            label_height.config(text=i18n.t("label_height"))
            label_thickness.config(text=i18n.t("label_thickness"))
            input_working_temp_label.config(text=i18n.t("label_working_temp"))
            btn_start.config(text=i18n.t("btn_start"))

        lang_combo.bind("<<ComboboxSelected>>", refresh_language)

        window.mainloop()


    #解码存储了参考温度的CSV文件
    def tref_csv_decoding(self):
        #确定钢材类型，选择合适的CSV
        mys_material=self.mys_material
        if "低合金钢" in mys_material or "low alloy" in mys_material.lower():
            csv_file_path=self.low_alloy_csv_path
        elif "碳钢" in mys_material or "carbon" in mys_material.lower():
            csv_file_path=self.carbon_steels_csv_path
        else:
            messagebox.showerror(i18n.t("error_title"), i18n.t("error_json_parse"))
            sys.exit()

        with open(csv_file_path, newline='', encoding="utf-8-sig") as csvfile:
            rowdics_list = []  # 创建列表，存储csv行字典
            mys_list = []
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                mys_list.append(int(row["MYS (MPa)"]))  # 将MYS数据存入列表
                rowdics_list.append(row)

        #从self里取值
        material_curve_type = self.material_curve_type
        mys=self.mys

        count_mys = 0
        mys_row = -1
        # 记录所在行的位置，以便解包
        for mys_in_csv in mys_list:
            if mys == mys_in_csv:
                mys_row = count_mys
                break
            count_mys += 1

        # 修正：MYS 未在参考温度表中找到时，不再静默使用第 0 行，而是报错终止
        if mys_row == -1:
            messagebox.showerror(i18n.t("error_title"), i18n.t("error_mys_not_found", mys=mys))
            sys.exit()

        # 确定参考温度
        ref_temp = 0
        if "A" in material_curve_type:
            ref_temp = int(rowdics_list[mys_row]["A (°C)"])
        elif "B" in material_curve_type:
            ref_temp = int(rowdics_list[mys_row]["B (°C)"])
        elif "C" in material_curve_type:
            ref_temp = int(rowdics_list[mys_row]["C (°C)"])
        elif "D" in material_curve_type:
            ref_temp = int(rowdics_list[mys_row]["D (°C)"])

        elif "a" in material_curve_type:
            ref_temp = int(rowdics_list[mys_row]["A (°C)"])
        elif "b" in material_curve_type:
            ref_temp = int(rowdics_list[mys_row]["B (°C)"])
        elif "c" in material_curve_type:
            ref_temp = int(rowdics_list[mys_row]["C (°C)"])
        elif "d" in material_curve_type:
            ref_temp = int(rowdics_list[mys_row]["D (°C)"])

        self.ref_temp=ref_temp

    def depark(self,imgpaths_and_informations_list):
        self.tref_csv_decoding()  #解码CSV，得到参考温度
        for imgpath_and_information_list in imgpaths_and_informations_list:
            img_path=imgpath_and_information_list[0]  #图片路径
            xyxy_points_list = imgpath_and_information_list[1]  #缺陷坐标列表，多个缺陷则有多个元素
            widths_and_heights_list = imgpath_and_information_list[2]  #缺陷长宽列表，多个缺陷则有多个元素
            img_shapes_list = imgpath_and_information_list[3] #图像尺寸列表
            self.api_ass(img_path,xyxy_points_list,widths_and_heights_list,img_shapes_list)


    def api_ass(self,img_path,xyxy_points_list,widths_and_heights_list,img_shapes_list):
        # 当待测图片中只有一条裂纹时
        if len(xyxy_points_list)==1:
            width=(widths_and_heights_list[0])[0]
            height=(widths_and_heights_list[0])[1]
            length=float(max(width,height))  #确定缺陷长度(2c)
            self._single_api_ass(length,img_path,xyxy_points_list,widths_and_heights_list)  #调用单裂纹评定方法

        # 当待测图片中有多条裂纹时
        # 进行等效裂纹计算，得到等效裂纹的长度和坐标，然后再进行1-t评定
        elif len(xyxy_points_list)>1:
            # 先得到每个裂纹的中心坐标
            center_points_list = [] #存储中心坐标的列表
            for xyxy_point in xyxy_points_list:
                single_center_point=[]
                x_center=float((xyxy_point[0]+xyxy_point[2])/2) #计算x中心坐标
                single_center_point.append(x_center)
                y_center=float((xyxy_point[1]+xyxy_point[3])/2) #计算y中心坐标
                single_center_point.append(y_center)
                center_points_list.append(single_center_point)

            # 定义滑动窗口的首尾指针
            head_pointer=0
            tail_pointer=1
            equvalent_lengths_list=[] #存储等效裂纹长度的列表，若有裂纹未被等效，则存储其原始长度
            equivalent_cracks_points_list=[] #存储等效裂纹坐标的列表
            crack_be_equivalent_list=[] #存储被等效的裂纹索引列表，存储int,方便后续画框和报告生成
            # 计算裂纹之间的距离，判断是否可以等效为一个裂纹
            while True:
                center_point_01_x=center_points_list[head_pointer][0]
                center_point_01_y=center_points_list[head_pointer][1]
                center_point_02_x=center_points_list[tail_pointer][0]
                center_point_02_y=center_points_list[tail_pointer][1]
                x_pixel_distance=abs(center_point_01_x-center_point_02_x)
                y_pixel_distance=abs(center_point_01_y-center_point_02_y)
                ratio_x=x_pixel_distance / img_shapes_list[0]
                ratio_y=y_pixel_distance / img_shapes_list[1]
                actual_distance_x=ratio_x*self.original_width
                actual_distance_y=ratio_y*self.original_height
                actual_distance=math.sqrt(actual_distance_x ** 2 + actual_distance_y ** 2)
                
                # 计算两个裂纹的长度
                length_01=float(max(widths_and_heights_list[head_pointer][0],widths_and_heights_list[head_pointer][1]))
                length_02=float(max(widths_and_heights_list[tail_pointer][0],widths_and_heights_list[tail_pointer][1]))
                if length_01/2.0+length_02/2.0 >= actual_distance: #两个裂纹半长度的和大于其距离，根据API 579-1/ASME FFS-1标准，两个裂纹可以等效为一个裂纹
                    # 计算等效裂纹的长度
                    equivalent_length=length_01/2.0+length_02/2.0+actual_distance
                    print(f"图片路径: {img_path}，裂纹{head_pointer}与裂纹{tail_pointer}等效为一个裂纹，等效长度: {equivalent_length}")
                    equvalent_lengths_list.append(equivalent_length) #存储等效裂纹长度
                    # 计算等效裂纹的坐标
                    x_01_equivalent=(center_point_01_x+center_point_02_x)/2.0
                    y_01_equivalent=(center_point_01_y+center_point_02_y)/2.0
                    # 将等效裂纹的坐标存入列表
                    equivalent_cracks_points_list.append([x_01_equivalent,y_01_equivalent])
                    # 将被等效的裂纹索引存入列表
                    crack_be_equivalent_list.append(head_pointer)
                    crack_be_equivalent_list.append(tail_pointer)
                    # 删除被等效的裂纹的中心坐标
                    del center_points_list[tail_pointer]
                    del center_points_list[head_pointer]
                    # 重置首尾指针
                    head_pointer=0
                    tail_pointer=1
                else:
                    # 如果两个裂纹不能等效，则将尾指针向后移动一位
                    tail_pointer += 1   

                if tail_pointer >= len(center_points_list)-1:  #如果尾指针已经到达最后一个裂纹，则将首指针向后移动一位，尾指针重置为首指针的下一位
                    head_pointer += 1
                    tail_pointer = head_pointer + 1

                if head_pointer >= len(center_points_list)-1:  #如果首指针已经到达最后一个裂纹，则退出循环
                    break    

                for crack_index in range(len(xyxy_points_list)): #center_points_list的长度已经改变，所以不能用center_points_list的长度来循环
                    if crack_index not in crack_be_equivalent_list:
                        # 计算裂纹的长度
                        length=float(max(widths_and_heights_list[crack_index][0],widths_and_heights_list[crack_index][1]))
                        equvalent_lengths_list.append(length) #存储裂纹长度
                        equivalent_cracks_points_list.append(center_points_list[crack_index]) #存储裂纹坐标

            # 对等效裂纹进行1-t评定(复用上面单裂纹的评定方法)   
            for length in equvalent_lengths_list:
                pass #还没想好怎么写，先睡了，或者需要写新的私有方法，或者直接给出全图评定结果

    def _single_api_ass(self,length,img_path,xyxy_points_list,widths_and_heights_list):
        curve_x_axis_var = round(float(self.working_temp - (self.ref_temp + 56.0)))  # 计算曲线的X轴变量值(T - Tref + 56)

        # -----确定1-t曲线类型（A/B/C）-----
        # 解析存储曲线离散化数据的json文件路径
        try:
            with open(self.one_t_json_path, "r", encoding="utf-8") as json_file:
                onet_json_dic_data = json.load(json_file)  # 存储json数据的字典
        except FileNotFoundError:
            messagebox.showerror(i18n.t("error_title"), i18n.t("error_1t_json_missing"))
            sys.exit()
        ass_data_dic = {}  # 存储温度与最大允许长度的对应字典
        one_t_material_type = self.one_t_material_type
        if "A." in one_t_material_type:
            ass_data_dic = onet_json_dic_data["A"]
        elif "B." in one_t_material_type:
            ass_data_dic = onet_json_dic_data["B"]
        elif "C." in one_t_material_type:
            ass_data_dic = onet_json_dic_data["C"]

        # 修正：温度参数(curve_x_axis_var)可能超出曲线表的温度范围，
        # 原 temp.index() 会抛 ValueError 导致崩溃；
        # 改为取最接近的温度点：低于下限自动归为最低温度，高于上限自动归为最高温度。
        temp_list = ass_data_dic["temp"]
        list_index = min(range(len(temp_list)), key=lambda i: abs(temp_list[i] - curve_x_axis_var))
        max_allow_length = float(ass_data_dic["length"][list_index])  # 计算最大允许长度

        # -----比对，给出结果-----
        single_ass_dic = {}
        if length > max_allow_length:
            print(f"图片路径: {img_path}，缺陷长度: {length}，最大允许长度: {max_allow_length}，评定结果: 不合格")
            single_ass_dic["img_path"] = img_path
            single_ass_dic["xyxys_list"] = xyxy_points_list  # xyxy_points_list本就是一个存储了所有缺陷坐标的列表，无需再用一个列表包裹起来
            single_ass_dic["wahs_list"] = widths_and_heights_list  # widths_and_heights_list本就是一个存储了所有缺陷长宽的列表，无需再用一个列表包裹起来
            single_ass_dic["lengths_list"] = [length]  # 考虑到以后可能有多个裂纹，用列表存储长度
            single_ass_dic["max_allow_length"] = max_allow_length  # 一张图片的最大允许长度是一样的，所以不用列表存储
            single_ass_dic["is_pass"] = False
        else:
            print(f"图片路径: {img_path}，缺陷长度: {length}，最大允许长度: {max_allow_length}，评定结果: 合格")
            single_ass_dic["img_path"] = img_path
            single_ass_dic["xyxys_list"] = xyxy_points_list  # xyxy_points_list本就是一个存储了所有缺陷坐标的列表，无需再用一个列表包裹起来
            single_ass_dic["wahs_list"] = widths_and_heights_list  # widths_and_heights_list本就是一个存储了所有缺陷长宽的列表，无需再用一个列表包裹起来
            single_ass_dic["lengths_list"] = [length]  # 考虑到以后可能有多个裂纹，用列表存储长度
            single_ass_dic["max_allow_length"] = max_allow_length
            single_ass_dic["is_pass"] = True
        self.api_ass_result_list.append(single_ass_dic)  # 存入类大列表，之后可以继承别的类来生成报告或画框
                





