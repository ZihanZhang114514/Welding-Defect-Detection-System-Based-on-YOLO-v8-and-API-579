from pathlib import Path

import numpy as np
import pandas as pd

# 以本脚本所在目录为基准，使用相对路径
ROOT = Path(__file__).resolve().parent
TARGET_KEYWORDS = ("A_type_material", "B_type_material", "C_type_material")


def process_csv(file_in: Path) -> None:
    file_out = file_in.with_name(f"{file_in.stem}_processed.csv")

    raw_df = pd.read_csv(file_in, header=None)
    if raw_df.shape[1] < 2:
        raise ValueError(f"{file_in.name} 至少需要两列：第一列 X，第二列 Y。")

    df = raw_df.iloc[:, :2].copy()
    df.columns = ["X", "Y"]

    orig_rows = len(df)
    print(f"\n处理文件: {file_in.name}")
    print(f"原始数据行数: {orig_rows}")

    df["X_int"] = df["X"].round().astype(np.int64)
    result = df.groupby("X_int", as_index=False)["Y"].mean()

    result["X"] = result["X_int"].astype(np.float32)
    result["Y"] = result["Y"].astype(np.float32)
    result = result[["X", "Y"]].copy()

    processed_rows = len(result)
    print(f"处理后压缩行数: {processed_rows}")

    result.to_csv(file_out, index=False, float_format="%.6f")
    print(f"已保存至: {file_out}")


if __name__ == "__main__":
    files = sorted(ROOT.glob("*.csv"))
    matched = [
        f
        for f in files
        if any(keyword in f.name for keyword in TARGET_KEYWORDS)
        and not f.name.endswith("_processed.csv")
    ]

    if not matched:
        raise FileNotFoundError(
            f"在目录中没有找到包含这些关键字的原始 CSV 文件: {TARGET_KEYWORDS}"
        )

    print(f"共找到 {len(matched)} 个目标原始 CSV 文件。")
    for file_in in matched:
        process_csv(file_in)

    print("\n全部处理完成。")