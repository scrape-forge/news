# -*- coding: utf-8 -*-
from datetime import datetime
import re
import pytz

DATE_FORMATS = [
    '%d %m %Y %H:%M:%S',
    '%d %m %Y %H:%M',
    '%d/%m/%Y %H:%M:%S',
    '%d/%m/%Y %H:%M',
    '%d-%m-%Y %H:%M:%S',
    '%d-%m-%Y %H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
]

def to_number_of_month(month_str):
    nick_month = {'jan': 'januari', 'feb': 'februari', 'mar': 'maret', 'apr': 'april', 'mei': 'mei', 'jun': 'juni', 'jul': 'juli',
                  'agu': 'agustus', 'ags': 'agustus', 'agu/ags': 'agustus', 'sep': 'september', 'okt': 'oktober', 'nov': 'november', 'des': 'desember'}
    try:
        month_str = nick_month[month_str]
    except:
        month_str = month_str
    month_lst = [('januari', '01'), ('februari', '02'), ('maret', '03'), ('april', '04'),
                 ('mei', '05'), ('juni', '06'), ('juli', '07'), ('agustus', '08'),
                 ('september', '09'), ('oktober', '10'), ('november', '11'), ('desember', '12')]
    month = [x[1] for x in month_lst if x[0] == month_str]
    if month:
        return month[0]
    return None


def remove_tabs(content):
    content = content.replace('\t', '').replace('\r', '').strip()
    return content


def utc_to_local_month(month):
    local_month = None
    month = str(month).lower()
    month_utc = {'january': 'januari', 'february': 'februari', 'march': 'maret', 'april': 'april', 'may': 'mei', 'june': 'juni',
                 'july': 'juli', 'august': 'agustus', 'september': 'september', 'october': 'oktober', 'november': 'november', 'december': 'desember'}
    try:
        local_month = month_utc[month]
    except:
        local_month = month
    return local_month

def new_date_parse(date_string):
    if not date_string:
        return None
    
    local_format = pytz.timezone('Asia/Jakarta')
    date_string = date_string.strip()
    for date_format in DATE_FORMATS:
        try:
            date = datetime.strptime(date_string, date_format)
            return local_format.localize(date, is_dst=None).astimezone(pytz.utc)
        except ValueError:
            continue
    return None

def date_parse(date_string):
    local_format = pytz.timezone('Asia/Jakarta')
    date_lst = date_string.split(' ')
    date = None
    if len(date_lst) == 5:
        try:
            new_date_lst = date_lst[:-1]
            if len(new_date_lst[-1].split(':')) == 3:
                date_str = '{}/{}/{} {}'.format(
                    new_date_lst[0],
                    to_number_of_month(new_date_lst[1].lower()),
                    new_date_lst[2].replace(',', '').strip(),
                    new_date_lst[3].strip())

                date = datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S')
            elif len(new_date_lst[-1].split(':')) == 2:
                date_str = '{}/{}/{} {}'.format(
                    new_date_lst[0],
                    to_number_of_month(new_date_lst[1].lower()),
                    new_date_lst[2].replace(',', '').strip(),
                    new_date_lst[3].strip())

                date = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
            elif len(new_date_lst[-1].split(':')) == 1:
                new_date_lst = date_lst[1:]
                if len(new_date_lst[-1].split(':')) == 2:
                    date_str = '{}/{}/{} {}'.format(
                        new_date_lst[0],
                        to_number_of_month(new_date_lst[1].lower()),
                        new_date_lst[2].replace(',', '').strip(),
                        new_date_lst[3].strip())

                    date = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
                else:
                    date_str = '{}/{}/{} {}'.format(
                        new_date_lst[0],
                        to_number_of_month(new_date_lst[1].lower()),
                        new_date_lst[2].replace(',', '').strip(),
                        new_date_lst[3].strip())

                    date = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
        except:
            pass
    elif len(date_lst) == 6:
        date_lst = date_lst[1:-1]
        try:
            if len(date_lst[-1].split(':')) == 2:
                date_str = '{}/{}/{} {}'.format(date_lst[0],
                                                to_number_of_month(
                    date_lst[1].lower()),
                    date_lst[2].replace(',', ''), date_lst[3])
                date = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
        except:
            pass
    elif len(date_lst) == 3:
        date_lst = date_lst[0:-1]
        try:
            if "/" in date_lst[0]:
                if ":" in date_lst[1]:
                    date = datetime.strptime('{} {}'.format(date_lst[0], date_lst[1]), '%d/%m/%Y %H:%M')
        except:
            pass
    if date:
        local_time = local_format.localize(date, is_dst=None)
        utc_time = local_time.astimezone(pytz.utc)
        return utc_time
    return None


def remove_baca_juga(content):
    content = content.replace('Baca Juga', '')
    return content

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def remove_day(text):
    days = [
        "Senin", "Selasa", "Rabu", "Kamis", 
        "Jumat", "Jum'at", "Sabtu", "Minggu"
    ]

    pattern = r'\b(' + '|'.join(days) + r')\b'
    result = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return ' '.join(result.split())