import concurrent.futures
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service


def get_html(url):
    options = Options()
    options.add_argument("--headless")
    # WebDriverを起動
    edge_path = "C:/Users/dev/programming/nitac-ai-club-platform/msedgedriver.exe"
    service = Service(edge_path)
    driver = webdriver.Edge(options, service)
    # driver.get("http://google.com")
    driver.get(url)
    time.sleep(2)
    html = driver.page_source
    return html


class HTML:
    def __init__(self, url):
        self.url = url
        html = self.get_html(url)
        self.soup = BeautifulSoup(html, "html.parser")

    @staticmethod
    def get_html(url):
        options = Options()
        options.add_argument("--headless")
        # WebDriverを起動
        edge_path = "C:/Users/dev/programming/nitac-ai-club-platform/msedgedriver.exe"
        service = Service(edge_path)
        driver = webdriver.Edge(options, service)
        # driver.get("http://google.com")
        driver.get(url)
        time.sleep(2)
        html = driver.page_source
        return html

    def is_unknown_page(self):
        unknown_page = self.soup.find(
            "h6", class_="sc-dkjaqt eCdyAW", string="We can't find that page."
        )
        return unknown_page is not None

    def exists_page(self):
        return not self.is_unknown_page()

    def is_competition_page(self):
        if (
            self.url.startswith("https://www.kaggle.com/competitions/")
            and self.url.split("/")[-2] == "competitions"
            and not self.is_unknown_page()
        ):
            return True
        return False

    def get_competition_name(self):
        h1 = self.soup.find_all("h1", class_="sc-jCbFiK jzEmlt")
        if len(h1) == 0:
            print(self.soup)
            assert False
            return None

        return h1[0].get_text()

    def get_competition_description(self):
        h1 = self.soup.find_all("span", class_="sc-dENhDJ sc-fTgapq bMuEQk cppFwb")
        if len(h1) == 0:
            return None
        return h1[0].get_text()


def get_competition_picture(competition_url):
    if competition_url[-1] == "/":
        competition_url = competition_url[:-1]

    competition_name = competition_url.split("/")[-1]
    search_url_base = (
        f"https://www.kaggle.com/competitions?searchQuery={competition_name}"
    )

    html = get_html(search_url_base)
    soup = BeautifulSoup(html, "html.parser")

    found_a_list = [
        e.children.__next__().children.__next__()
        for e in soup.find_all(
            "li",
            class_=lambda x: x
            and "MuiListItem-root" in x
            and "MuiListItem-gutters" in x
            and "sc-hDcvty" in x
            and "cBatpr" in x,
        )
    ]

    found_url_list = [
        a
        for a in found_a_list
        if f"https://www.kaggle.com{a.get('href')}" == competition_url
    ]

    if len(found_url_list) == 0:
        nav_list = soup.find_all(
            "span", class_=lambda x: x and "MuiTouchRipple-root" in x
        )
        for nav_child in nav_list:
            nav = nav_child.parent
            if nav.get_text().isdigit:
                next_page_url = f"{search_url_base}&page={nav.get_text()}"

                html = get_html(next_page_url)
                soup = BeautifulSoup(html, "html.parser")

                found_a_list = [
                    e.children.__next__().children.__next__()
                    for e in soup.find_all(
                        "li",
                        class_=lambda x: x
                        and "MuiListItem-root" in x
                        and "MuiListItem-gutters" in x
                        and "sc-hDcvty" in x
                        and "cBatpr" in x,
                    )
                ]

                found_url_list = [
                    a
                    for a in found_a_list
                    if f"https://www.kaggle.com{a.get('href')}" == competition_url
                ]

                if len(found_url_list) > 0:
                    break

    url = found_url_list[0].find("img").get("src")
    if url[0] == "/":
        url = "https://www.kaggle.com" + url
    return url


class Result:
    def __init__(self, code_url: str, competition_url: str, score: float):
        self.code_url = code_url
        self.competition_url = competition_url
        self.score = score

    def __repr__(self):
        return f"BestScore(url={self.code_url}, competition_url={self.competition_url}, score={self.score})"


def _is_unknown_page(soup):
    unknown_page = soup.find(
        "h6", class_="sc-dkjaqt eCdyAW", string="We can't find that page."
    )
    return unknown_page is not None


def _get_public_code_url_list(user_name):
    url = f"https://www.kaggle.com/{user_name}/code"
    html = get_html(url)
    soup = BeautifulSoup(html, "html.parser")
    if _is_unknown_page(soup):
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


def _get_score(url):
    prefix = "https://www.kaggle.com"

    html = get_html(url)
    soup = BeautifulSoup(html, "html.parser")

    if _is_unknown_page(soup):
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

        return Result(url, prefix + competition_relative_url, score)

    else:
        assert False


def _get_best_score_list(public_code_url_list):
    def process_url(url):
        try:
            score = _get_score(url)
            return score
        except ValueError as e:
            return None

    # 並列処理を実行
    with concurrent.futures.ThreadPoolExecutor() as executor:
        score_list: list[Result | None] = list(
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


def calc_result_list(user_name_in_kaggle) -> list[Result]:
    try:
        public_code_url_list = _get_public_code_url_list(user_name_in_kaggle)
    except ValueError as e:
        raise ValueError(f"User {user_name_in_kaggle} is not found")
    result_list = _get_best_score_list(public_code_url_list)

    return result_list
