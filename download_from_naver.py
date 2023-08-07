'''
전체적인 방법
다운로드 하고자 하는 웹툰의 titleId를 가져온다


0. 다운로드 경로 변경
1. 로그인 화면 띄우고
2. id를 통해 웹툰 페이지에 접속
3. title과 link를 csv로 저장
4. 루프를 돌면서 페이지를 다운로드
	ㄱ. 마지막까지 스크롤
	ㄴ. 전체 댓글 더 보기 클릭
	ㄷ. 댓글 더 보기 2번정도 더 클릭(있다면)
	ㄹ. pyautogui로 다운로드 클릭
	ㅁ. 다운로드가 끝나는 걸 어떻게 대기하지???
	ㅂ. 다운로드한 파일이름 변경
	ㅅ. 약간의 대기


프로그램을 시작하기에 앞서 현재 사용중인 크롬 버전과 프로젝트 폴더의 있는 크롬 드라이버의 버전이 다른 경우 실행 불가
아래 페이지에서 최신 크롬 드라이버를 받도록
https://chromedriver.chromium.org/downloads
'''
import os
import re
import time
import argparse
import pyautogui
import pandas as pd
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

@dataclass
class Data:
    title: str
    url: str


def try_assert(args):
    assert (args.id)
    assert (args.dst_folder)
    assert (os.path.exists(args.dst_folder))
    assert (args.webtoon_name)
    if args.url_file:
        assert (os.path.exists(args.url_file))


def initialize_option(dst_folder):
    options = webdriver.ChromeOptions()

    # Save page with SingleFile extension install
    options.add_extension("1.18.53_0.crx")

    # set download path
    prefs = {'download.default_directory': dst_folder}
    options.add_experimental_option('prefs', prefs)
    return options


def initialize_driver(options):
    driver = webdriver.Chrome(executable_path="chromedriver.exe", options=options)
    driver.maximize_window()

    # 확장 클릭
    pyautogui.click(3665, 85)

    # 고정 클릭
    pyautogui.click(3599, 288)

    # 확장 다시 클릭
    pyautogui.click(3665, 85)

    # savefile page 클릭
    # pyautogui.click(3613, 83)

    return driver


def is_loaded(driver, css_selector):
    return driver.execute_script("return document.readyState") == 'complete' and \
           (not css_selector or driver.find_elements_by_css_selector(css_selector))

def connect_webpage(driver, sec, url, css_selector=''):
    # driver.implicitly_wait(sec)
    driver.get(url)

    try:
        WebDriverWait(driver, sec).until(lambda driver: is_loaded(driver, css_selector))
    except TimeoutException:
        raise Exception(f"Timed out waiting for page to load : {url}")

def parse_tags(driver, selector):
    tags = driver.find_elements_by_css_selector(selector)
    if not tags:
        raise Exception(f"Can't load tags : {selector}")
    return tags


def parse_title(driver, webtoon_name):
    # TODO 페이지가 10이 넘어서 다음화살표가 있는 경우는 미구현
    connect_webpage(driver, 10,
                    url=f'https://comic.naver.com/webtoon/list?titleId={args.id}&page=1&sort=ASC',
                    css_selector="[class*='EpisodeListView__count--']")

    total_count_tag = driver.find_elements_by_css_selector("[class*='EpisodeListView__count--']")
    if not total_count_tag:
        raise Exception("Can't load total count num")
    total_number = int(re.findall(r'\d+', total_count_tag[0].text)[0])


    records = []

    count_tags = driver.find_elements_by_css_selector("button[class*='Paginate__page--']")
    max_count = max([int(tag.text) for tag in count_tags])

    title_selector = "[class*='EpisodeListList__title--']"
    link_selector = "a[class*='EpisodeListList__link--']"
    for num in range(1, max_count + 1):
        connect_webpage(driver, 10,
                        url=f'https://comic.naver.com/webtoon/list?titleId={args.id}&page={num}&sort=ASC',
                        css_selector=title_selector)

        title_tags = parse_tags(driver, title_selector)
        link_tags = parse_tags(driver, link_selector)

        for title_tag, link_tags in zip(title_tags, link_tags):
            records.append((title_tag.text, link_tags.get_attribute('href')))


    parsed_num = len(records)
    if total_number != parsed_num:
        raise Exception(f"It if different : {total_number} vs {parsed_num}")

    df = pd.DataFrame.from_records(records, columns=['title', 'link'])
    df.to_csv(f'{webtoon_name}.csv', encoding='utf-8-sig')

    records = [Data(*record) for record in records]
    return records


def download_pages(args, driver, records):
    num_width = len(str(len(records)))

    for idx, record in enumerate(records):
        _download_page(driver, num_width, idx, record, args)
        if idx > 10:
            break


