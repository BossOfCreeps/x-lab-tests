"""
Нужно составить sql запрос, который выведет: дату(можно задать промежуток дат), результат распознавания (АО, человек,
положительно-отрицательно), далее для каждого результата распознавания: кол-во за каждую дату (если указан промежуток),
длительность всех аудио, проект и сервер.
"""
from datetime import datetime
from pprint import pprint

import psycopg2


def get_range():
    _range = input("Дата или промежуток (Д/П): ")
    if _range.upper() == "П":
        return True
    elif _range.upper() == "Д":
        return False
    else:
        print("Введите Д (дата) или П (промежуток дат)")
        get_range()


def get_date(param=""):
    __date = input("Введите {}дату в формате YYYY MM DD: ".format(param))
    try:
        __date = __date.split(" ")
        return datetime(int(__date[0]), int(__date[1]), int(__date[2])).date()
    except:
        print("Ошибка")
        get_date(param)


is_range = get_range()

try:
    connection = psycopg2.connect(user="postgres", password="rootroot",
                                  host="localhost", port="5433", database="database")
    cursor = connection.cursor()
    if is_range:
        s_date = get_date("первую ")
        f_date = get_date("вторую ")

        cursor.execute("""SELECT date, result FROM stt_table WHERE date >'{}' and date<'{}';""".format(s_date, f_date))
        print("Дата \t\t\t результат распознавания (АО, человек, положительно-отрицательно)")
        for record in cursor.fetchall():
            print(record[0].strftime("%d/%m/%Y"), "\t\t", record[1])
        cursor.execute("SELECT stt_table.date, count(stt_table.id), sum(stt_table.audio_len), project.name, server.name "
                       "FROM stt_table, project, server "
                       "WHERE date>'{}' and date<'{}' GROUP BY date; ".format(s_date, f_date))
        print("Дата \t кол-во \t длительность \t проект \t сервер")
        for record in cursor.fetchall():
            print(record[0].strftime("%d/%m/%Y"), "\t", record[1], "\t", record[2], "\t", record[3], "\t", record[4])
    else:
        _date = get_date()
        cursor.execute("""SELECT date, result FROM stt_table WHERE date = '{}';""".format(_date))
        print("Дата \t\t\t результат распознавания (АО, человек, положительно-отрицательно)")
        for record in cursor.fetchall():
            print(record[0].strftime("%d/%m/%Y"), "\t\t", record[1])
except:
    print("Ошибка базы данных")
    quit()
