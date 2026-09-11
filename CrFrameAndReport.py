# -*- coding: utf-8 -*-
"""
CrFrameAndReport.py
===================

将过程式脚本 label_PO.py 中的「画框 + 裁剪 + 长宽标注 + 报告生成」核心逻辑
重构为面向对象的类，供 label_CR.py 在完成缺陷检测与 API 579（PI 579）评定后调用，
生成最终的带框报告。

分工说明：
    缺陷检测（YOLO 推理）与 API 579 评定仍由调用方 label_CR.py 完成；
    本类只负责：根据评定结果画框、裁剪单个缺陷、标注长宽、生成 Word 报告。

====================================================================================
接口文档（重要：本类改变了原 label_PO.py 使用全局变量的传参方式，特此说明）
====================================================================================
构造方法：
    CRFrameAndReport(api_ass_result_list, folder_path)

参数说明：
    1) api_ass_result_list : list[dict]
       由 CrApiAssisment.depark() 产生的评定结果列表
       （即 CrApiAssisment.api_ass_result_list）。
       列表中每个元素对应一张图片，是一个字典，**必需的 key 及其值类型**如下：
         "img_path"         : str                —— 图片绝对路径
         "xyxys_list"       : list[list[int]]    —— 所有缺陷检测框坐标，
                                                    内层列表为 [x1, y1, x2, y2]（像素，int）
         "wahs_list"        : list[list[float]]  —— 所有缺陷的实际宽高，
                                                    内层列表为 [width_mm, height_mm]（mm，float）
         "lengths_list"     : list[float]        —— 所有缺陷长度（取宽高较大值），单位 mm
         "max_allow_length" : float              —— 该图允许的最大缺陷长度，单位 mm
         "is_pass"          : bool               —— 该图是否通过 API 579 评定

    2) folder_path : str
       用户选择的图片文件夹绝对路径；输出会写入 folder_path/output 及
       folder_path/inspection_report.docx。

主要方法：
    run() —— 主入口：遍历评定结果 -> 画框并保存图片 -> 生成报告。
"""

import os

import cv2
from docx import Document