def show_comments(driver):
    total_comment_selector = "[class*='u_cbox_btn_view_comment']"
    more_comment_selector = "[class*='u_cbox_btn_more']"

    driver.find_element_by_tag_name('body').send_keys(Keys.END)

    curr_style = driver.find_element_by_class_name("u_cbox_paginate").get_attribute("style")
    while curr_style == 'display: none;':
        total_comment = parse_tags(driver, total_comment_selector)[0]
        if total_comment.is_displayed() and total_comment.is_enabled():
            total_comment.click()
        curr_style = driver.find_element_by_class_name("u_cbox_paginate").get_attribute("style")
        time.sleep(0.3)


    # 두 번 더 더보기 댓글을 호출
    # TODO 두 번 이상 댓글 더보기가 없는 경우 미구현
    for _ in range(2):
        time.sleep(0.5)
        comment = parse_tags(driver, more_comment_selector)[0]
        comment.click()


def wait_for_mask_erased(driver):
    mask_selector = "singlefile-mask"
    tags = driver.find_elements_by_css_selector(mask_selector)
    cnt = 0
    while tags:
        time.sleep(1)
        tags = driver.find_elements_by_css_selector(mask_selector)
        cnt += 1
        if cnt > 30:
            raise Exception(f"Time is more than 30 sec in wait mask")


def wait_for_chrome_download(prev_list, dst_folder):
    # chrome에서 파일을 다운받을 때 tmp파일로 저장되므로
    # tmp파일을 리턴하지 않도록 확장자 확인 과정 필요

    cnt = 0
    while cnt < 30:
        curr_list = set(os.listdir(dst_folder))
        diff = curr_list - prev_list

        if len(diff) > 1:
            raise Exception(f"There are more than 1 files: {diff}")

        if diff:
            new_file = list(diff)[0]
            if new_file.endswith('.html'):
                return new_file

        cnt += 1
        time.sleep(1)

    raise Exception("Time is more than 30 sec in chrome_download")


def _download_file(driver, args):
    # 현재 폴더 상태 저장
    prev_list = set(os.listdir(args.dst_folder))

    # 다운로드 클릭
    pyautogui.click(3613, 83)

    # 다운로드 창 나타나는 것을 대기
    time.sleep(1)

    # mask가 사라지는 것을 대기
    wait_for_mask_erased(driver)

    # file이 실제로 다운로드 되는 것을 대기
    new_file = wait_for_chrome_download(prev_list, args.dst_folder)

    return new_file


def _download_page(driver, num_width, idx, record, args):
    # 웹페이지 접속
    total_comment_selector = "[class*='u_cbox_btn_view_comment']"
    connect_webpage(driver, 30,
                    url=record.url,
                    css_selector=total_comment_selector)

    # 댓글 띄우기
    show_comments(driver)

    # 실제 파일 다운로드
    new_file = _download_file(driver, args)

    # 파일 이름 변경
    src_path = os.path.join(args.dst_folder, new_file)
    dst_path = os.path.join(args.dst_folder, f'{idx:0{num_width}}_{record.title}.html')
    os.rename(src_path, dst_path)


def main(args):
    try_assert(args)

    options = initialize_option(args.dst_folder)

    driver = initialize_driver(options)

    # TODO 로그인 이후 페이지를 어떻게 처리할지 미구현
    if not args.without_login:
        connect_webpage(driver, 3, 'https://nid.naver.com/nidlogin.login?mode=form&url=https%3A%2F%2Fwww.naver.com')

    # naver에서 selenium으로 접속하는 것을 차단하기 때문에 로그인은 직접 해주어야 함
    # 따라서 아래 라인에서 디버깅을 걸어두고 로그인하는 것이 편리
    debuggin_point = 0

    # TODO 이미 url 데이터를 파싱한 경우, title 파싱을 생략하도록 작성 필요 (매번 파싱하는 것은 귀찮)
    if args.url_file:
        df = pd.read_csv(args.url_file)
        records = [Data(record[1], record[2]) for record in df.to_records(index=False)]
    else:
        records = parse_title(driver, args.webtoon_name)

    download_pages(args, driver, records)

    driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--id",
                        help="웹툰의 ID : https://comic.naver.com/webtoon/list?titleId=778963 에서 778963에 해당")  # extra value
    parser.add_argument("-d", "--dst_folder", help="file이 저장될 경로")
    parser.add_argument("-w", "--without_login", action='store_true', help="로그인을 해야 하는 경우 설정")
    parser.add_argument("-n", "--webtoon_name", help="csv로 저장할 웹툰의 이름")
    parser.add_argument("-f", "--url_file", help="title과 url이 저장된 csv 파일. 반드시 idx, title, url의 형태")

    args = parser.parse_args()

    main(args)
