from bs4 import BeautifulSoup
from glob import glob
import json
from multiprocessing import Pool
from os import path
import re

def is_valid_para(para):
    if not para: return False  # no content
    if para == '此回覆已被刪除': return False
    if '分享自 LIHKG 討論區' in para: return False
    if len(para) < 5: return False  # length < 5
    if 'http://' in para: return False  # includes URL
    if 'https://' in para: return False  # includes URL
    if re.fullmatch(r'[A-Za-z ]+', para): return False  # only English words
    if re.fullmatch(r'\d{4}.\d{2}.\d{2}', para): return False  # date
    if re.fullmatch(r'\d{2}:\d{2}:\d{2}', para): return False  # time
    if len(set(para)) * 5 < len(para): return False  # too many repeated characters
    return True

def process_page(obj_str, f):
    obj = json.loads(obj_str)
    if obj['success'] == 1:
        response = obj['response']
        item_data = response['item_data']
        for item_datum in item_data:
            msg = item_datum['msg']
            root = BeautifulSoup(msg, 'lxml')
            while True:
                blockquote = root.blockquote
                if not blockquote:
                    break
                blockquote.decompose()
            text = root.get_text()
            paras = text.split('\n')
            for para in paras:
                para = para.strip()
                if is_valid_para(para):
                    print(para, file=f)

def process_file(src_file):
    dst_file = path.join('processed', src_file)
    with open(src_file) as f, open(dst_file, 'w') as g:
        for line in f:
            _, _, obj_str = line.split('\t')
            process_page(obj_str, g)

def main():
    src_files = glob('./lihkg-*.csv')

    with Pool() as p:
        p.map(process_file, src_files)

if __name__ == '__main__':
    main()
