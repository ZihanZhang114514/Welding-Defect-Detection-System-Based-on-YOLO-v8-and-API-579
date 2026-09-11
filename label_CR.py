import os
import cv2
from ultralytics import YOLO
from CrApiAssisment import CrApiAssisment
from tkinter import messagebox
from CrFrameAndReport import CRFrameAndReport

import i18n

# ===================== 配置项 =====================
# 你训练好的模型路径（.pt 文件，相对工程目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "cr_best.pt")  # CR缺陷

# 置信度阈值（低于这个不显示）
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.6  # IOU 阈值

# 实例化评定类，并弹出GUI等待用户输入（GUI内部会把参数写入实例属性）
api_ass = CrApiAssisment()
api_ass.gui()

# GUI结束后校验用户输入
if not api_ass.folder_path:
    messagebox.showerror(i18n.t("error_title"), i18n.t("error_no_image_folder"))
    exit(1)
if not (api_ass.original_width and api_ass.original_height):
    messagebox.showerror(i18n.t("error_title"), i18n.t("error_no_wh"))
    exit(1)

# 定义输出文件夹（移到用户操作后）
OUTPUT_FOLDER = os.path.join(api_ass.folder_path, "output")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 加载模型
model = YOLO(MODEL_PATH)

# 支持的图片后缀
IMG_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")


def start_messagebox():
    messagebox.showinfo(i18n.t("info_title"), i18n.t("info_start_cr"))


def run():
    imgpaths_and_informations_list = []  # 创建大列表，存储小列表
    # 遍历文件夹
    for filename in os.listdir(api_ass.folder_path):
        if filename.lower().endswith(IMG_EXTENSIONS):
            img_path = os.path.join(api_ass.folder_path, filename)
            print(f"正在检测: {img_path}")

            # 推理
            results = model(img_path, conf=CONF_THRESHOLD, iou=IOU_THRESHOLD)

            # 读取原图，获取图像尺寸（供坐标比例换算使用）
            img = cv2.imread(img_path)
            if img is None:
                print(f"警告：无法读取图片，已跳过: {img_path}")
                continue
            # 创建列表存储图像尺寸 [宽, 高]（像素），提前初始化避免无检测框时未定义
            img_shape_list = [img.shape[1], img.shape[0]]

            single_imgpath_and_information_list = []  # 创建小列表，存储
            single_imgpath_and_information_list.append(img_path)
            single_img_points_list = []  # 记录单张图片中所有缺陷坐标的列表
            single_img_wahs_list = []  # 记录单张图片中所有缺陷长宽的列表

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # 坐标
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    single_img_points_list.append([x1, y1, x2, y2])

                    # 计算实际宽高
                    width = x2 - x1
                    height = y2 - y1
                    ratio_of_width = width / img.shape[1]
                    ratio_of_height = height / img.shape[0]
                    actual_width = ratio_of_width * api_ass.original_width
                    actual_height = ratio_of_height * api_ass.original_height
                    single_img_wahs_list.append([actual_width, actual_height])

            single_imgpath_and_information_list.append(single_img_points_list)
            single_imgpath_and_information_list.append(single_img_wahs_list)
            single_imgpath_and_information_list.append(img_shape_list)
            imgpaths_and_informations_list.append(single_imgpath_and_information_list)  # 存入大列表

    # 将检测结果交给 API 579 评定类处理
    api_ass.depark(imgpaths_and_informations_list)

    # 读取并解析 PI 579 评定结果
    api_ass_result_list = api_ass.api_ass_result_list

    # 调用 CRFrameAndReport 类生成最终的带框报告
    far = CRFrameAndReport(api_ass_result_list, api_ass.folder_path)
    far.run()

    # 检测完成提示
    print(f"\n检测完成！所有结果已保存到: {OUTPUT_FOLDER}")
    os.startfile(OUTPUT_FOLDER)
    messagebox.showinfo(i18n.t("info_title"), i18n.t("done_msg", folder=OUTPUT_FOLDER))


if __name__ == "__main__":
    start_messagebox()
    run()
