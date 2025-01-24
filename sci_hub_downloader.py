import json
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


def read_google_results(json_file):
    """
    读取 google_results.json 文件，按年份整理 URL 和文件名列表。
    :param json_file: JSON 文件路径
    :return: 按年份分类的字典，例如 {2022: {"urls": [...], "names": [...], "metadata": [...]}}
    """
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    results_by_year = {}
    for entry in data:
        year = entry.get("year", "Unknown")
        url = entry.get("url")
        paper_name = entry.get("paper_name")
        authors = entry.get("authors")

        if year not in results_by_year:
            results_by_year[year] = {"urls": [], "names": [], "metadata": []}

        sanitized_name = paper_name.replace("/", "-").replace(" ", "_") + ".pdf"
        results_by_year[year]["urls"].append(url)
        results_by_year[year]["names"].append(sanitized_name)
        results_by_year[year]["metadata"].append({
            "url": url,
            "paper_name": paper_name,
            "authors": authors,
            "year": year
        })

    return results_by_year


def init_driver(download_dir):
    """
    初始化 Selenium ChromeDriver，并设置下载目录。
    :param download_dir: 下载保存的目录路径
    :return: Selenium WebDriver 对象
    """
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-notifications")

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })

    return driver


def download_from_scihub(driver, url_list, download_dir, file_names, paper_metadata, not_found):
    """
    使用 Selenium 下载 Sci-Hub 文献，并支持自定义保存目录和文件名。
    如果下载链接未找到，将记录到 not_found 列表中。
    :param driver: 已初始化的 Selenium WebDriver
    :param url_list: Sci-Hub 文献 URL 列表
    :param download_dir: 下载保存的目录路径
    :param file_names: 保存文件的自定义名称列表（与 url_list 顺序对应）
    :param paper_metadata: 文献的元数据列表（与 url_list 顺序对应），包含 URL、名称、作者、年份
    :param not_found: 用于存储未找到下载链接的文献信息
    """
    for i, url in enumerate(url_list):
        scihub_link = f"https://sci-hub.se/{url}"
        print(f"[INFO] 打开链接: {scihub_link}")
        driver.get(scihub_link)

        try:
            time.sleep(2)
            download_button = driver.find_element(By.XPATH, "//button[contains(text(), '↓ save')]")
            download_button.click()
            print(f"[INFO] 已点击下载按钮: {url}")

            if file_names and i < len(file_names):
                time.sleep(5)
                downloaded_file = max(
                    [os.path.join(download_dir, f) for f in os.listdir(download_dir)],
                    key=os.path.getctime
                )
                new_file_name = os.path.join(download_dir, file_names[i])
                os.rename(downloaded_file, new_file_name)
                print(f"[INFO] 文件已保存为: {new_file_name}")

        except:
            # 如果未找到下载按钮，将文献信息记录到 not_found 列表
            print(f"[WARN] Sci-hub未找到此文档: {url}")
            not_found.append(paper_metadata[i])
            time.sleep(5)
            continue

    print(f"[INFO] {len(url_list)} 篇文献处理完成。")


def download_papers_by_year(results_by_year, base_download_dir, not_found_file):
    """
    根据年份组织下载 URL 和文件名，并调用下载逻辑，将未找到的文献记录到 JSON 文件。
    :param results_by_year: 按年份分类的字典，例如 {2022: {"urls": [...], "names": [...], "metadata": [...]}}
    :param base_download_dir: 下载文件的根目录
    :param not_found_file: 未找到文献的 JSON 文件路径
    """
    driver = init_driver(base_download_dir)
    not_found = []

    try:
        # 打开 Sci-Hub 主页，手动通过验证码（仅一次）
        driver.get("https://sci-hub.se/")
        print("[INFO] 打开 Sci-Hub 主页，请在浏览器里完成验证码（如有）后，按回车继续...")
        input("按回车继续: ")

        for year, data in results_by_year.items():
            year_dir = os.path.join(base_download_dir, year)
            os.makedirs(year_dir, exist_ok=True)

            print(f"[INFO] 正在处理年份 {year}...")
            download_from_scihub(
                driver,
                data["urls"],
                year_dir,
                data["names"],
                data["metadata"],
                not_found
            )
            print(f"[INFO] 年份 {year} 的文献下载完成。")

    except Exception as e:
        print(f"[ERROR] 处理过程中出现异常: {e}")
    finally:
        with open(not_found_file, "w", encoding="utf-8") as file:
            json.dump(not_found, file, ensure_ascii=False, indent=4)
        print(f"[INFO] 未找到的文献信息已保存到: {not_found_file}")

        driver.quit()
        print("[INFO] 浏览器已关闭。")


if __name__ == "__main__":
    json_file_path = "google_results.json"
    results_by_year = read_google_results(json_file_path)
    base_download_dir = os.path.join(os.getcwd(), "scihub_papers")

    # 未找到文献的保存路径
    not_found_file = os.path.join(os.getcwd(), "not_found.json")

    # 根据年份分类下载
    download_papers_by_year(results_by_year, base_download_dir, not_found_file)
