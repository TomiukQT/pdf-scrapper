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
from io import StringIO
from datetime import date


def get_downloads(folder):
    pdfs = []
    path = f'data/{folder}'
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        pdfs = [f.split('__')[1] for f in listdir(path) if isfile(join(path, f)) and f.split(".")[-1] == 'pdf']
    return pdfs


# %%
def request_pdf_single(folder, url, page, file_prefix, downloaded):
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
            path = f'data/{folder}/{file_prefix:03d}__{file_name}'
            if file_name in downloaded:
                continue
            file_prefix += 1
            print(f"Downloading {file_name} from: {full_url}")
            open(path, 'wb').write(r.content)
            #year = int(doc.info[0]['CreationDate'][2:6])
            # urllib.request.urlretrieve(f'{prefix}{link}', f'/data/{i}.pdf')
    return file_prefix
https://www.novarole.cz/modules/file_storage/download.php?file=e1d9d58c%7C704

def request_pdf(folder, url, first, last, downloaded):
    file_prefix = len(downloaded)
    if not os.path.exists(f'data/{folder}'):
        os.makedirs(f'data/{folder}')
    for i in range(last, first-1, -1):
        file_prefix = request_pdf_single(folder, url, i, file_prefix, downloaded)
        time.sleep(.1)

##Pdf parsing and craeting reoslution

def extract_text(pdf_path):
    output_string = StringIO()
    with open(pdf_path, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)

    return output_string.getvalue()


def parse_new_format(resolutions, text, debug=False):
    date_pub = parse_new_date(text.splitlines()[1])
    res = {
        'name': '',
        'header': '',
        'res_text': '',
        'result': ''
    }
    mode = 'name'
    for line in text.splitlines():
        if debug:
            print(f">>>{line}")
        if re.search('^RMě/.*', line) and mode == "name":
            res['name'] = line
            mode = "header"
            continue
        if mode == "header":
            res['header'] = line
            mode = "text"
            continue
        if mode == "text" and re.search('^Usnesení .*', line):
            res['result'] = line
            # resolutions.append(Resolution(name, header, date_pub, restext, result))
            res = res.fromkeys(res, '')
            mode = "name"
        if mode == "text":
            res['res_text'] += line.strip()


def parse_new_date(date_line):
    date_r = re.search(r'[1-3]*[1-9]. [1]*[1-9]. 20[1-3][1-9]', date_line)
    date_text = date_r.group(0)
    date_p = re.findall(r'\d+', date_text)
    return date.fromisoformat(f'{int(date_p[2])}-{int(date_p[1]):02d}-{int(date_p[0]):02d}')


def get_resolutions():
    resolutions = []
    path = 'data/council'
    files = os.listdir(path)
    for name in files:
        text = extract_text(f'{path}/{name}')
        parse_new_format(text, False)
    return resolutions


def create_database():
    pdfs = get_downloads('council')
    request_pdf('council', 'https://www.novarole.cz/samosprava/rada-mesta/usneseni-rady-mesta/?page=', 1, 4, pdfs)
    # new_pdfs = download_new_files(pdfs)
    resolutions = get_resolutions()


def __main__():
    create_database()


if __name__ == '__main__':
    __main__()
