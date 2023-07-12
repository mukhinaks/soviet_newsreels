# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 12:00:47 2021

@author: Ksenia Mukhina
"""
from bs4 import BeautifulSoup
import requests
import time
import json

netfilm_url = 'https://www.net-film.ru/'
langs = ['', 'en/']

output_folder = 'data/'

#Extract general information about newsreel issues: ID, link, title, link to video
def get_newsreel_issues(base_url, pages):    
    news_film = {}
    for page_number in range(pages + 1):
        page = requests.get(base_url  + str(page_number))
        soup = BeautifulSoup(page.text)
        
        elements = soup.find_all(class_= 'newsreel-unit')
        
        for elem in elements:
            if elem =='Ошибка':
                continue
            elif elem == 'Error':
                continue
            
            news = {}
            news['ID'] = int(elem.find('input').get('value'))
            news['link'] = elem.find('a').get('href')
            news['title'] = elem.find('h2').text.strip()
            news['img'] = 'https:' + elem.find('img').get('src')
            news['media_link'] = news['img'][:-5] + '.mp4'    
            
            news_film[news['ID']] = news
            
            
    return news_film      
        
daily_news_link = 'newsreels-daily-news-page-'
base_url = netfilm_url + daily_news_link
pages = 89

newsreel_issues = get_newsreel_issues(base_url, pages)

#Extract metadata of digitised newsreel issues
def get_all_metadata(news):
    news_page = requests.get(netfilm_url + news['link'])
    page_soup = BeautifulSoup(news_page.text)
    
    upd_info = page_soup.find(class_="film-detailed") 

    authors = {}
    for person in upd_info.find(class_="authors").find_all('div'):
        if person.find('a'):
            authors[person.find('span').text] = {}
            authors[person.find('span').text]['link'] = person.find('a').get('href')
            authors[person.find('span').text]['name'] = person.find('a').text
        else:
            auth = person.find_all('span')
            
            authors[auth[0].text] = {}
            if len(auth) >= 1:
                authors[auth[0].text] ['name'] = []
                for at in auth[1:]:
                     authors[auth[0].text] ['name'].append(at.text)
                
            else:
                authors[auth[0].text]['name'] = [auth[0].text]
        
        
            
    news['authors'] = authors
    news['annotation'] = upd_info.find(class_="annotations").text
    
    imgs = []
    if upd_info.find(class_='frameset'):
        imgs_html = upd_info.find(class_='frameset').find_all('span')           
        
        for img in imgs_html:
            if img.find('img'):
                tmp = {}
                tmp['link'] = img.find('img').get('src')
                tmp['data-in'] = int(img.find('span').get('data-in'))
                imgs.append(tmp)
        
    news['images'] = imgs
    
    outline = []
    for item in upd_info.find('div', class_="play-area").find_all('p'):
        try:
            d = {}
            d['data-in'] = int(item.get('data-in'))
            d['footage'] = item.get('data-footage')
            d['description'] = item.text
            outline.append(d)
        except:
            try:
                if len(item.parent.find_all('p')) > 1:
                    news['place'] = [x.text.strip() for x in item.parent.find_all('p') if 'class' not in x.attrs]
                else:
                    news['year'] = item.parent.find(text=True, recursive=False)
            except:
                pass
    
    news['outline'] = outline
    
    if upd_info.find(class_='im-collection'):
        if upd_info.find(class_='im-collection').find(class_ = 'nf-player__playlist-name'):
            news['duration'] = upd_info.find(class_='im-collection').find(class_ = 'nf-player__playlist-name').find('span').text
        else:
            news['duration'] = ''
            
        if upd_info.find(class_='im-collection').find(class_ = 'nf-player__playlist-quality'):
            news['quality'] = upd_info.find(class_='im-collection').find(class_ = 'nf-player__playlist-quality').find('span').text.strip()
        else:
            news['quality'] = 'Not Digitized'
    else:
        news['quality'] = 'Not Digitized'
        news['duration'] = ''

for k, v in newsreel_issues.items():
    print('processing', k)
    get_all_metadata(v)
    
    time.sleep(2)
    
with open(daily_news_link[:-6] + '.json', 'w') as f: 
    json.dump(newsreel_issues, f)  
   
    
# Reformat data to csv
import re
import pandas as pd 

all_data = []

for i, k in enumerate(newsreel_issues.keys()):
    print(i + 1, '/', len(newsreel_issues))
    v = newsreel_issues[k]
  
    object_news = {}
    object_news['ID'] = v['ID']
    object_news['Year'] = int(re.findall('(\d{4})', v['title'])[0])
    
    split_list = v['title'].split()
    if "№" in split_list:
        issue_id = split_list.index("№") + 1
        object_news['Issue'] = split_list[issue_id]
    else:
        object_news['Issue'] = -1
    object_news['Title'] = v['title']   
    
    object_news['Duration'] = v['duration']
    
    object_news['Annotation'] = ' '.join(v['annotation'].split()[1:]) if v['annotation'] != '\n' else ''
    
    object_news['Media'] = v['media_link']
    object_news['Link'] = v['link']
    
    if 'Студия' in v['authors']:
        object_news['Author_studio'] = v['authors']['Студия']['name']
    else:
        object_news['Author_studio'] = None
        
    if 'Режиссер:' in v['authors']:
        object_news['Author_director'] = v['authors']['Режиссер:']['name']
    else:
        object_news['Author_director'] = None
        
    if 'Другие авторы:' in v['authors']:
        object_news['Author_others'] = v['authors']['Другие авторы:']['name']
    else:
        object_news['Author_others'] = None
        
    if 'Операторы:' in v['authors']:
        object_news['Author_cinematography'] = v['authors']['Операторы:']['name']
    else:
        object_news['Author_cinematography'] = None
        
    if 'Авторы текстов:' in v['authors']:
        object_news['Author_text'] = v['authors']['Авторы текстов:']['name']
    else:
        object_news['Author_text'] = None
        
    if 'Авторы сценария:' in v['authors']:
        object_news['Author_script'] = v['authors']['Авторы сценария:']['name']
    else:
        object_news['Author_script'] = None
    
    descr = ''
    descr_en = ''
    descr_trans = ''
    for i, elem in enumerate(v['outline']):
        tmp = {k:val for k,val in object_news.items()}
        tmp['Timestamp'] = elem['data-in']
        tmp ['Description'] = elem['description']
        
        descr += str(elem['data-in']) + ": " +  elem['description'] + '\n'
    
    object_news['Outline'] = descr
    all_data.append(object_news)
    
df = pd.DataFrame(all_data)
df = df[['ID', 'Year', 'Issue', 'Title', 'Duration',
       'Annotation', 
       'Outline', 
       'Author_studio',
       'Author_director', 'Author_others', 'Author_cinematography',
       'Author_text', 'Author_script', 
       'Media', 'Link',]]

csv_name = '_'.join(daily_news_link.split('-')[1:-2])
df.to_csv( csv_name + '.csv', encoding='utf-8-sig')    