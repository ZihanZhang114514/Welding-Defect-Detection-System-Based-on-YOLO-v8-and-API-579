# -*- coding: utf-8 -*-
"""极简中英文国际化模块。

用法：
    import i18n
    i18n.set_language("en")   # 或 "zh"
    text = i18n.t("app_title")

语言状态保存在模块全局，main_selector / input_dialog / CrApiAssisment
以及各 label_* 脚本共享同一个 i18n 模块，因此在一个界面切换语言后，
后续流程（含弹窗提示）都会跟随当前语言。

初始语言可通过环境变量 APP_LANG 传入（main_selector 启动子进程时会设置）。
"""

import os

_LANG = os.environ.get("APP_LANG", "zh")
if _LANG not in ("zh", "en"):
    _LANG = "zh"

# 语言下拉菜单选项（显示名 -> 代码）
LANGUAGE_OPTIONS = ["中文", "English"]


def _lang_code(display_name):
    """把下拉框显示名转换为语言代码。"""
    return "en" if display_name and "Eng" in display_name else "zh"


_TRANSLATIONS = {
    "zh": {
        "app_title": "基于YOLO v8的焊接缺陷自动识别系统",
        "language_label": "语言 / Language",
        "select_defect_type": "请选择缺陷类型",
        "defect_po": "气泡（PO）",
        "defect_lp": "未焊透 (LP)",
        "defect_cr": "裂纹 (CR)",
        "title_po": "气泡（PO）缺陷检测系统",
        "title_lp": "未焊透（LP）缺陷检测系统",
        "cr_title": "裂纹(CR)焊接缺陷评定系统",
        "select_image_folder": "选择图片文件夹",
        "label_width": "请输入原图像宽度(mm):",
        "label_height": "请输入原图像高度(mm):",
        "label_thickness": "请输入容器壁厚",
        "label_working_temp": "请输入工作温度(℃):",
        "btn_start": "开始检测",
        "warn_select_folder": "请先选择图片文件夹！",
        "warn_input_wh": "请输入原图像的宽度和高度！",
        "warn_input_thickness": "请输入容器壁厚！",
        "warn_steel_type": "请输入钢材类型",
        "warn_working_temp": "请输入工作温度",
        "warn_select_1t_material": "请选择1-t评估材料类型",
        "warn_select_curve": "请选择温度豁免曲线类型",
        "warn_numeric": "宽度、高度和壁厚必须是数字！",
        "error_title": "错误",
        "error_no_caller": "未接收到调用者信息",
        "error_json_parse": "JSON配置文件解析出现错误！程序将终止",
        "error_no_image_folder": "未选择图片文件夹！",
        "error_no_wh": "未输入原图像宽高！",
        "error_no_thickness": "未输入容器壁厚",
        "error_no_images": "文件夹中没有待检测图片",
        "error_mys_not_found": "最小屈服强度 MYS={mys} MPa 未在参考温度表中找到！程序将终止",
        "error_1t_json_missing": "找不到存储1-t曲线数据的json，程序终止",
        "error_draw_api_box": "无法绘制单个API结果标注框",
        "info_start_cr": "开始标注缺陷并计算长宽",
        "info_start_po": "开始标注缺陷并根据API 579评判",
        "info_start_lp": "开始标注未焊透缺陷并根据API 579评判",
        "done_msg": "检测完成！所有结果已保存到: {folder}",
        "done_stat": "运行总共用时{run_time}s\n总共处理了{image_num}张图片\n处理每张图片平均耗时{single_run_time}ms",
        "warn_title": "警告",
        "info_title": "提示",
    },
    "en": {
        "app_title": "Welding Defect Auto-Detection System Based on YOLOv8",
        "language_label": "Language / 语言",
        "select_defect_type": "Please select defect type",
        "defect_po": "Porosity (PO)",
        "defect_lp": "Lack of Penetration (LP)",
        "defect_cr": "Crack (CR)",
        "title_po": "Porosity (PO) Defect Detection System",
        "title_lp": "Lack of Penetration (LP) Defect Detection System",
        "cr_title": "Crack (CR) Welding Defect Assessment System",
        "select_image_folder": "Select Image Folder",
        "label_width": "Original image width (mm):",
        "label_height": "Original image height (mm):",
        "label_thickness": "Container wall thickness",
        "label_working_temp": "Working temperature (℃):",
        "btn_start": "Start Detection",
        "warn_select_folder": "Please select an image folder first!",
        "warn_input_wh": "Please enter image width and height!",
        "warn_input_thickness": "Please enter container wall thickness!",
        "warn_steel_type": "Please select steel type",
        "warn_working_temp": "Please enter working temperature",
        "warn_select_1t_material": "Please select 1-t assessment material type",
        "warn_select_curve": "Please select temperature exemption curve type",
        "warn_numeric": "Width, height and thickness must be numbers!",
        "error_title": "Error",
        "error_no_caller": "Caller information not received",
        "error_json_parse": "JSON config parse error! Program will exit",
        "error_no_image_folder": "No image folder selected!",
        "error_no_wh": "Image width/height not entered!",
        "error_no_thickness": "Container wall thickness not entered",
        "error_no_images": "No images to detect in the folder",
        "error_mys_not_found": "MYS={mys} MPa was not found in the reference temperature table! Program will exit",
        "error_1t_json_missing": "Cannot find the JSON storing 1-t curve data. Program will exit",
        "error_draw_api_box": "Cannot draw single API result annotation box",
        "info_start_cr": "Start annotating defects and computing width/height",
        "info_start_po": "Start annotating defects and assessing per API 579",
        "info_start_lp": "Start annotating lack-of-penetration defects and assessing per API 579",
        "done_msg": "Detection finished! All results saved to: {folder}",
        "done_stat": "Total time {run_time}s\n{image_num} images processed\nAverage {single_run_time}ms per image",
        "warn_title": "Warning",
        "info_title": "Info",
    },
}


def set_language(lang):
    """设置语言，lang 为 "zh" 或 "en"。"""
    global _LANG
    if lang in ("zh", "en"):
        _LANG = lang


def get_language():
    return _LANG


def t(key, **kwargs):
    """按当前语言返回文案，支持 {key} 占位符格式化。"""
    table = _TRANSLATIONS.get(_LANG, _TRANSLATIONS["zh"])
    fallback = _TRANSLATIONS["zh"]
    text = table.get(key, fallback.get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text
