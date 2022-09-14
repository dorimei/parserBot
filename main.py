import json
import sys
import requests
from bs4 import BeautifulSoup, NavigableString


def get_url():
    return sys.argv[1]


def is_valid_row(row):
    for ch in row.children:
        if not isinstance(ch, NavigableString):
            if 'class' in ch.attrs and ch["class"][0] == 'R7C1':
                return True


def int_or_default(value, default=0):
    return int(value) if value else default


result = list()

url = get_url()
response = requests.get(url)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')

tableRows = soup.find_all('tr')

for row in tableRows:
    if not is_valid_row(row):
        continue

    row_childs = row.findAll('td')

    data = {
        'order': int_or_default(row_childs[1].text),
        'snils': row_childs[2].text,
        'isOriginals': row_childs[4].text == 'Да',
        'approved': row_childs[5].text == 'Да',
        'totalScore': int_or_default(row_childs[6].text),
        'score': int_or_default(row_childs[7].text),
        'description': row_childs[8].text,
        'examScore': int_or_default(row_childs[9].text),
        'individualScore': int_or_default(row_childs[10].text),
        'isAdvantaged': row_childs[9].text == 'Да'
    }
    result.append(data)

json_string = json.dumps(result, ensure_ascii=False).encode('utf-8')
f = open("demofile2.json", "x")
f.write(json_string.decode())
f.close()