class CRFrameAndReport:
    """根据 API 579 评定结果绘制带框图像并生成检测报告的类。"""

    def __init__(self, api_ass_result_list, folder_path):
        self.api_ass_result_list = api_ass_result_list
        self.folder_path = folder_path

        # 输出目录结构（与 label_PO.py 保持一致）
        self.output_folder = os.path.join(folder_path, "output")
        os.makedirs(self.output_folder, exist_ok=True)

        self.width_height_folder = os.path.join(self.output_folder, "width_and_height")
        os.makedirs(self.width_height_folder, exist_ok=True)

        self.crop_folder = os.path.join(self.output_folder, "cropped_single_elements")
        os.makedirs(self.crop_folder, exist_ok=True)

        self.single_wh_folder = os.path.join(self.output_folder, "single_element_width_and_height")
        os.makedirs(self.single_wh_folder, exist_ok=True)

        self.single_api_folder = os.path.join(self.output_folder, "api_single_element_box")
        os.makedirs(self.single_api_folder, exist_ok=True)

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def run(self):
        """遍历评定结果，绘制并保存带框图像，最后生成 Word 报告。"""
        for ass_dic in self.api_ass_result_list:
            self._draw_single_image(ass_dic)
        self._generate_docx()
        print(f"带框报告生成完成！输出目录: {self.output_folder}")

    # ------------------------------------------------------------------
    # 单张图片绘制
    # ------------------------------------------------------------------
    def _draw_single_image(self, ass_dic):
        img_path = ass_dic["img_path"]
        xyxy_list = ass_dic["xyxys_list"]
        wahs_list = ass_dic["wahs_list"]
        is_pass = ass_dic["is_pass"]

        filename = os.path.basename(img_path)

        img = cv2.imread(img_path)
        if img is None:
            print(f"警告：无法读取图片 {img_path}，已跳过")
            return

        img_wh = img.copy()  # 仅标注长宽的全图副本

        for i, ((x1, y1, x2, y2), (w_mm, h_mm)) in enumerate(zip(xyxy_list, wahs_list)):
            w_text = f"Width:{w_mm:.4f}mm"
            h_text = f"Height:{h_mm:.4f}mm"

            # 1) 裁剪单个缺陷
            self._crop_single_element(img_path, x1, y1, x2, y2, i)

            # 2) 生成单个缺陷的长宽标注图
            self._draw_single_wh(img_path, x1, y1, x2, y2, i, w_text, h_text)

            # 3) 生成单个缺陷的 API 判定图
            self._draw_single_api(img_path, x1, y1, x2, y2, i, is_pass)

            # 4) 全图判定框
            color = (0, 255, 0) if is_pass else (0, 0, 255)
            label = "passed" if is_pass else "failed"
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # 5) 全图长宽标注
            cv2.rectangle(img_wh, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img_wh, w_text, (x1, y2 + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(img_wh, h_text, (x1, y2 + 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imwrite(os.path.join(self.output_folder, filename), img)
        cv2.imwrite(os.path.join(self.width_height_folder, filename), img_wh)

    # ------------------------------------------------------------------
    # 单个缺陷相关图片
    # ------------------------------------------------------------------
    def _crop_single_element(self, img_path, x1, y1, x2, y2, index):
        """裁剪单个缺陷并保存。"""
        name = os.path.splitext(os.path.basename(img_path))[0]
        folder = os.path.join(self.crop_folder, name)
        os.makedirs(folder, exist_ok=True)
        img = cv2.imread(img_path)
        # 向外扩 6 像素，并用 max 防止越界
        crop = img[max(0, y1 - 6):y2 + 6, max(0, x1 - 6):x2 + 6]
        cv2.imwrite(os.path.join(folder, f"{index}.png"), crop)

    def _draw_single_wh(self, img_path, x1, y1, x2, y2, index, w_text, h_text):
        """为单个缺陷画框并标注长宽后保存。"""
        name = os.path.splitext(os.path.basename(img_path))[0]
        folder = os.path.join(self.single_wh_folder, name)
        os.makedirs(folder, exist_ok=True)
        img = cv2.imread(img_path)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, w_text, (x1, y2 + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(img, h_text, (x1, y2 + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imwrite(os.path.join(folder, f"{index}.png"), img)

    def _draw_single_api(self, img_path, x1, y1, x2, y2, index, is_pass):
        """为单个缺陷画 API 判定框（绿=通过，红=不通过）并保存。"""
        name = os.path.splitext(os.path.basename(img_path))[0]
        folder = os.path.join(self.single_api_folder, name)
        os.makedirs(folder, exist_ok=True)
        img = cv2.imread(img_path)
        color = (0, 255, 0) if is_pass else (0, 0, 255)
        label = "passed" if is_pass else "failed"
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, label, (x1, y2 + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.imwrite(os.path.join(folder, f"{index}.png"), img)

    # ------------------------------------------------------------------
    # Word 报告
    # ------------------------------------------------------------------
    def _generate_docx(self):
        """根据评定结果列表生成 Word 检测报告。"""
        path = os.path.join(self.folder_path, "inspection_report.docx")
        doc = Document()
        doc.add_heading("裂纹(CR)缺陷检测报告", level=1)

        for ass_dic in self.api_ass_result_list:
            filename = os.path.basename(ass_dic["img_path"])
            xyxy_list = ass_dic["xyxys_list"]
            wahs_list = ass_dic["wahs_list"]
            lengths_list = ass_dic["lengths_list"]
            max_allow_length = ass_dic["max_allow_length"]
            is_pass = ass_dic["is_pass"]

            doc.add_paragraph(f"文件名：{filename}")
            doc.add_paragraph("缺陷类型：裂纹(CR)")

            for i in range(len(xyxy_list)):
                w_mm = wahs_list[i][0]
                h_mm = wahs_list[i][1]
                length = lengths_list[i] if i < len(lengths_list) else max(w_mm, h_mm)
                doc.add_paragraph(f"缺陷{i + 1}:")
                doc.add_paragraph(f"    长:{w_mm:.4f}mm，宽:{h_mm:.4f}mm")
                doc.add_paragraph(f"    缺陷长度:{length:.4f}mm，最大允许长度:{max_allow_length:.4f}mm")

            doc.add_paragraph(f"评定结论：{'合格' if is_pass else '不合格'}")
            doc.add_page_break()

        doc.save(path)
        print(f"检测报告已保存到: {path}")
