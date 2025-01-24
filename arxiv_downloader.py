import json
import subprocess
import time
import os

with open('results.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

month_indices = {}

for entry in data:
    arxiv_index = entry['arxiv_index']
    year_month = arxiv_index.split(":")[1][:4]

    if year_month not in month_indices:
        month_indices[year_month] = []
    month_indices[year_month].append(arxiv_index.split(":")[1])

for year_month, indices in sorted(month_indices.items()):
    output_dir = year_month
    os.makedirs(output_dir, exist_ok=True)

    command = f"paper -d {output_dir} {' '.join(indices)}"

    print(f"正在处理 {year_month}，执行命令：{command}")
    subprocess.run(command, shell=True)

    time.sleep(2)

print("所有月份处理完成！")
