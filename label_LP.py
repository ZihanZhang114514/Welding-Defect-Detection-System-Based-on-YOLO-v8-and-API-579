# -*- coding: utf-8 -*-
import os
import cv2
from ultralytics import YOLO
import input_dialog
from tkinter import messagebox
from threading import Thread
import time
from docx import Document

import i18n

# ===================== Configs =====================
# 你训练好的模型路径（.pt 文件，相对工程目录，需是检测未焊透的模型）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "lp_best.pt")

# 置信度阈值（低于这个不显示）
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.6  # IOU 阈值

# 先调用GUI并等待用户完成操作（选择文件夹、输入宽高）
type="LP"
input_dialog.create_gui(type)

# 确认用户完成输入后再定义输出路径（关键修复点）
if input_dialog.folder_path is None:
    messagebox.showerror(i18n.t("error_title"), i18n.t("error_no_image_folder"))
    exit(1)
if input_dialog.original_width is None or input_dialog.original_height is None:
    messagebox.showerror(i18n.t("error_title"), i18n.t("error_no_wh"))
    exit(1)
if input_dialog.wall_thickness is None:
    messagebox.showerror(i18n.t("error_title"), i18n.t("error_no_thickness"))
    exit(1)

#记录程序开始运行时的时间
starttime = time.time()

# ===================== API 579 未焊透（Incomplete Penetration）判据 =====================
# 未焊透关键判据（参考API 579-1/ASME FFS-1标准）
wall_thickness = float(input_dialog.wall_thickness)  # 容器壁厚(mm)
# 1. 单个未焊透最大允许深度（占壁厚百分比，API 579典型值）
max_ip_depth_ratio = 0.2  # 未焊透深度≤壁厚的20%
max_ip_depth = wall_thickness * max_ip_depth_ratio  # 最大允许深度(mm)
# 2. 未焊透长度判据：单段最大允许长度(mm)
max_ip_length_single = 25.0  # 单段未焊透≤25mm（API 579典型阈值）
# 3. 累计长度判据：任意300mm范围内累计长度≤50mm
cumulative_window_mm = 300.0  # 统计窗口300mm
max_ip_length_cumulative = 50.0  # 300mm内累计≤50mm

# 定义输出文件夹（移到用户操作后）
OUTPUT_FOLDER = os.path.join(input_dialog.folder_path, "output")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 定义输出文件夹（移到用户操作后）
OUTPUT_FOLDER = os.path.join(input_dialog.folder_path, "output")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

#定义长宽标注文件夹
WIDTH_AND_HEIGHT_FOLDER = os.path.join(OUTPUT_FOLDER,"width_and_height")
os.makedirs(WIDTH_AND_HEIGHT_FOLDER, exist_ok=True)

#定义API结果文件夹
API_FOLDER = os.path.join(OUTPUT_FOLDER,"API")
os.makedirs(API_FOLDER, exist_ok=True)

# 加载模型
model = YOLO(MODEL_PATH)

# 支持的图片后缀
IMG_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")

image_num=0  #定义存储图像个数的int

def start_messagebox():
    messagebox.showinfo(i18n.t("info_title"), i18n.t("info_start_lp"))


