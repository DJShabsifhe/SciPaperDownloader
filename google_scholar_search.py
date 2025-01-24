import json
import re
import time
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.common.by import By


def build_scholar_page_url(query, start=0, start_year=None, end_year=None, lang="zh-CN"):
    """
    构造带有 offset (start) 和年份参数的 Google Scholar 搜索链接。
    start=0 表示第1页, start=10 表示第2页, 依此类推。
    """
    base_url = "https://scholar.google.com/scholar"
    q = quote(query)
    url = f"{base_url}?start={start}&q={q}&hl={lang}&as_sdt=0,5"

    if start_year:
        url += f"&as_ylo={start_year}"
    if end_year:
        url += f"&as_yhi={end_year}"

    return url


def parse_scholar_results(driver):
    """
    从当前页面的搜索结果中解析信息（标题、URL、作者、年份）。
    返回一个列表，每个元素都是字典。
    """
    papers_data = []
    result_blocks = driver.find_elements(By.CSS_SELECTOR, '.gs_r.gs_or.gs_scl')

    for block in result_blocks:
        paper_title = "N/A"
        paper_authors = "N/A"
        paper_url = "N/A"
        paper_year = "N/A"

        try:
            title_elem = block.find_element(By.CSS_SELECTOR, '.gs_rt')
            paper_title = title_elem.text.strip()
        except:
            paper_title = "No title found"

        try:
            link_elem = title_elem.find_element(By.TAG_NAME, 'a')
            paper_url = link_elem.get_attribute('href')
        except:
            paper_url = "No direct link found"

        try:
            authors_elem = block.find_element(By.CSS_SELECTOR, '.gs_a')
            authors_raw = authors_elem.text.strip()

            authors_parts = authors_raw.split(" - ", 1)
            paper_authors = authors_parts[0].strip()

            rest_info = authors_parts[1] if len(authors_parts) > 1 else ""
            match = re.search(r"\b(1[89]\d{2}|20\d{2})\b", rest_info)
            paper_year = match.group(0) if match else "N/A"

        except:
            paper_authors = "No authors found"
            paper_year = "N/A"

        papers_data.append({
            "url": paper_url,
            "paper_name": paper_title,
            "authors": paper_authors,
            "year": paper_year
        })

    return papers_data


def parse_year_val(year_str):
    """
    尝试将年份字符串转换为 int，失败则返回一个很大的数字（999999），
    这样在排序时无年份的条目会排在最后。
    """
    try:
        return int(year_str)
    except:
        return 999999


def scrape_google_scholar_100_pages(query, start_year=None, end_year=None, output_json="results.json"):
    """
    不解析总结果数，直接从第1页翻到第100页。
    每页10条，总计最多获取 100 * 10 = 1000 条记录。
    如果某一页没有数据，立即停止。
    抓取完后，按照年份升序排序，写入 JSON。
    """
    driver = webdriver.Chrome()
    all_results = []
    page_count = 0
    start = 0

    try:
        while True:
            page_count += 1
            if page_count > 100:
                print("已经爬完所有页面，停止。")
                break

            page_url = build_scholar_page_url(
                query=query,
                start=start,
                start_year=start_year,
                end_year=end_year
            )
            print(f"[第 {page_count} 页] 访问: {page_url}")
            driver.get(page_url)
            time.sleep(2)  # 等待页面加载

            results_on_page = parse_scholar_results(driver)
            count_this_page = len(results_on_page)
            print(f"  本页共抓取到 {count_this_page} 条结果.")

            if count_this_page == 0:
                print("无更多结果，提前结束。")
                break

            all_results.extend(results_on_page)

            start += 10  # Scholar 每页10条

        # 所有结果爬取完成后，按照年份升序排序
        sorted_results = sorted(all_results, key=lambda item: parse_year_val(item.get("year", "N/A")))

        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(sorted_results, f, ensure_ascii=False, indent=4)

        print(f"爬取完成，共计 {len(sorted_results)} 条记录，已保存到 {output_json}。")

        return sorted_results

    finally:
        driver.quit()


if __name__ == "__main__":
    # 示例：搜索 "deep learning segmentation"，时间范围 2022~2023
    # 不管总结果多少，最多翻到 100 页或遇到空页就停止。
    # 最后按照年份(升序)排序输出。
    scrape_google_scholar_100_pages(
        query="deep learning segmentation",
        start_year=2022,
        end_year=2023,
        output_json="google_results.json"
    )
