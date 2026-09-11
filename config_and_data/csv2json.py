import csv
import json
from pathlib import Path

# 以本脚本所在目录为基准，全部使用相对路径
BASE_DIR = Path(__file__).resolve().parent

PATH_LIST = [
    BASE_DIR / "A_one_t_ass.csv",
    BASE_DIR / "B_one_t_ass.csv",
    BASE_DIR / "C_one_t_ass.csv",
]
TYPE_LIST = ["A", "B", "C"]
JSON_FILE = BASE_DIR / "ABC_one_t_ass_json.json"

dic_tobe_dump_to_json={}
for csv_file,type_name in zip(PATH_LIST,TYPE_LIST):
    temp_list=[]
    length_list=[]
    with open(csv_file, newline="", encoding="utf-8-sig") as f:
        csv_reader = csv.DictReader(f, delimiter=',')
        for row_dic in csv_reader:
            temp=row_dic["T - Tref + 56"] #温度
            length=row_dic["2c"] #最大允许长度
            length_list.append(length)
            temp_list.append(temp)
        single_type_dic={"temp":temp_list,"length":length_list} #存入单类型字典
        dic_tobe_dump_to_json[type_name]=single_type_dic #存入json写入字典

with open(JSON_FILE,"w",encoding="utf-8") as json_file:
    json.dump(dic_tobe_dump_to_json,json_file)