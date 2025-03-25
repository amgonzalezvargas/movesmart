# app.py
from flask import Flask, render_template, request
import os
from utils import get_countries, get_country_items, get_job_areas, search_jobs


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/countries')
def countries():
    countries_data = get_cheapest_countries()
    return render_template('countries.html', countries=countries_data)

@app.route('/about')
def about():
    return render_template('about.html')


from flask import request
from utils import get_countries, get_country_items

@app.route('/search', methods=['GET', 'POST'])
def search_country():
    countries = get_countries()
    selected_country = None
    items = []
    if request.method == 'POST':
        selected_country = request.form.get('country')
        items = get_country_items(selected_country)
    return render_template('search_country.html', countries=countries, selected_country=selected_country, items=items)

@app.route('/search_job', methods=['GET', 'POST'])
def search_job():
    countries = get_countries()
    job_areas = get_job_areas()
    results = []
    sort_by = request.args.get('sort_by', 'job_title')
    sort_dir = request.args.get('sort_dir', 'asc')
    
    if request.method == 'POST':
        country = request.form.get('country', '')
        area = request.form.get('area', '')
        keywords = request.form.get('keywords', '')
        
        results = search_jobs(country, area, keywords, sort_by, sort_dir)
        
    return render_template('search_job.html', 
                          countries=countries, 
                          job_areas=job_areas, 
                          results=results,
                          sort_by=sort_by,
                          sort_dir=sort_dir)



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