def run():
    global image_num

    data_dic_list = []

    # 遍历文件夹
    for filename in os.listdir(input_dialog.folder_path):

        #定义字典存储文件信息
        data_dic={"filename":os.path.splitext(os.path.split(filename)[1])[0],"size":[],"api":[]}

        if filename.lower().endswith(IMG_EXTENSIONS):
            img_path = os.path.join(input_dialog.folder_path, filename)
            print(f"正在检测: {img_path}")

            # 推理
            results = model(img_path, conf=CONF_THRESHOLD, iou=IOU_THRESHOLD)

            # 读取原图并画框
            img = cv2.imread(img_path)
            ip_defects = []  # 存储未焊透缺陷参数: [中心x像素, 深度(mm), 长度(mm), 框坐标(x1,y1,x2,y2)]

            for result in results:
                boxes = result.boxes

                count = 0
                for box in boxes:
                    # 坐标
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    # 置信度
                    conf = box.conf[0].item()
                    # 类别ID
                    cls_id = int(box.cls[0].item())
                    # 类别名称（需确保模型类别包含"IncompletePenetration"/"未焊透"）
                    cls_name = model.names[cls_id]

                    #切出元素并保存
                    crop_out_a_single_element(img_path, y1, y2, x1, x2, count)

                    # 画检测框（初始绿框）
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    # 标注检测信息
                    label = f"{cls_name} {conf:.2f}"
                    cv2.putText(img, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                (0, 255, 0), 2)

                    # 计算实际宽高
                    width = x2 - x1
                    height = y2 - y1
                    ratio_of_width = width / img.shape[1]
                    ratio_of_height = height / img.shape[0]
                    actual_width = ratio_of_width * float(input_dialog.original_width)
                    actual_height = ratio_of_height * float(input_dialog.original_height)



                    #=================处理长宽区，可保证程序同时输出API检测结果与实际长宽=========================
                    #标注长宽并保存
                    img_wh=img
                    actual_width_4=format(actual_width,".4f")
                    actual_height_4=format(actual_height,".4f")

                    #缺陷实际尺寸加入信息字典
                    data_dic["size"].append([actual_width_4, actual_height_4])

                    w=f"Width:{actual_width_4}mm"
                    cv2.putText(img, w, (x1, y2 + 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                (0, 255, 0), 2)
                    h = f"Height:{actual_height_4}mm"
                    cv2.putText(img,h, (x1, y2 + 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                (0, 255, 0), 2)
                    save_path_wh=os.path.join(WIDTH_AND_HEIGHT_FOLDER, filename)
                    cv2.imwrite(save_path_wh, img_wh)

                    #标注单个长宽
                    rectangle_single_element_width_and_height(img_path, y1, y2, x1, x2, count,w,h)


                    # ===================== 计算未焊透实际尺寸（核心）=====================
                    # 像素尺寸转实际尺寸（基于用户输入的原图宽高）
                    img_h, img_w = img.shape[:2]
                    ratio_w = float(input_dialog.original_width) / img_w  # 像素→实际宽度的比例
                    ratio_h = float(input_dialog.original_height) / img_h  # 像素→实际高度的比例



                    # 未焊透：深度（沿壁厚方向）、长度（沿焊缝方向）
                    # 需根据你的图像标注规则调整（示例：框高度=深度，框宽度=长度）
                    ip_depth_px = y2 - y1  # 像素深度
                    ip_length_px = x2 - x1  # 像素长度
                    ip_depth_mm = ip_depth_px * ratio_h  # 实际深度(mm)
                    ip_length_mm = ip_length_px * ratio_w  # 实际长度(mm)
                    ip_center_x_px = (x1 + x2) / 2  # 缺陷中心x像素坐标（用于滑动窗口）

                    # 存储未焊透缺陷信息
                    ip_defects.append([
                        ip_center_x_px, ip_depth_mm, ip_length_mm,
                        x1, y1, x2, y2
                    ])

                    count+=1
            image_num+=1

            # ===================== API 579 未焊透判定逻辑 =====================
            pass_api = True  # 初始判定为通过
            fail_reasons = []  # 记录失败原因

            # 1. 单个未焊透深度判定
            for _, depth, length, x1, y1, x2, y2 in ip_defects:
                if depth > max_ip_depth:
                    pass_api = False
                    fail_reasons.append(f"未焊透深度超标: {depth:.2f}mm > 允许{max_ip_depth:.2f}mm")

            # 2. 单个未焊透长度判定
            for _, depth, length, x1, y1, x2, y2 in ip_defects:
                if length > max_ip_length_single:
                    pass_api = False
                    fail_reasons.append(f"未焊透单段长度超标: {length:.2f}mm > 允许{max_ip_length_single:.2f}mm")

            # 3. 300mm窗口内累计长度判定（滑动窗口）
            if ip_defects:
                # 计算300mm对应的像素宽度
                pixel_per_mm = img_w / float(input_dialog.original_width)  # 1mm对应像素数
                window_300mm_px = int(cumulative_window_mm * pixel_per_mm)  # 300mm窗口像素宽度
                step_px = max(1, int(window_300mm_px / 10))  # 滑动步长（避免漏检）

                max_cumulative_length = 0.0  # 最大累计长度
                img_width_px = img.shape[1]
                end_x = max(0, img_width_px - window_300mm_px)

                # 滑动窗口遍历
                for start_x in range(0, end_x + 1, step_px):
                    end_window_x = start_x + window_300mm_px
                    current_cumulative = 0.0

                    # 统计当前窗口内的未焊透长度总和
                    for center_x, _, length, _, _, _, _ in ip_defects:
                        if start_x <= center_x <= end_window_x:
                            current_cumulative += length

                    if current_cumulative > max_cumulative_length:
                        max_cumulative_length = current_cumulative

                # 判定累计长度是否超标
                if max_cumulative_length > max_ip_length_cumulative:
                    pass_api = False
                    fail_reasons.append(
                        f"300mm内累计长度超标: {max_cumulative_length:.2f}mm > 允许{max_ip_length_cumulative:.2f}mm")

            # ===================== 标注判定结果（红/绿框+文字）=====================
            for _, _, _, x1, y1, x2, y2 in ip_defects:
                if not pass_api:
                    # 未通过：红框+failed标注
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    label_api = "failed"

                    rectangle_single_element_api(img_path, y1, y2, x1, x2, count, False)  # 生成只带单个框的图片

                    # API判定信息存入信息字典
                    data_dic["api"].append(False)

                    cv2.putText(img, label_api, (x1, y2 + 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                (0, 0, 255), 2)
                else:
                    # 通过：绿框+passed标注
                    label_api = "passed"

                    rectangle_single_element_api(img_path, y1, y2, x1, x2, count, True)  # 生成只带单个框的图片

                    # API判定信息存入信息字典
                    data_dic["api"].append(True)

                    cv2.putText(img, label_api, (x1, y2 + 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                (0, 255, 0), 2)

                # 字典存入列表
            data_dic_list.append(data_dic)

            # ===================== 保存结果 =====================
            save_path = os.path.join(OUTPUT_FOLDER, filename)
            cv2.imwrite(save_path, img)
            # 打印判定结果
            if fail_reasons:
                print(f"文件{filename}判定失败：{'; '.join(fail_reasons)}")
            else:
                print(f"文件{filename}判定通过")

    # 检测完成提示
    print(f"\n检测完成！所有结果已保存到: {OUTPUT_FOLDER}")
    endtime=time.time()
    run_time = format(endtime - starttime)
    if image_num==0:
        messagebox.showerror(i18n.t("error_title"), i18n.t("error_no_images"))
    single_run_time=(float(run_time)*1000.0) / image_num
    os.startfile(OUTPUT_FOLDER)  # 打开输出文件夹
    generate_docx(data_dic_list)
    messagebox.showinfo(i18n.t("info_title"),
                        i18n.t("done_msg", folder=OUTPUT_FOLDER) + "\n" +
                        i18n.t("done_stat", run_time=run_time, image_num=image_num,
                               single_run_time=single_run_time))


def crop_out_a_single_element(img_path, y1, y2, x1, x2, count):
    name = os.path.splitext(os.path.split(img_path)[1])[0]#获取文件名
    crop_single_elements_folder = os.path.join(OUTPUT_FOLDER,"cropped_single_elements", name)
    os.makedirs(crop_single_elements_folder, exist_ok=True)
    img = cv2.imread(img_path)
    crop_img=img[y1-6:y2+6, x1-6:x2+6]
    cv2.imwrite(os.path.join(crop_single_elements_folder, f"{count}.png"), crop_img)

def rectangle_single_element_api(img_path, y1, y2, x1, x2, count, if_api_passed):
    name = os.path.splitext(os.path.split(img_path)[1])[0]#获取文件名
    rectangle_single_elements_by_API_folder = os.path.join(OUTPUT_FOLDER,"api_single_element_box", name)
    os.makedirs(rectangle_single_elements_by_API_folder, exist_ok=True)
    img = cv2.imread(img_path)

    if if_api_passed is True:
        #画绿色框
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        #标注通过文本
        label_API = f"passed"
        cv2.putText(img, label_API, (x1, y2 + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 255, 0), 2)

    elif if_api_passed is False:
        # 画红色框
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

        # 标注未通过文本
        label_API = f"failed"
        cv2.putText(img, label_API, (x1, y2 + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 0, 255), 2)

    else:
        messagebox.showerror(i18n.t("error_title"), i18n.t("error_draw_api_box"))
    cv2.imwrite(os.path.join(rectangle_single_elements_by_API_folder,f"{count}.png"), img)

def rectangle_single_element_width_and_height(img_path, y1, y2, x1, x2, count,w,h):#画框并标长宽
    name = os.path.splitext(os.path.split(img_path)[1])[0]#获取文件名
    rectangle_single_element_width_and_height_folder = os.path.join(OUTPUT_FOLDER,"single_element_width_and_height", name)
    os.makedirs(rectangle_single_element_width_and_height_folder, exist_ok=True)

    img = cv2.imread(img_path)
    # 画框
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # 标注长宽并保存
    cv2.putText(img, w, (x1, y2 + 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0, 255, 0), 2)

    cv2.putText(img, h, (x1, y2 + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0, 255, 0), 2)

    cv2.imwrite(os.path.join(rectangle_single_element_width_and_height_folder,f"{count}.png"), img)

def generate_docx(data_dic_list):
    print(data_dic_list)
    print(OUTPUT_FOLDER)
    path=os.path.join(OUTPUT_FOLDER,"inspection_report.docx")
    doc=Document()#创建文档
    doc.add_heading('气泡缺陷检测报告', level=1)
    for data in data_dic_list:
        doc.add_paragraph(f"文件名：{data.get('filename')}")
        #写入缺陷尺寸
        doc.add_paragraph(f"缺陷类型：")
        count=0
        for size in data.get('size'):
            if size is None:
                continue
            doc.add_paragraph(f"缺陷{count+1}:")

            doc.add_paragraph(f"    长:{size[0]}mm,宽:{size[1]}mm")
            doc.add_paragraph(f"    是否通过API 579评定:{data.get('api')[count]}")
            count+=1
            """
            #以下是图片插入代码，但一直插不进去，先搁置
            img_path=os.path.join(input_dialog.folder_path,data.get('filename')+".png")#!!!这里不是png会报错，有空就改
            print(img_path)
            doc.add_picture(img_path,width=4,height=4)
            """
        doc.add_page_break()  # 添加分页符
    doc.save(path)

# 线程执行
thread_run = Thread(target=run)
thread_sm = Thread(target=start_messagebox)

# 启动线程
thread_run.start()
thread_sm.start()

# 等待线程结束
thread_run.join()
thread_sm.join()