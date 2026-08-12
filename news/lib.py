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


# Standardized Topic Pattern Dictionary (100% Free, runs locally in < 0.01ms)
TOPIC_PATTERNS = {
    'IKN': [r'\bikn\b', r'ibu kota nusantara', r'penajam paser'],
    'Pilkada': [r'\bpilkada\b', r'\bcagub\b', r'\bcawagub\b', r'pemilihan kepala daerah'],
    'Pemilu': [r'\bpemilu\b', r'\bcapres\b', r'\bcawapres\b', r'\bkpu\b'],
    'Suku Bunga BI': [r'suku bunga', r'bi rate', r'bank indonesia rate'],
    'Inflasi': [r'\binflasi\b', r'harga beras', r'indeks harga konsumen'],
    'Ekonomi & Bisnis': [r'\bekonomi\b', r'\bbisnis\b', r'pasar modal', r'\bihsg\b', r'rupiah', r'investasi'],
    'Politik & Hukum': [r'\bpolitik\b', r'\bhukum\b', r'\bkpk\b', r'mahkamah konstitusi', r'\bmk\b', r'\bdpr\b'],
    'Teknologi & AI': [r'\bteknologi\b', r'\btekno\b', r'artificial intelligence', r'\bai\b', r'startup', r'gadget'],
    'Otomotif': [r'\botomotif\b', r'mobil listrik', r'\bev\b', r'sepeda motor'],
    'Kesehatan': [r'\bkesehatan\b', r'bpjs', r'penyakit', r'rumah sakit', r'dokter'],
    'Olahraga': [r'sepakbola', r'\bbola\b', r'timnas', r'liga 1', r'badminton', r'olahraga'],
    'Lifestyle & Hiburan': [r'lifestyle', r'hiburan', r'selebriti', r'film', r'musik', r'kuliner']
}

IGNORE_TAGS = {
    'berita', 'terkini', 'detiknews', 'detikfinance', 'detikhot',
    'detiksport', 'detikinet', 'detikoto', 'detik travel', 'home',
    'news', 'artikel', 'update', 'utama'
}


def normalize_tags(raw_tags=None, title="", summary=""):
    """
    Standardizes messy portal tags + extracts high-value topic tags from title & summary.
    Runs locally in < 0.01ms during crawl ingestion. Batch AI tagging is handled asynchronously by tag_worker.py.
    """
    normalized = set()

    # 1. Clean existing raw tags from portal
    if raw_tags:
        if isinstance(raw_tags, str):
            raw_tags = [raw_tags]
        for tag in raw_tags:
            clean = tag.strip().lower()
            if clean and clean not in IGNORE_TAGS and len(clean) > 2:
                normalized.add(tag.strip().title())

    # 2. Rule-based topic extraction from title & summary
    search_text = f"{title} {summary}".lower()
    for topic, patterns in TOPIC_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, search_text):
                normalized.add(topic)
                break

    return sorted(list(normalized))


CATEGORY_MAPPING = {
    # 1. Ekonomi & Bisnis
    'ekonomi': 'Ekonomi & Bisnis',
    'economy': 'Ekonomi & Bisnis',
    'ekonomi bisnis': 'Ekonomi & Bisnis',
    'bisnis': 'Ekonomi & Bisnis',
    'finance': 'Ekonomi & Bisnis',
    'finansial': 'Ekonomi & Bisnis',
    'market update': 'Ekonomi & Bisnis',
    'inspirasi bisnis': 'Ekonomi & Bisnis',
    'energi': 'Ekonomi & Bisnis',
    'pertanian': 'Ekonomi & Bisnis',
    'kripto': 'Ekonomi & Bisnis',

    # 2. Politik & Hukum
    'politik': 'Politik & Hukum',
    'nasional': 'Politik & Hukum',
    'kilas-kementerian': 'Politik & Hukum',
    'kasuistika': 'Politik & Hukum',

    # 3. Teknologi & Sains
    'teknologi': 'Teknologi & Sains',
    'tekno': 'Teknologi & Sains',
    'techno': 'Teknologi & Sains',
    'sains': 'Teknologi & Sains',

    # 4. Olahraga
    'sport': 'Olahraga',
    'bola': 'Olahraga',
    'sepak bola dunia': 'Olahraga',
    'sepak bola indonesia': 'Olahraga',
    'sepakbola dunia': 'Olahraga',
    'liga champion': 'Olahraga',
    'liga italia': 'Olahraga',
    'liga spanyol': 'Olahraga',
    'liga indonesia': 'Olahraga',
    'motogp': 'Olahraga',
    'sport lain': 'Olahraga',
    'netting': 'Olahraga',

    # 5. Internasional
    'international': 'Internasional',
    'internasional': 'Internasional',
    'dunia': 'Internasional',

    # 6. Regional & Daerah
    'regional': 'Regional & Daerah',
    'berita daerah': 'Regional & Daerah',
    'daerah': 'Regional & Daerah',
    'megapolitan': 'Regional & Daerah',
    'metro': 'Regional & Daerah',
    'metropolitan': 'Regional & Daerah',
    'nusantara': 'Regional & Daerah',
    'surabaya raya': 'Regional & Daerah',

    # 7. Gaya Hidup & Edukasi
    'lifestyle': 'Gaya Hidup & Edukasi',
    'life': 'Gaya Hidup & Edukasi',
    'fashion': 'Gaya Hidup & Edukasi',
    'beauty': 'Gaya Hidup & Edukasi',
    'food': 'Gaya Hidup & Edukasi',
    'kuliner': 'Gaya Hidup & Edukasi',
    'travel': 'Gaya Hidup & Edukasi',
    'zodiak': 'Gaya Hidup & Edukasi',
    'mom and kids': 'Gaya Hidup & Edukasi',
    'edukasi': 'Gaya Hidup & Edukasi',
    'pendidikan': 'Gaya Hidup & Edukasi',

    # 8. Hiburan & Seleb
    'entertainment': 'Hiburan & Seleb',
    'showbiz': 'Hiburan & Seleb',
    'seleb': 'Hiburan & Seleb',
    'hiburan': 'Hiburan & Seleb',
    'tv scoop': 'Hiburan & Seleb',
    'hot gossip': 'Hiburan & Seleb',
    'hot issue': 'Hiburan & Seleb',

    # 9. Kesehatan
    'kesehatan': 'Kesehatan',
    'health': 'Kesehatan',

    # 10. Religi & Humaniora
    'islam digest': 'Religi & Humaniora',
    'islam nusantara': 'Religi & Humaniora',
    'ihram': 'Religi & Humaniora',
    'filantropi khazanah': 'Religi & Humaniora',

    # Ignored portal generic labels
    'terkini': 'General',
    'berita': 'General',
    'news': 'General',
    'top news': 'General',
    'foto': 'General',
}


