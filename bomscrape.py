
# coding: utf-8


'''This script contains functions that get called on
to scrape boxofficemojo.com for movie data
'''

from bs4 import BeautifulSoup
import requests
import re
import math
import pandas as pd
import time
import numpy as np
import numscrape


def get_url(page, year, rating):
    head = 'http://www.boxofficemojo.com/yearly/chart/mpaarating.htm?'
    page = 'page='+str(page)+'&'
    year = 'yr='+str(year)+'&'
    rating = 'rating='+rating+'&'
    end = 'view=releasedate&p=.htm'
    url = head+page+year+rating+end
    return url


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


def get_pages(soup):
    for b in soup.find_all('b'):
        bolded = b.text
        if 'Summary of' in bolded:
            numbers = ''.join(re.findall(re.compile('\d'),bolded))
            return int(math.ceil(float(numbers)/100)) 
    return 0
        

def get_header(th):
    headers=[]
    for item in th:
        if item:
            headers.append(item.split('(')[0])
    headers[0] = 'Year'
    headers[4] = 'TotalGross'
    headers[5] = 'TG'+headers[5] 
    headers[7] = 'O'+headers[7] 
    if len(headers)==9:
        if headers[-1] != 'Close':
            headers.append(u'Close')
            return (headers, True)
    return (headers, False)



def make_df(soup, year):
    table = soup.find("table", attrs={"cellpadding":"5"})
    if table is None:
        return
    headers, addclose = get_header([a.text for a in table.tr.find_all('a')])
    df = pd.DataFrame()
    for tr in table('tr'): 
        if tr.get('bgcolor')=='#ffffff' or tr.get('bgcolor')=='#f4f4ff':
            if tr.text[0].isdigit():
                df = df.append(make_vector(tr, addclose), ignore_index=True)
    df.columns=headers
    df['Year'] = [year] * len(df)
#     df.drop('Rank', axis=1, inplace=True)
    return df


def clean_int(unistring):
    if unistring != u'N/A':
        return int(unistring.strip('$').replace(',',''))
    return unistring


def make_vector(tr, addclose):
    items = []
    for item in tr:
        items.append(item.text)
    if addclose == True:
        items.append(u'-')
    vals4to7 = [clean_int(items[i]) for i in range(4,8,1)]
    items = items[:4]+vals4to7+items[8:]

    return pd.Series(items)

    

# Make a dataframe for a certain year or rating for all pages
def category(year, rating):
    firsturl = get_url(1, year, rating)
    soup = get_soup(firsturl)
    pages = get_pages(soup)
    df = make_df(soup, year)
    for page in range(2, pages+1, 1):
        url = get_url(page, year, rating)
        soup = get_soup(url)
        df = pd.concat([df,make_df(soup, year)], ignore_index=True)
    return df



## By Year
## Given year, make a dataframe for each year and rating, 
## initializing with G ratings

def by_year(year):
    startrating = 'G'
    df = category(year,startrating)
    if df is None:
        df = pd.DataFrame()
    ratings = ['PG','PG-13','R','NC-17','Unrated']
    for rating in ratings:
        df = pd.concat([df, category(year, rating)], ignore_index=True)
    return df


## By Rating
## Given rating and range of years, 
## Make a dataframe for each year and rating,
## initializing with the first year

def by_rating(rating, startyear, endyear):
    df = category(startyear, rating)
    if df is None:
        df = pd.DataFrame()
    years = range(startyear+1, endyear+1, 1)
    for year in years:
        df = pd.concat([df, category(year, rating)], ignore_index=True)
    return df

def movies(data):
    budgetdf = numscrape.get_budget()
    df = pd.DataFrame()
    movies = data['Movie Title ']
    grosses = data['TotalGross']
    moviesref = budgetdf['MovieTitle']
    ratings = data['MPAARating']
    thrs = data['TGTheaters']

    for movie in movies:
        if movie in moviesref.values:
            ind = moviesref[moviesref == movie].index[0]
            budget = budgetdf['Budget'][ind]
            mind = movies[movies==movie].index[0]
            rating = ratings[mind]
            gross = grosses[mind]
            theater = thrs[mind]
            if budget == 'N/A' or gross == 'N/A' or theater == 'N/A':
                continue
            else:
                df = df.append(pd.Series([movie, gross, budget, rating, theater]), ignore_index = True)
    df.columns = ['Movie','Gross','Budget', 'Rating','Theater']
    return df
