# read and analysis first 200 pages of https://www.shab.ir then make ML model to predict
#   price houses

import requests
from bs4 import BeautifulSoup
import mysql.connector
import re
import pandas as pd


# find all houses in a page and analysis their data then call insert_to_database()
def find_items(soup):
    data = soup.find_all('small', attrs={'class': 'mF-kH'})
    house = soup.find_all('div', attrs={'class': "_1xM_0"})

    for i, d in enumerate(data):
        kind, room, city_state = d.text.strip().split('.')
        kind = kind.strip()
        room = int(room.split()[0].strip())
        state, city = [x.strip() for x in city_state.split('،')]
        a = list(house_info('https://www.shab.ir' + house[i].find('a')['href']))
        price = a[-1]
        a = a[0:-1] + [kind, room, city, state, price]

        insert_to_database(a)


# read first 200 pages of https://www.shab.ir
def load_pages():
    for i in range(1, 201):
        url = 'https://www.shab.ir/search?phrase=&page=' + str(i)
        html = requests.get(url)
        soup = ''
        if html.status_code == 200:
            soup = BeautifulSoup(html.text, 'html.parser')
        find_items(soup)


# read every house page and scrape additional data (such as capacity, equipment, ...)
def house_info(url):
    html = requests.get(url)
    soup = ''
    if html.status_code == 200:
        soup = BeautifulSoup(html.text, 'html.parser')
    data = soup.find_all('div', attrs={'wrap': 'Wrap'})

    price_temp = soup.find('p', attrs={'class': 'Ckx0h _-9HBW'}).text
    price = ''
    for p in price_temp.split('٫'):
        price += p
    price = int(price)

    j = 0
    spaces = []
    for d in data[3]:
        spaces.append(int((re.findall(r'[0-9]+', d.text))[0]))
        j += 1
        if j == 2:
            break

    capacity = soup.find('p', attrs={'class': '_1FWax'}).text
    extra = soup.find('div', attrs={'class': '_2A2J4'}).find('div', attrs={'wrap': 'Wrap'}).text
    capacity = int(re.findall('[0-9]+', capacity)[0])
    extra = int(re.findall('[0-9]+', extra)[0])

    equipment = 17 - len(soup.find_all('li', attrs={'class': '_2HNc4 _2HKby'}))
    code = url.split('/')[-1]
    return code, spaces[0], spaces[1], equipment, capacity, extra, price


# insert data in database if doesn't exist before
def insert_to_database(data):
    cnx = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='shab')
    cursor = cnx.cursor()
    cursor.execute('SELECT EXISTS (SELECT * FROM houses2 WHERE id=\'{}\')'.format(data[0]))
    exists = bool(cursor.fetchone()[0])
    cnx.close()

    cnx = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='shab')
    cursor = cnx.cursor()
    if not exists:
        query = 'INSERT INTO houses2 VALUES (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',' \
                '\'{}\');'.format(data[0], data[1], data[2], data[3],
                                  data[4], data[5], data[6], data[7], data[8], data[9], data[10])
    else:
        query = 'UPDATE houses2 SET price = \'{}\' WHERE id=\'{}\''.format(data[-1], data[0])
    cursor.execute(query)
    cnx.commit()
    cnx.close()


def read_database():
    cnx = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='shab')
    cursor = cnx.cursor()
    query = 'SELECT * FROM houses2;'
    cursor.execute(query)
    arr = []
    for c in cursor:
        arr.append(list(c))
    cnx.close()
    return pd.DataFrame(arr, columns=['id', 'area', 'space', 'equipment', 'type', 'room', 'city', 'state',
                                      'price', 'capacity', 'extra'])


load_pages()
dataframe = read_database()
dataframe.to_csv('houses.csv')
