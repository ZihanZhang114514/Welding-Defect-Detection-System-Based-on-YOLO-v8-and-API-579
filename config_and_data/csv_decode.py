import csv
from pathlib import Path

# 以本脚本所在目录为基准，使用相对路径
CSV_FILE = Path(__file__).resolve().parent / "low_alloy_steel_reference_temperature.csv"


while True:
    try:
        mys=int(input("请输入压力(Mpa): "))
        break
    except ValueError:
        print("请输入数字!")

while True:
    material_type=input(r"请输入材料类型（A/B/C/D）：")
    if material_type=="A" or material_type=="B" or material_type=="C" or material_type=="D":
        break

    elif material_type=="a" or material_type=="b" or material_type=="c" or material_type=="d":
        break
    else:
        print("请输入ABCD之中的一个字母！")

with open(CSV_FILE, newline='', encoding="utf-8-sig") as csvfile:
    rowdics_list = []  # 创建列表，存储csv行字典
    mys_list = []
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        mys_list.append(int(row["MYS (MPa)"]))  #将MYS数据存入列表
        rowdics_list.append(row)

count_mys=0
mys_row=0
#记录所在行的位置，以便解包
for mys_in_csv in mys_list:
    if mys== mys_in_csv:
        mys_row=count_mys
        break
    count_mys+=1

#确定参考温度
ref_temp=0
if "A" in material_type:
    ref_temp=int(rowdics_list[mys_row]["A (°C)"])
elif "B" in material_type:
    ref_temp=int(rowdics_list[mys_row]["B (°C)"])
elif "C" in material_type:
    ref_temp = int(rowdics_list[mys_row]["C (°C)"])
elif "D" in material_type:
    ref_temp = int(rowdics_list[mys_row]["D (°C)"])

elif "a" in material_type:
    ref_temp=int(rowdics_list[mys_row]["A (°C)"])
elif "b" in material_type:
    ref_temp=int(rowdics_list[mys_row]["B (°C)"])
elif "c" in material_type:
    ref_temp = int(rowdics_list[mys_row]["C (°C)"])
elif "d" in material_type:
    ref_temp = int(rowdics_list[mys_row]["D (°C)"])

print(f"参考温度是{ref_temp}")
