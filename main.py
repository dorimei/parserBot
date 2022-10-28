import json
import requests
from bs4 import BeautifulSoup

links = {
    "Информационные системы и технологии, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o230400.htm",
    "Стандартизация и метрология, контракт": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OK/o221700k.htm",
    "Экология и природопользование, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o022000.htm",
    "Картография и геоинформатика, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o021300.htm",
    "Информационная безопасность, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o090900.htm",
    "Приборостроение, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o200100.htm",
    "Оптотехника, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o200400.htm",
    "Землеустройство и кадастры, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o120700.htm",
    "Геодезия и дистанционное зондирование, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o120100.htm",
    "Фотоника и оптоинформатика, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o200300.htm",
    "Боеприпасы и взрыватели, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o170100.htm",
    "Прикладная геодезия, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o120401.htm",
    "Горное дело, бюджет": "https://sgugit.ru/upload/to-the-entrant/announcements-reception-of-2020/lists-of-students/ranking-lists-of-applicants/OB/o130400.htm",

}

students = dict()


def update_all_links_cache():
    students.clear()
    for key, value in links.items():
        update_one_link(value, key)


def update_one_link(link_url, link_name):
    res = requests.get(link_url)
    soup = BeautifulSoup(res.content, "lxml")
    for item in soup.find_all(class_="R0")[5:]:
        row_fields = item.text.split("\n")
        snils = row_fields[3]
        studentData = {'order': int(row_fields[2]), 'snils': snils, 'consent': row_fields[6] == 'Да',
                   'isOriginals': row_fields[5] == 'Да', 'totalScore': int(row_fields[7]), 'score': int(row_fields[8]),
                   'description': row_fields[9], 'isAdvantaged': row_fields[16] == 'Да'}

        if snils not in students.keys():
            students[snils] = {}

        students[snils][link_name] = studentData


def find_student_data(snils):
    return students[snils]


update_all_links_cache()


with open('db.json', 'w', encoding="utf-8") as file:
    jsonStr = json.dumps(students, ensure_ascii=False, indent=4)
    file.write(jsonStr)