import requests
from bs4 import BeautifulSoup ##
import re
import pandas as pd
import time
import urllib
import os
from os import listdir
from os.path import isfile,join
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from io import StringIO, BytesIO

from datetime import date

from .models import Resolution,Representative, Voting
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


def request_pdf(current, url):
    for i in range(0, 20):
        response, link = request_pdf_single(url, i)
        if response == '' or link == '':
            continue
        if link not in current:
               parse_new_format(extract_text(response))
        else:
            break
        if link == LAST:
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
    #logging.warning(lines)
    date_pub = parse_new_date(lines[1])

    res_text = ''
    category = 'None'
    mode = 'name'

    for line in text.splitlines():
        if debug:
            print(f">>>{line}")
        if mode == "name" and re.search(r'^\d+/\d+ - ',line):
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


def parse_new_result(result_text):
    t = 0
    f = 0
    n = 0
    tokens = result_text.split(' ')
    remove_all(tokens, '')
    for i in range(0, len(tokens)):
        if tokens[i] == 'schváleno':
            t = int(tokens[i+1])
        if tokens[i] == 'proti':
            f = int(tokens[i - 1])
        if tokens[i] == 'se':
            n = int(tokens[i - 1])
    return t, f, n


def parse_new_date(date_line):
    date_r = re.search(r'[1-3]*[0-9]. [1]*[1-9]. 20[1-3][0-9]', date_line)
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
    return resolutions


def check_and_update(current_data):
    request_pdf(current_data, 'https://www.novarole.cz/samosprava/rada-mesta/usneseni-rady-mesta/?page=')


def create_database():
    resolutions = get_resolutions()


def refresh_data():
    current_data = get_current_data()
    check_and_update(current_data)
    #create_database()


LAST = 'https://www.novarole.cz/modules/file_storage/download.php?file=5bae53d5%7C706'


def substitute(x):
    if x == 'Bechiňský':
        return 'Bartoň'


def create_representatives():
    res = [
        ('Jitka', 'Pokorná', 'VOLBA PRO NOVOU ROLI...'), ('Hana ', 'Nesybová', 'VOLBA PRO NOVOU ROLI...'),
        ('Jiří', 'Sýkora', 'ČSSD'),
        ('Libor', 'Škarda', 'HN.ZA HARM.ROZVOJ OBCÍ'), ('Václav', 'Bartoň', 'VOLBA PRO NOVOU ROLI...'),
        ('Jan', 'Kvapil', 'VOLBA PRO NOVOU ROLI...'),
        ('Tomáš', 'Pavlíček', 'VOLBA PRO NOVOU ROLI...'), ('Petra', 'Krbcová', 'VOLBA PRO NOVOU ROLI...'),
        ('Ladislav', 'Cinegr', 'SNK Nová Role - Mezirolí'),
        ('Luboš', 'Pastor', 'ODS'), ('Milena', 'Tichá', 'ODS'), ('Karel', 'Švec', 'ODS'),
        ('Miluše', 'Dušková', 'HN.ZA HARM.ROZVOJ OBCÍ'),
        ('Ladislav', 'Slíž', 'ANO 2011'), ('David', 'Niedermertl', 'ANO 2011')
    ]

    for r in res:
        representative = Representative.objects.create()
        representative.name, representative.surname, representative.party = r
        representative.save()


def __main__():
    return


if __name__ == '__main__':
    __main__()
