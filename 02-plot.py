import json
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle as pltRectangle

mpl.rcParams["figure.figsize"] = [15, 7]

with open("result.json", encoding="utf-8") as f:
    api_runs = json.load(f)

df = pd.DataFrame(api_runs, columns=["Response Time", "Region"])
df["Run"] = range(1, len(df) + 1)

# リージョンごとの配色（必要に応じて追加する）
color_map = {
    "Japan East": "lightpink",
    "Sweden Central": "lightyellow",
    "East US 2": "lightblue",
    "UK South": "lightgreen",
    "unavailable": "lightgray",  # 全バックエンド枯渇時の 503
}

colors = [color_map.get(region, "gray") for region in df["Region"]]
ax = df.plot(kind="bar", x="Run", y="Response Time", color=colors, legend=False)

# 凡例（実際に出現したリージョンのみ）
legend_labels = [
    pltRectangle((0, 0), 1, 1, color=color_map.get(region, "gray"))
    for region in df["Region"].unique()
]
ax.legend(legend_labels, df["Region"].unique())

plt.title("Backend Pool Load Balancing results")
plt.xlabel("Run #")
plt.ylabel("Response Time (sec)")
plt.xticks(rotation=0)

average = df["Response Time"].mean()
plt.axhline(y=average, color="r", linestyle="--", label=f"Average: {average:.2f}")

os.makedirs("images", exist_ok=True)
output_path = "images/load-balancing-result.png"
plt.savefig(output_path, bbox_inches="tight", dpi=120)
print(f"保存しました: {output_path}")
