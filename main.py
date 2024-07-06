import requests
import psycopg2
import re
import os

db_config = {
    'dbname': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '12345'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

def clean_html(raw_html):
    if raw_html is None:
        return ""                                    # Возвращаем пустую строку, если входное значение None
    cleanr = re.compile('<.*?>')                     # Регулярное выражение для поиска HTML-тегов
    cleantext = re.sub(cleanr, '', raw_html)         # Заменяем все найденные теги на пустую строку
    return cleantext

def create_table(conn):                              #Создает таблицу
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT to_regclass('public.vacancies')")
        table_exists = cursor.fetchone()[0]
        create_table_query = """
            CREATE TABLE IF NOT EXISTS vacancies (
                id SERIAL PRIMARY KEY,
                vacancy VARCHAR(200),
                company VARCHAR(200),
                city VARCHAR(50),
                salary VARCHAR(50),
                experience VARCHAR(50),
                schedule VARCHAR(200),
                skills TEXT,
                url VARCHAR(200) UNIQUE
            )
        """
        cursor.execute(create_table_query)
        if not table_exists:
            print("Таблица 'vacancies' успешно создана.")
    except Exception as e:
        print(f"Ошибка при создании таблицы: {e}")
    finally:
        cursor.close()

def truncate_table(conn):                  # Очищает таблицу, если в базе данных больше 2000 вакансий
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT to_regclass('public.vacancies')")
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM vacancies")
            count = cursor.fetchone()[0]
            if count >= 2000: 
                truncate_table_query = "TRUNCATE TABLE vacancies RESTART IDENTITY"
                cursor.execute(truncate_table_query)
                print("Таблица 'vacancies' была очищена, так как содержала 2000 или более записей.")
                conn.commit()
        else:
            print("Таблица 'vacancies' не существует.")
    except Exception as e:
        print(f"Ошибка при проверке/очистке таблицы: {e}")
    finally:
        cursor.close()
    

def insert_vacancy(conn, vacancy_name, company_name, city, salary, experience_required, schedule, skills, vacancy_url):       #Проверка вакансий на дубликаты в таблице
    cursor = conn.cursor()
    # Проверяем, существует ли уже такая вакансия
    cursor.execute("SELECT id FROM vacancies WHERE url = %s", (vacancy_url,))
    if cursor.fetchone() is None:
        insert_query = """
            INSERT INTO vacancies (vacancy, company, city, salary, experience, schedule, skills, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (vacancy_name, company_name, city, salary, experience_required, schedule, skills, vacancy_url))
        conn.commit()
    cursor.close()
    

def get_vacancies(keyword, page, per_page=20):           #Получает вакансии по ключевому слову с сайта hh.ru
    url = "https://api.hh.ru/vacancies"                        
    params = {
        "text": keyword,                                 #Ключевое слово для поиска
        "area": None,                                    #Город (1 - Москва, None - разные города)
        "per_page": per_page,                            #Количество результатов на странице
        "page": page                                     #Номер страницы результатов поиска
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def analyze_vacancies(conn):                             #Анализирует и выводит общее количество вакансий в базе данных
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM vacancies"
    cursor.execute(query)
    total_vacancies = cursor.fetchone()[0]
    print(f"Общее количество вакансий в базе данных: {total_vacancies}")
    cursor.close()

def search_vacancies_by_keyword(keyword, city=None, salary=None, experience=None, schedule=None, skills=None):      #Ищет вакансии по ключевому слову и дополнительным параметрам в базе данных (city, salary, experience, schedule: дополнительные параметры фильтрации). Возвращает список найденных вакансий.
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    query = """
        SELECT * FROM vacancies
        WHERE LOWER(vacancy) LIKE LOWER(%s)
    """
    params = ['%' + keyword + '%']

    if city:
        query += " AND LOWER(city) = LOWER(%s)"
        params.append(city)
    if salary:
        query += " AND LOWER(salary) LIKE LOWER(%s)"
        params.append('%' + salary + '%')
    if experience:
        query += " AND LOWER(experience) = LOWER(%s)"
        params.append(experience)
    if schedule:
        query += " AND LOWER(schedule) = LOWER(%s)"
        params.append(schedule)
    if skills:
        skills_list = [skill.strip() for skill in skills.split(',')]
        query += " AND ("
        for i in range(len(skills_list)):
            query += "LOWER(skills) LIKE LOWER(%s)"
            params.append('%' + skills_list[i] + '%')
            if i < len(skills_list) - 1:
                query += " OR "
        query += ")"

    cursor.execute(query, params)
    vacancies = cursor.fetchall()
    cursor.close()
    conn.close()
    return vacancies

def count_vacancies(keyword, city=None, salary=None, experience=None, schedule=None, skills=None):      #Считает количество вакансий, соответствующих заданным критериям поиска в базе данных. Возвращает количество вакансий.
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    query = """
        SELECT COUNT(*) FROM vacancies
        WHERE LOWER(vacancy) LIKE LOWER(%s)
    """
    params = ['%' + keyword + '%']

    if city:
        query += " AND LOWER(city) = LOWER(%s)"
        params.append(city)
    if salary:
        query += " AND LOWER(salary) LIKE LOWER(%s)"
        params.append('%' + salary + '%')
    if experience:
        query += " AND LOWER(experience) = LOWER(%s)"
        params.append(experience)
    if schedule:
        query += " AND LOWER(schedule) = LOWER(%s)"
        params.append(schedule)
    if skills:
        skills_list = [skill.strip() for skill in skills.split(',')]
        query += " AND ("
        for i in range(len(skills_list)):
            query += "LOWER(skills) LIKE LOWER(%s)"
            params.append('%' + skills_list[i] + '%')
            if i < len(skills_list) - 1:
                query += " OR "
        query += ")"


    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count

    
def main(keyword):                                       #Основная функция, управляющая процессом парсинга и обработки данных.
    try:
        conn = psycopg2.connect(**db_config)
        print("Успешное подключение к базе данных")
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return
    
    truncate_table(conn)
    create_table(conn)
    
    for page in range(30):
        vacancies_info = get_vacancies(keyword, page=page)
        for item in vacancies_info.get("items", []):
            vacancy_name = item.get("name")
            company_name = item.get("employer", {}).get("name")
            city = item.get("area", {}).get("name")
            experience_required = item.get("experience", {}).get("name", "Опыт работы не указан")
            salary_info = item.get("salary")
            if salary_info:
                salary_from = salary_info.get("from")
                salary_to = salary_info.get("to")
                currency = salary_info.get("currency")
                salary = f"от {salary_from} до {salary_to} {currency}" if salary_from and salary_to else "з/п не указана"
            else:
                salary = "з/п не указана"
            schedule = item.get("schedule", {}).get("name", "Формат работы не указан")
            skills_raw = item.get("snippet", {}).get("requirement", "Навыки не указаны")
            skills = clean_html(skills_raw)
            vacancy_url = item.get("alternate_url")
            insert_vacancy(conn, vacancy_name, company_name, city, salary, experience_required, schedule, skills, vacancy_url)

    analyze_vacancies(conn)

    conn.close()


def run_parser():                             #Запускает парсер, вызывая функцию main()
    print("Запуск парсера...")
    main()

if __name__ == "__main__":
    run_parser()                            #Запускает парсер, вызывая функцию main()

