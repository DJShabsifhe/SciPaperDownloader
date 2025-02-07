import json
import time
import os
from pathlib import Path
from arxiv_dl.__main__ import download_paper
import random
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def download_with_retry(index, output_dir, max_retries=3, base_delay=5):
    for attempt in range(max_retries):
        try:
            success = download_paper(
                target=index,
                verbose=False,
                download_dir=output_dir,
                n_threads=5,
                pdf_only=True
            )
            if success:
                print(f"成功下载: {index}")
                return True
            
        except Exception as e:
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"下载 {index} 时出错 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            print(f"等待 {delay:.1f} 秒后重试...")
            time.sleep(delay)
    
    print(f"下载失败 {index} (已重试 {max_retries} 次)")
    return False

with open('results.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

month_indices = {}
for entry in data:
    arxiv_index = entry['arxiv_index']
    year_month = arxiv_index.split(":")[1][:4]
    
    if year_month not in month_indices:
        month_indices[year_month] = []
    month_indices[year_month].append(arxiv_index.split(":")[1])

failed_papers = []
for year_month, indices in sorted(month_indices.items()):
    output_dir = Path(year_month)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n开始处理 {year_month} 中的论文...")
    for index in indices:
        if not download_with_retry(index, output_dir):
            failed_papers.append((year_month, index))
        time.sleep(1)

print("\n下载统计:")
print(f"总论文数: {sum(len(indices) for indices in month_indices.values())}")
print(f"失败数量: {len(failed_papers)}")

if failed_papers:
    print("\n失败的论文列表:")
    for year_month, index in failed_papers:
        print(f"- {year_month}/{index}")
