import os
from tinkoff_voicekit_client import ClientSTT
from datetime import datetime
import soundfile as sf
import psycopg2

API_KEY = ""
SECRET_KEY = ""

negative_words = ["нет", "неудобно", "отказ"]


def get_path():
    _path = input("Файл путь к .wav файлу: ").replace("/", "//").replace("\\", "//")
    if not os.path.exists(_path):
        print("Файл не найден")
        get_path()
    else:
        try:
            sf.SoundFile(_path)
        except:
            open("error-log.txt", "a").write(datetime.now().strftime("%d/%m/%Y\t%I:%M:%S\t") + "WAV file error\n")
            quit()
        return _path


def get_phone():
    _phone = input("Номер телефона: ").replace("-", "").replace("+7", "8").replace("", "")
    if len(_phone) != 11:
        print("Телефон не подходит")
        get_phone()
    else:
        return _phone


def get_bool_db():
    _bool_db = input("Записи в базу данных (Y/N): ")
    if _bool_db.upper() == "Y":
        return True
    elif _bool_db.upper() == "N":
        return False
    else:
        print("Введите Y или N")
        get_bool_db()


def get_stage():
    _stage = input("Этап распознавания (1/2): ")
    if _stage == "1":
        return 1
    elif _stage == "2":
        return 2
    else:
        print("Введите 1 или 2")
        get_stage()


# На вход из консоли принимает файл путь к .wav файлу, номер телефона, флаг необходимости записи в базу данных,
# этап распознавания
path = get_path()
phone = get_phone()
bool_db = get_bool_db()
stage = get_stage()

# Отправляет файл на распознавание
try:
    stt_results = ClientSTT(API_KEY, SECRET_KEY). \
        recognize(path, {"encoding": "LINEAR16", "sample_rate_hertz": 8000, "num_channels": 1})
except:
    open("error-log.txt", "a").write(datetime.now().strftime("%d/%m/%Y\t%I:%M:%S\t") + "STT error\n")
    quit()

# Обрабатывает результат:
if stage == 1:  # Если первый этап, то
    result = "человек"  # если человек, возвращает 1
    for stt_result in stt_results:
        for alternative in stt_result["alternatives"]:
            if alternative["transcript"] == "вас приветствует автоответчик оставьте сообщение после сигнала":
                result = "АО"  # если в аудио записи распознан автоответчик возвращает 0
elif stage == 2:  # Если второй этап, то
    result = "положительно"  # если положительные (“говорите”, “да конечно” и т.п.) то возвращает 1
    for stt_result in stt_results:
        for alternative in stt_result["alternatives"]:
            for word in alternative["transcript"].split(" "):
                if word in negative_words:
                    result = "отрицательно"  # если в ответе есть отрицательные слова (“нет”, “неудобно” и т.п.), то 0

# Пишет результат распознавания в лог-файл в формате: дата, время, уникальный id, результат действия (АО или человек
# для 1 этапа и положительно или отрицательно для 2го этапа), номер телефона, длительность аудио, результат
# распознавания
records_to_insert = [
    datetime.now().date(),  # дата
    datetime.now().time(),  # время
    str(len(open("log.txt", "r").readlines()) + 1),  # уникальный id
    result,  # результат действия
    int(phone),  # номер телефона
    len(sf.SoundFile(path)) / sf.SoundFile(path).samplerate,  # длительность аудио
    str(stt_results)  # результат распознавания
]

with open("log.txt", "a") as log:
    for record in records_to_insert:
        log.write(str(record) + "\t")
    log.write("\n")

# Если выставлен соответствующий флаг, то пишет результат в базу данных в том же формате что и в лог-файл. СУБД Postgres
if bool_db:
    try:
        """
        CREATE TABLE public.stt_table
        (
            date date,
            "time" time without time zone,
            id bigint NOT NULL,
            result character varying COLLATE pg_catalog."default",
            phone bigint,
            audio_len double precision,
            text text COLLATE pg_catalog."default",
            CONSTRAINT "TABLE_pkey" PRIMARY KEY (id)
        )
        WITH (
            OIDS = FALSE
        )
        TABLESPACE pg_default;
        
        ALTER TABLE public.stt_table
            OWNER to postgres;
    """
        connection = psycopg2.connect(user="postgres", password="rootroot",
                                      host="localhost", port="5433", database="database")
        cursor = connection.cursor()
        query = "INSERT INTO stt_table (date, time, id, result, phone, audio_len, text) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(query, records_to_insert)
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        print("Database error: {}".format(e))
        open("error-log.txt", "a").write(datetime.now().strftime("%d/%m/%Y\t%I:%M:%S\t") + "Database error: {}\n".format(e))
        quit()


# Удаляет .wav файл
os.remove(path)
