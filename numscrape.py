
# coding: utf-8

from bs4 import BeautifulSoup
import requests
import re
import math
import pandas as pd
import time
import numpy as np
import bomscrape




def get_soup(url):
    response = requests.get(url) 
    soup = None
    if response.status_code == 200:
        page = response.text
        soup = BeautifulSoup(page, 'html5lib')
    else:
        print 'Unresponsive. Trying Again...'
        time.sleep(0.5)
        return get_soup(url)
    return soup



def get_budget():
    soup = get_soup('http://www.the-numbers.com/movie/budgets/all')
    table = soup.find('table')
    df = pd.DataFrame()
    for tr in table('tr'):
        if tr.find('b') is not None:
            movie = tr.find('b').text
            budget = bomscrape.clean_int(tr.find_all(class_='data')[1].text)
            df = df.append(pd.Series([movie, budget]), ignore_index=True)
    df.columns = ['MovieTitle', 'Budget']
    return df





