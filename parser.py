import json
import requests
from bs4 import BeautifulSoup

links = {}
students = dict()


def init():
    with open("links.txt", 'r', encoding='UTF-8') as file:
        while line := file.readline().rstrip():
            row = line.split(";")
            links[row[0]] = row[1]


def update_all_links_cache():
    students.clear()
    for key, value in links.items():
        update_one_link(value, key)
    with open('db.json', 'w', encoding="utf-8") as file:
        jsonStr = json.dumps(students, ensure_ascii=False, indent=4)
        file.write(jsonStr)


def update_one_link(link_url, link_name):
    res = requests.get(link_url)
    soup = BeautifulSoup(res.content, "lxml")
    for item in soup.find_all(class_="R0")[5:]:
        row_fields = item.text.split("\n")
        snils = row_fields[3]
        studentData = {'order': int(row_fields[2]), 'snils': snils, 'consent': row_fields[6] == 'Да',
                       'isOriginals': row_fields[5] == 'Да', 'totalScore': int(row_fields[7]),
                       'score': int(row_fields[8]),
                       'description': row_fields[9], 'isAdvantaged': row_fields[16] == 'Да'}

        if snils not in students.keys():
            students[snils] = {}

        students[snils][link_name] = studentData


def find_student_data(snils):
    return students[snils]


init()
