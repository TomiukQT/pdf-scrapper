import requests
from bs4 import BeautifulSoup  ##
import re
import pandas as pd
import time
import urllib
import os
from os import listdir
from os.path import isfile, join
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from io import StringIO, BytesIO
import sys

from datetime import date

from .models import Resolution, ExtendedResolution
import logging


def get_downloads(folder):
    pdfs = []
    path = f'data/{folder}'
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        pdfs = [f.split('__')[1] for f in listdir(path) if isfile(join(path, f)) and f.split(".")[-1] == 'pdf']
    return pdfs


# %%
def request_pdf_single(url, page):
    full_url = f'{url}{page}'
    resp = requests.get(full_url)
    resp.encoding = 'utf-8'

    soup = BeautifulSoup(resp.content, from_encoding="utf-8")

    prefix = "https://www.novarole.cz/"

    for i, l in enumerate(soup.find_all("a", class_="file")):
        link = l.get('href')
        if "file_storage" in link:
            # print(l.get('download'))
            r = requests.get(f'{prefix}{link}', allow_redirects=True)
            file_name = l.get('download')
            return r, link
    return '', ''


def request_pdf(current, url, parser_func, last_url):
    for i in range(0, 20):
        response, link = request_pdf_single(url, i)
        if response == '' or link == '':
            continue
        if link not in current:
            parser_func(extract_text(response))
            return
        else:
            break
        if link == last_url:
            break


# Pdf parsing and creating resolution
def extract_text(pdf_response):
    output_string = StringIO()
    pdf = BytesIO(pdf_response.content)
    parser = PDFParser(pdf)
    doc = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.create_pages(doc):
        interpreter.process_page(page)

    return output_string.getvalue()


def remove_all(arr, x):
    while x in arr:
        arr.remove(x)


def parse_new_format(text, debug=False) -> []:
    lines = text.splitlines()
    while '' in lines:
        lines.remove('')
    while ' ' in lines:
        lines.remove(' ')
    # logging.warning(lines)
    date_pub = parse_new_date(lines[1])

    res_text = ''
    category = 'None'
    mode = 'name'

    for line in text.splitlines():
        if debug:
            print(f">>>{line}")
        if mode == "name" and re.search(r'^\d+/\d+ - ', line):
            category = line.split('- ')[1]
            continue
        if re.search('^RMě/.*', line) and mode == "name":
            resolution = Resolution.objects.create()
            resolution.name = line
            mode = "header"
            continue
        if mode == "header":
            resolution.name += line
            mode = "text"
            continue
        if mode == "text" and re.search('^Usnesení .*', line):
            resolution.text = res_text
            resolution.result_text = line
            resolution.vote_yes, resolution.vote_no, resolution.vote_neutral = parse_new_result(line)
            resolution.category = category
            resolution.date = date_pub
            resolution.save()
            res_text = ''
            mode = "name"
        if mode == "text":
            res_text += line.strip()


def parse_zme_format(text, debug=False):
    #import pdb;pdb.set_trace()
    lines = text.splitlines()

    #while '' in lines:
        #lines.remove('')
    #while ' ' in lines:
        #lines.remove(' ')
    # import pdb;pdb.set_trace()
    date_pub = parse_new_date(lines[2])
    resolutions = []
    name = ""
    restext = ""
    result = ""

    attendance = []
    category = ''

    mode = "init"
    scanning = True
    for line in lines:
        if debug:
            print(f">>>{line}")
        if re.search(r'^Omluven[aiy]*:', line) and mode == "init":
            attendance = parse_attendance(line)
            mode = "firstscan"
            continue
        if mode == "firstscan" and re.search(r'^[0-9]*/03', line):
            category = line
            mode = "name"
            continue
        if mode == "scan":
            if re.search(r'^[0-9]+/[0-9]+', line):
                category = line
                mode = "name"
                continue
            else:
                category = "Unknown"
                mode = "name"
        if mode == "name":
            if re.search('^ZMě/', line):
                name = line
                mode = "name2"
                continue
            else:
                mode = "text"
        if mode == "name2":
            name += f' -- {line}'
            mode = "text"
            continue
        if mode == "text" and re.search(r'^Usnesení ', line, re.IGNORECASE):
            mode = "result"
            result = line
            continue
        if mode == "result":
            if line == '' or line == ' ':
                mode = "final"
            else:
                result += line

        if mode == "final":
            mode = "scan"
            ex_resolution = ExtendedResolution.objects.create()
            ex_resolution.name = name
            ex_resolution.text = restext
            ex_resolution.result_text = result
            ex_resolution.attendance = attendance_to_str(attendance)

            results, ex_resolution.vote_yes, ex_resolution.vote_no, ex_resolution.vote_neutral, \
                ex_resolution.vote_missing, ex_resolution.result = parse_result_zme(result, attendance)
            ex_resolution.result_by_person = result_to_str(results)
            ex_resolution.category = category
            ex_resolution.date = date_pub
            ex_resolution.save()
            restext = ""
            continue
        if mode == "text":
            if line == ' ' or line == '':
                restext += '\n'
            else:
                restext += line.strip()
    return resolutions


def parse_attendance(text):
    attendance = []
    words = re.findall(r'\w+', text, re.UNICODE)
    for word in words:
        if word in representatives:
            attendance.append(word)
    return attendance


