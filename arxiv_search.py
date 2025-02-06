import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time


def simple_search(search_string):
    """
    在 arXiv 主搜索页面搜索、翻页，并保存所有结果到 results.json。

    :param search_string: 搜索的关键词
    """
    # 设置 ChromeDriver
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # 保存结果的文件名
    output_file = "results.json"

    # 如果文件存在，读取已有数据
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            results = json.load(f)
    else:
        results = []

    try:
        # 打开 arXiv 主搜索页面
        driver.get("https://arxiv.org/search/")

        # 输入搜索关键词
        search_box = driver.find_element(By.CSS_SELECTOR, 'input#query')
        search_box.send_keys(search_string)

        # 点击搜索按钮
        search_button = driver.find_element(By.CSS_SELECTOR, 'button.button.is-link.is-medium')
        search_button.click()

        # 等待搜索结果加载
        time.sleep(5)

        # 设置结果页为 200 条
        dropdown = driver.find_element(By.CSS_SELECTOR, 'select#size')
        dropdown.click()
        dropdown.find_element(By.XPATH, '//option[@value="200"]').click()

        # 点击 "Go" 按钮
        go_button = driver.find_element(By.CSS_SELECTOR, 'button.button.is-small.is-link')
        go_button.click()

        # 等待页面重新加载
        time.sleep(5)

        # 开始提取数据并处理翻页
        while True:
            # 提取当前页的论文信息
            papers = driver.find_elements(By.CSS_SELECTOR, 'li.arxiv-result')
            for paper in papers:
                # 提取 arXiv 索引
                arxiv_index = paper.find_element(By.CSS_SELECTOR, 'p.list-title a').text.strip()
                # 提取论文名称
                paper_name = paper.find_element(By.CSS_SELECTOR, 'p.title').text.strip()
                # 提取作者列表
                authors = paper.find_element(By.CSS_SELECTOR, 'p.authors').text.strip()
                authors = authors.replace("Authors:", "").strip()  # 去掉 "Authors:" 标记

                # 保存到结果列表
                results.append({
                    "arxiv_index": arxiv_index,
                    "paper_name": paper_name,
                    "authors": authors
                })

            # 保存到 JSON 文件
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4, ensure_ascii=False)

            # 检查是否有下一页
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'a.pagination-next')
                if "disabled" in next_button.get_attribute("class"):
                    break  # 如果按钮被禁用，说明没有下一页
                else:
                    next_button.click()
                    time.sleep(5)  # 等待下一页加载
            except:
                break

    except Exception as e:
        print(f"发生错误：{e}")

    finally:
        driver.quit()

def search_arxiv_and_save(search_string, start_date="0", end_date="0", search_all_fields=False):
    """
    在 arXiv 高级搜索页面搜索、翻页，并保存所有结果到 results.json。

    :param search_string: 搜索的关键词
    :param start_date: 起始日期，格式为 "YYYY-MM-DD" 或 "0" 表示不限
    :param end_date: 结束日期，格式为 "YYYY-MM-DD" 或 "0" 表示不限
    :param search_all_fields: 如果为 True，则选择 "All fields" 搜索，否则只搜索标题。
    """
    # 设置 ChromeDriver
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # 保存结果的文件名
    output_file = "results.json"

    # 如果文件存在，读取已有数据
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            results = json.load(f)
    else:
        results = []

    try:
        driver.get("https://arxiv.org/search/advanced")
        search_box = driver.find_element(By.CSS_SELECTOR, 'input#terms-0-term')
        search_box.send_keys(search_string)

        # If "All fields", 即模糊搜索
        if search_all_fields:
            field_dropdown = driver.find_element(By.CSS_SELECTOR, 'select#terms-0-field')
            driver.execute_script("arguments[0].value = 'all';", field_dropdown)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", field_dropdown)

        date_range_radio = driver.find_element(By.CSS_SELECTOR, 'input#date-filter_by-3')
        date_range_radio.click()

        # 输入起始日期（如果设置了）
        if start_date != "0":
            start_date_box = driver.find_element(By.CSS_SELECTOR, 'input#date-from_date')
            start_date_box.send_keys(start_date)

        # 输入结束日期（如果设置了）
        if end_date != "0":
            end_date_box = driver.find_element(By.CSS_SELECTOR, 'input#date-to_date')
            end_date_box.send_keys(end_date)

        search_button = driver.find_element(By.CSS_SELECTOR, 'button.button.is-link.is-medium')
        search_button.click()

        time.sleep(5)

        dropdown = driver.find_element(By.CSS_SELECTOR, 'select#size')
        dropdown.click()
        dropdown.find_element(By.XPATH, '//option[@value="200"]').click()

        go_button = driver.find_element(By.CSS_SELECTOR, 'button.button.is-small.is-link')
        go_button.click()

        time.sleep(5)

        while True:
            papers = driver.find_elements(By.CSS_SELECTOR, 'li.arxiv-result')
            for paper in papers:
                arxiv_index = paper.find_element(By.CSS_SELECTOR, 'p.list-title a').text.strip()
                paper_name = paper.find_element(By.CSS_SELECTOR, 'p.title').text.strip()
                authors = paper.find_element(By.CSS_SELECTOR, 'p.authors').text.strip()
                authors = authors.replace("Authors:", "").strip()  # 去掉 "Authors:" 标记

                results.append({
                    "arxiv_index": arxiv_index,
                    "paper_name": paper_name,
                    "authors": authors
                })

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4, ensure_ascii=False)

            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'a.pagination-next')
                if "disabled" in next_button.get_attribute("class"):
                    break
                else:
                    next_button.click()
                    time.sleep(5)
            except:
                break

    except Exception as e:
        print(f"发生错误：{e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    search_arxiv_and_save("machine learning", start_date="2023-01", end_date="2023-12-31", search_all_fields=True)
    # simple_search("something")
