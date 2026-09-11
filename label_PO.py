import os
import time

import cv2
from ultralytics import YOLO
import input_dialog
from tkinter import messagebox
from threading import Thread

import i18n

from docx import Document
#from docx.enum.text import WD_PARAGRAPH_ALIGNMENT



# ===================== Configs =====================
# 你训练好的模型路径（.pt 文件，相对工程目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "po_best.pt")

# 置信度阈值（低于这个不显示）
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.6  # IOU 阈值

# 先调用GUI并等待用户完成操作（选择文件夹、输入宽高）
type="PO"
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
# API579 官方固定判据
single_max = min(0.4 * float(input_dialog.wall_thickness), 5.0)  # 单个气孔最大允许
sum_limit_25 = 10.0  # 25mm内气孔总和上限

#记录程序开始运行时的时间
starttime = time.time()

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

image_num = 0


def start_messagebox():
    messagebox.showinfo(i18n.t("info_title"), i18n.t("info_start_po"))


def run():
    global image_num

    #定义列表存储文件信息字典
    data_dic_list=list()

    # 遍历文件夹
    for filename in os.listdir(input_dialog.folder_path):

        #定义字典存储文件信息
        data_dic={"filename":os.path.splitext(os.path.split(filename)[1])[0],"size":list(),"api":list()}

        if filename.lower().endswith(IMG_EXTENSIONS):
            img_path = os.path.join(input_dialog.folder_path, filename)#图片路径
            print(f"正在检测: {img_path}")

            # 推理
            results = model(img_path, conf=CONF_THRESHOLD, iou=IOU_THRESHOLD)

            # 读取原图并画框
            img = cv2.imread(img_path)
            hole_list = []  # 移到外层，避免每次循环重置
            for result in results:
                boxes = result.boxes

                count=0#循环计数变量
                for box in boxes:
                    # 坐标
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    # 置信度
                    conf = box.conf[0].item()
                    # 类别ID
                    cls_id = int(box.cls[0].item())
                    # 类别名称
                    cls_name = model.names[cls_id]

                    #切出元素并保存
                    crop_out_a_single_element(img_path, y1, y2, x1, x2, count)

                    # 画框
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # 标注文字
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

                    #缺陷实际尺寸加入信息字典
                    data_dic["size"].append([actual_width, actual_height])

                    #标注长宽并保存
                    img_wh=img
                    actual_width_4=format(actual_width,".4f")
                    actual_height_4=format(actual_height,".4f")
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

                    # 将要给API 579去判断的数据
                    # 修复：避免除以0（如果actual_width为0）
                    if actual_width == 0:
                        pixel_25mm = 0
                    else:
                        pixel_25mm = img.shape[1] * (25 / actual_width)  # 计算25mm所占的像素
                    x = (x1 + x2) / 2
                    diameter = max(actual_width, actual_height)
                    hole_list.append([x, diameter])  # 加入列表
                    count+=1#记录循环次数
            image_num += 1

            # ======================  滑动窗口25mm 遍历统计 ======================
            # 修复：将浮点数转为整数（关键）
            window_pixel = int(pixel_25mm) if pixel_25mm > 0 else 0  # 窗口像素 = 25mm
            step = int(window_pixel / 5) if window_pixel >= 5 else 1  # 滑动步长，防止漏判（避免步长为0）

            max_sum = 0.0
            all_single_pass = True

            # 先校验所有单个气孔是否超标
            for _, size_mm in hole_list:
                if size_mm > single_max:
                    all_single_pass = False

            # 滑动窗口扫描
            img_w = img.shape[1]
            # 修复：确保range参数都是整数，且结束值≥起始值
            end_x = max(0, img_w - window_pixel)
            for start_x in range(0, end_x, step):
                current_sum = 0.0
                for x_pos, size_mm in hole_list:
                    # 判断气孔是否在当前25mm窗口内
                    if start_x <= x_pos <= start_x + window_pixel:
                        current_sum += size_mm
                if current_sum > max_sum:
                    max_sum = current_sum

            # ====================== API 579最终判定 =====================
            # 修复逻辑：原逻辑判断反了，all_single_pass是“所有单个都通过”，max_sum≤sum_limit_25才是通过
            pass_api = all_single_pass and (max_sum <= sum_limit_25)
            # 重新遍历boxes画判定框（原代码只画最后一个box的问题）
            for result in results:
                boxes = result.boxes
                count=0
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    if not pass_api:
                        #API判定信息存入信息字典
                        data_dic["api"].append(False)

                        # 未通过：画红框+标字
                        rectangle_single_element_api(img_path, y1, y2, x1, x2, count, False)#生成只带单个框的图片

                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        label_API = f"failed"
                        cv2.putText(img, label_API, (x1, y2 + 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                    (0, 0, 255), 2)
                    else:
                        #API判定信息存入信息字典
                        data_dic["api"].append(True)

                        # 通过：画绿框+标字（保留原检测框，叠加判定文字）
                        rectangle_single_element_api(img_path, y1, y2, x1, x2, count, True)  # 生成只带单个框的图片
                        label_API = f"passed"
                        cv2.putText(img, label_API, (x1, y2 + 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                    (0, 255, 0), 2)
                    count+=1
            #字典存入列表
            data_dic_list.append(data_dic)

            # 保存结果
            save_path = os.path.join(OUTPUT_FOLDER, filename)
            cv2.imwrite(save_path, img)

    generate_docx(data_dic_list)

    for data in data_dic_list:
        #with(open(os.path.join(OUTPUT_FOLDER, "报告.txt"), "w")) as f:
            #f.write(data)
        print(data)


    # 检测完成提示
    print(f"\n检测完成！所有结果已保存到: {OUTPUT_FOLDER}")
    end_time = time.time()
    run_time=format(end_time-starttime)
    single_run_time = (float(run_time) * 1000.0) / image_num
    os.startfile(OUTPUT_FOLDER)  # 打开输出文件夹
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
    path=os.path.join(input_dialog.folder_path,"inspection_report.docx")
    doc=Document()#创建文档
    doc.add_heading('未焊透缺陷检测报告', level=1)
    for data in data_dic_list:
        doc.add_paragraph(f"文件名：{data.get('filename')}")
        #写入缺陷尺寸
        doc.add_paragraph(f"缺陷类型：")
        count=0
        for size in data.get('size'):
            doc.add_paragraph(f"缺陷{count+1}:")
            format_width="{:.4f}".format(size[0])
            format_height="{:.4f}".format(size[1])
            doc.add_paragraph(f"    长:{format_width}mm,宽:{format_height}mm")
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


# 修复线程创建方式（先创建Thread对象，再调用start）
thread_run = Thread(target=run)
# 修复：start_messagebox不要加()，否则直接执行而不是线程执行
thread_sm = Thread(target=start_messagebox)

# 启动线程
thread_run.start()
thread_sm.start()

# 等待线程结束
thread_run.join()
thread_sm.join()