def parse_result_zme(text, attendance):
    active = [x for x in representatives if x not in attendance]
    result = dict.fromkeys(representatives, "?")

    yes = 0
    no = 0
    neutral = 0
    missing = 0
    result_bool = False
    if re.search(r'^Usnesení schváleno', text):
        result_bool = True
        y = re.findall(r'\d+', text)[0]
        yes = int(y)
    # Nekdo se zdrzel nebo hlasoval proti:
        if ',' in text:
            tokens = re.findall(r'\d+ \w+', text, re.UNICODE)
            votings = re.findall(r'\([^)]+\)', text, re.UNICODE)

            i = 0
            for s in tokens[1:]:
                split = s.split(' ')
                if split[1] == 'se':
                    neutral = int(split[0])
                    set_result(result, 'Zdrzel', votings[i])
                elif split[1] == 'nepřítomen':
                    missing = int(split[0])
                    set_result(result, 'Nepritomen', votings[i])
                elif split[1] == 'proti':
                    no = int[split[0]]
                    set_result(result, 'Proti', votings[i])
                else:
                    continue
                i += 1

        for a in active:
            if result[a] == "?":
                result[a] = "Pro"


    if re.search(r'^Usnesení nepřijato', text, re.IGNORECASE):
        res = re.findall(r'\(.+\)', text, re.UNICODE)[0]
        tokens = res[1:-1].split(' ')
        votings = re.findall(r'– [^–]+(;|\))', text, re.UNICODE)
        result_bool = False

        last = ''
        i = 0
        for s in tokens:
            if s == 'se':
                neutral = int(last)
                set_result(result, 'Zdrzel', votings[i])
            elif s == 'nepřítomen':
                missing = int(last)
                set_result(result, 'Nepritomen', votings[i])
            elif s == 'proti':
                no = int(last)
                set_result(result, 'Proti', votings[i])
            elif s == 'pro':
                yes = int(last)
                set_result(result, 'Pro', votings[i])
            else:
                last = s
                continue
            i += 1
            last = s



    #import pdb; pdb.set_trace()
    return result, yes, no, neutral, missing, result_bool


def result_to_str(results: {}):
    s = '('
    for k in results.keys():
        s += f'{k}:{results[k]},'
    return s[:-1] + ')'


def attendance_to_str(attendance: []):
    s = 'Docházka:('
    for a in attendance:
        s += f'{a},'
    return s[:-1] + ')'


def set_result(results, to, text):
    tokens = re.findall(r'\w+', text, re.UNICODE)
    for s in tokens:
        if s in results.keys():
            results[s] = to


def parse_new_result(result_text):
    t = 0
    f = 0
    n = 0
    tokens = result_text.split(' ')
    remove_all(tokens, '')
    for i in range(0, len(tokens)):
        if tokens[i] == 'schváleno':
            t = int(tokens[i + 1])
        if tokens[i] == 'proti':
            f = int(tokens[i - 1])
        if tokens[i] == 'se':
            n = int(tokens[i - 1])
    return t, f, n


def parse_new_date(date_line):
    date_r = re.search(r'[1-3]*[0-9]. [1]*[1-9]. 20[1-3][0-9]', date_line)
    if date_r is None:
        return date.today()
    date_text = date_r.group(0)
    date_p = re.findall(r'\d+', date_text)
    return date.fromisoformat(f'{int(date_p[2])}-{int(date_p[1]):02d}-{int(date_p[0]):02d}')


def get_resolutions():
    resolutions = []
    path = 'scrapper/data/council'
    files = os.listdir(path)
    for name in files:
        logging.warning(name)
        text = extract_text(f'{path}/{name}')
        return parse_new_format(text, False)
        resolutions.append(parse_new_format(text, False))
    return resolutions


def get_current_data():
    resolutions = set(map(lambda x: x.link, Resolution.objects.all()))
    resolutions_zme = set(map(lambda x: x.link, ExtendedResolution.objects.all()))
    return resolutions, resolutions_zme


def check_and_update(current_data, current_data_zme):
    request_pdf(current_data, PREFIX, parse_new_format, LAST)
    request_pdf(current_data_zme, PREFIX_ZME, parse_zme_format, LAST_ZME)


def refresh_data():
    current_data, current_data_zme = get_current_data()
    check_and_update(current_data, current_data_zme)
    # create_database()


LAST = 'https://www.novarole.cz/modules/file_storage/download.php?file=5bae53d5%7C706'
PREFIX = 'https://www.novarole.cz/samosprava/rada-mesta/usneseni-rady-mesta/?page='
LAST_ZME = 'https://www.novarole.cz/modules/file_storage/download.php?file=0d6531d4%7C672'
PREFIX_ZME = 'https://www.novarole.cz/samosprava/zastupitelstvo-mesta/zapisy-z-jednani-zastupitelstva/?page='
representatives = ["Pokorná", "Krbcová", "Nesybová", "Dušková", "Tichá",
                   "Škarda", "Sýkora", "Bartoň", "Švec", "Pastor", "Slíž",
                   "Pavlíček", "Niedermertl", "Cinegr", "Kvapil"]


def substitute(x):
    if x == 'Bechiňský':
        return 'Bartoň'


def __main__():
    return


if __name__ == '__main__':
    globals()[sys.argv[1]]()
