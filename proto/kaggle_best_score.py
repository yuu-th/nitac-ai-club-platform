import concurrent.futures
import logging
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service


def get_html(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("disable-web-security")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-features=msSmartScreenProtection")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--log-level=OFF")
    options.set_capability("browserVersion", "117")
    options.add_argument("start-maximized")

    options.page_load_strategy = "eager"
    # options.page_load_strategy = "normal"
    # WebDriverを起動
    edge_path = "./msedgedriver.exe"
    service = Service(
        edge_path,
        # service_args=["--log-level="],
        # log_output="test.log",
        # log_level=logging.CRITICAL,
        print_first_line=False,
    )
    driver = webdriver.Edge(options, service)
    # driver.get("http://google.com")
    driver.get(url)
    time.sleep(2)
    html = driver.page_source
    driver.quit()
    return html


def is_unknown_page(soup):
    unknown_page = soup.find(
        "h6", class_="sc-dkjaqt eCdyAW", string="We can't find that page."
    )
    return unknown_page is not None


def get_public_code_url_list(user_name):
    url = f"https://www.kaggle.com/{user_name}/code"
    html = get_html(url)
    soup = BeautifulSoup(html, "html.parser")
    if is_unknown_page(soup):
        raise ValueError("user_name is not found")

    user_name_p = soup.find("p", class_="sc-hfvVTD cZmHWZ")
    if user_name_p is None:
        raise ValueError("user_name is not found")
    li_elements = soup.find_all(
        "li",
        class_="MuiListItem-root MuiListItem-gutters MuiListItem-divider sc-hDcvty cBatpr css-1nkzj85",
    )
    prefix = "https://www.kaggle.com"
    public_code_url_list = []
    for li in li_elements:
        links = li.find_all("a")

        public_code_url_list.append(prefix + links[0].get("href"))

    return public_code_url_list


class Score:
    def __init__(self, code_url: str, competition_url: str, score: float):
        self.code_url = code_url
        self.competition_url = competition_url
        self.score = score

    def __repr__(self):
        return f"BestScore(url={self.code_url}, competition_url={self.competition_url}, score={self.score})"


def get_score(url):
    prefix = "https://www.kaggle.com"

    html = get_html(url)
    soup = BeautifulSoup(html, "html.parser")

    if is_unknown_page(soup):
        raise ValueError("code_url is not found")

    # div_if_no_score_available = soup.find("div", class_="sc-dLVkIh hPYerM")
    score_div_previous_sibling = soup.find(
        "div",
        class_="sc-epPVmt",
        #   class_="sc-epPVmt sc-gXwEoq ktnkNI jDdPdJ",
        string="Best Score",
    )
    # print(score_div_previous_sibling)
    # print(div_if_no_score_available, div_if_score_available)
    if score_div_previous_sibling is None:
        raise ValueError("no score available")
    elif score_div_previous_sibling is not None:
        score = float(score_div_previous_sibling.next_sibling.get_text().split(" ")[0])

        competition_relative_url = soup.find("a", class_="sc-pFPEP dCTTgx").get("href")

        return Score(url, prefix + competition_relative_url, score)

    else:
        assert False


def get_best_score_list(public_code_url_list):
    def process_url(url):
        try:
            score = get_score(url)
            return score
        except ValueError as e:
            return None

    # 並列処理を実行
    with concurrent.futures.ThreadPoolExecutor() as executor:
        score_list: list[Score | None] = list(
            executor.map(process_url, public_code_url_list)
        )

    # score_listの各要素の中でのcompetition_listを調べ、重複したものがあれば、scoreが最大のもののみを一つ選ぶようにする
    competition_url_to_score = {}
    for score in score_list:
        if score is None:
            continue
        if score.competition_url not in competition_url_to_score:
            competition_url_to_score[score.competition_url] = score
        else:
            if score.score > competition_url_to_score[score.competition_url].score:
                competition_url_to_score[score.competition_url] = score

    return list(competition_url_to_score.values())


def main():
    for user_name in ["yuuthk", "rodneybook", "testsetadfsfad", "yul0408"]:
        try:
            public_code_url_list = get_public_code_url_list(user_name)
        except ValueError as e:
            print(
                f"username: {user_name} is not found. Please check the username and try again."
            )
            continue
        best_score_list = get_best_score_list(public_code_url_list)
        print(best_score_list)


if __name__ == "__main__":
    main()