def normalize_category(raw_category: str) -> str:
    """
    Normalizes messy raw portal categories into clean 10 Master Categories.
    Example: 'Ekonomi Bisnis' -> 'Ekonomi & Bisnis', 'tekno' -> 'Teknologi & Sains'.
    """
    if not raw_category:
        return 'General'
    
    clean = raw_category.strip().lower()
    if clean in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[clean]

    # Partial matching for common sub-categories
    if 'ekonomi' in clean or 'bisnis' in clean or 'finance' in clean:
        return 'Ekonomi & Bisnis'
    if 'politik' in clean or 'hukum' in clean:
        return 'Politik & Hukum'
    if 'tekno' in clean or 'sains' in clean:
        return 'Teknologi & Sains'
    if 'sport' in clean or 'bola' in clean:
        return 'Olahraga'
    if 'sehat' in clean or 'health' in clean:
        return 'Kesehatan'
    if 'hiburan' in clean or 'seleb' in clean:
        return 'Hiburan & Seleb'

    return raw_category.strip().title()





import html
from w3lib.html import remove_tags

PORTAL_SUFFIX_RE = re.compile(
    r'\s*[-|–]\s*(detiknews|detikfinance|detikhot|detikinet|detiksport|detikoto|detikfood|detikhealth|wolipop|kompas\.com|antaranews|liputan6\.com|tempo\.co|republika\.co\.id|sindonews|okezone|jawapos|suara\.com|merdeka\.com).*$',
    re.IGNORECASE
)

DATELINE_RE = re.compile(
    r'^\s*([A-Z\s]+,\s*(KOMPAS\.com|ANTARA|Liputan6\.com|Detikcom|Tempo\.co)\s*[-–—]\s*|ANTARA\s*[-–—]\s*)',
    re.IGNORECASE
)

BACA_JUGA_RE = re.compile(r'baca juga:.*$', re.IGNORECASE)


def clean_text(text: str) -> str:
    """
    Cleans raw Indonesian text:
    - Unescapes HTML entities (&amp;, &quot;, &#39;)
    - Removes HTML tags
    - Replaces non-breaking spaces (\xa0) and normalizes whitespace
    """
    if not text:
        return ""
    text = html.unescape(text)
    text = remove_tags(text)
    text = text.replace('\xa0', ' ').replace('\t', ' ').replace('\r', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_headline(title: str) -> str:
    """Cleans headlines by removing portal suffixes, watermarks, and html noise."""
    text = clean_text(title)
    text = PORTAL_SUFFIX_RE.sub('', text).strip()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
    return text


def clean_summary(summary: str, max_chars: int = 500) -> str:
    """Cleans summaries by removing datelines ('JAKARTA, KOMPAS.com - '), 'Baca Juga', and truncating."""
    text = clean_text(summary)
    text = DATELINE_RE.sub('', text).strip()
    text = BACA_JUGA_RE.sub('', text).strip()
    return text[:max_chars].strip()