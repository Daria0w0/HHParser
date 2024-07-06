from flask import Flask, request, render_template, redirect, url_for
from main import search_vacancies_by_keyword, count_vacancies, main
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'keyword' in request.form:
            keyword = request.form.get('keyword')
            main(keyword)
            return redirect(url_for('search_results', keyword=keyword))
        elif 'all_vacancies' in request.form:
            return redirect(url_for('all_vacancies'))
    return render_template('index.html')

@app.route('/search_results/<keyword>')
def search_results(keyword):
    city = request.args.get('city', '')
    salary = request.args.get('salary', '')
    experience = request.args.get('experience', '')
    schedule = request.args.get('schedule', '')
    skills = request.args.get('skills', '')

    vacancies = search_vacancies_by_keyword(keyword, city=city, salary=salary, experience=experience, schedule=schedule, skills=skills)
    total_vacancies = count_vacancies(keyword, city, salary, experience, schedule, skills)

    return render_template('search_results.html', vacancies=vacancies, total_vacancies=total_vacancies, keyword=keyword, city=city, salary=salary, experience=experience, schedule=schedule, skills=skills)

@app.route('/all_vacancies')
def all_vacancies():
    city = request.args.get('city', '')
    salary = request.args.get('salary', '')
    experience = request.args.get('experience', '')
    schedule = request.args.get('schedule', '')
    skills = request.args.get('skills', '')
    
    vacancies = search_vacancies_by_keyword('', city=city, salary=salary, experience=experience, schedule=schedule, skills=skills)
    total_vacancies = len(vacancies)

    return render_template('all_vacancies.html', vacancies=vacancies, total_vacancies=total_vacancies, city=city, salary=salary, experience=experience, schedule=schedule, skills=skills)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)