# app.py
from flask import Flask, render_template, request
import os
import re
from utils import get_cities, get_city_items, compare_city_items, get_countries, create_salaries_chart, get_job_areas, search_jobs_by_country, create_affordability_heatmap
from utils import search_jobs_by_keywords, get_city_items_for_basket, get_reference_basket_cost
from utils import get_countries, create_salaries_chart, get_job_areas, search_jobs_by_country, create_affordability_heatmap
from utils import search_jobs_by_keywords



app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/compare_cities', methods=['GET', 'POST'])
def compare_cities():
    # Get all cities for the dropdowns
    cities = get_cities()
    
    # Initialize variables
    left_city = None
    right_city = None
    left_city_display = {"country": "", "city": ""}
    right_city_display = {"country": "", "city": ""}
    comparison_results = []
    
    # Handle form submission
    if request.method == 'POST':
        left_city = request.form.get('left_city')
        right_city = request.form.get('right_city')
        
        # Extract country and city for display
        if left_city and " - " in left_city:
            country, city = left_city.split(" - ")
            left_city_display = {"country": country, "city": city}
        
        if right_city and " - " in right_city:
            country, city = right_city.split(" - ")
            right_city_display = {"country": country, "city": city}
        
        if left_city and right_city:
            # Get items for each city
            left_items = get_city_items(left_city)
            right_items = get_city_items(right_city)
            
            # Compare items
            comparison_results = compare_city_items(left_items, right_items)
    
    return render_template('compare_cities.html', 
                           cities=cities, 
                           left_city=left_city, 
                           right_city=right_city,
                           left_city_display=left_city_display,
                           right_city_display=right_city_display,
                           comparison_results=comparison_results)

@app.route('/salaries_by_area', methods=['GET', 'POST'])
def salaries_by_area():
    # Get all countries for the dropdown
    countries = get_countries()
    
    # Initialize variables
    selected_country = None
    img_data = None
    
    # Handle form submission
    if request.method == 'POST':
        selected_country = request.form.get('country')
        
        if selected_country:
            # Generate the chart
            img_data = create_salaries_chart(selected_country)
    
    return render_template('salaries_by_area.html', 
                           countries=countries, 
                           selected_country=selected_country, 
                           img_data=img_data)



@app.route('/jobs_by_country', methods=['GET', 'POST'])
def jobs_by_country():
    # Get data for dropdowns
    countries = get_countries()
    job_areas = get_job_areas()
    salary_ranges = list(range(0, 21000, 1000))  # 0 to 20000 in increments of 1000
    
    # Initialize variables
    selected_country = None
    selected_area = None
    selected_salary = None
    results = []
    searched = False
    
    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'month_mean_salary')
    sort_dir = request.args.get('sort_dir', 'DESC')
    
    # Handle form submission
    if request.method == 'POST':
        searched = True
        selected_country = request.form.get('country')
        selected_area = request.form.get('job_area')
        selected_salary = request.form.get('min_salary')
        
        if selected_country and selected_area and selected_salary:
            results = search_jobs_by_country(selected_country, selected_area, selected_salary, sort_by, sort_dir)
    
    # If using GET for sorting but we have form data in session
    elif request.args.get('sort_by') and request.args.get('country'):
        searched = True
        selected_country = request.args.get('country')
        selected_area = request.args.get('area')
        selected_salary = request.args.get('salary')
        
        if selected_country and selected_area and selected_salary:
            results = search_jobs_by_country(selected_country, selected_area, selected_salary, sort_by, sort_dir)
    
    return render_template('jobs_by_country.html',
                          countries=countries,
                          job_areas=job_areas,
                          salary_ranges=salary_ranges,
                          selected_country=selected_country,
                          selected_area=selected_area,
                          selected_salary=selected_salary,
                          results=results,
                          searched=searched,
                          sort_by=sort_by,
                          sort_dir=sort_dir)



@app.route('/affordability_by_country', methods=['GET', 'POST'])
def affordability_by_country():
    # Get all countries for the dropdown
    countries = get_countries()
    
    # Initialize variables
    selected_country = None
    img_data = None
    no_results = False
    
    # Handle form submission
    if request.method == 'POST':
        selected_country = request.form.get('country')
        
        if selected_country:
            # Generate the heatmap
            img_data = create_affordability_heatmap(selected_country)
            
            if img_data is None:
                no_results = True
    
    return render_template('affordability_by_country.html', 
                           countries=countries, 
                           selected_country=selected_country, 
                           img_data=img_data,
                           no_results=no_results)

@app.route('/worldwide_job_search', methods=['GET', 'POST'])
def worldwide_job_search():
    # Initialize variables
    results = []
    searched = False
    keywords = None
    
    # Handle form submission
    if request.method == 'POST':
        searched = True
        keywords = request.form.get('keywords')
        
        if keywords:
            # Search for jobs matching the keywords
            results = search_jobs_by_keywords(keywords)
    
    return render_template('worldwide_job_search.html', 
                           results=results,
                           searched=searched,
                           keywords=keywords)


@app.route('/custom_basket', methods=['GET', 'POST'])
def custom_basket():
    # Get all cities for the dropdown
    cities = get_cities()
    
    # Initialize variables
    selected_city = None
    items = None
    reference_basket = None
    custom_basket = None
    
    # Handle form submission
    if request.method == 'POST':
        selected_city = request.form.get('city')
        
        if selected_city:
            # Get items for the selected city
            items = get_city_items_for_basket(selected_city)
            
            # Get reference basket cost
            reference_basket = get_reference_basket_cost(selected_city)
            
            # Check if this is a calculation request
            if request.form.get('calculate'):
                # Calculate custom basket cost
                custom_basket = 0
                
                for item in items:
                    quantity = request.form.get(f'quantity_{item["item_id"]}')
                    if quantity and float(quantity) > 0:
                        item['quantity'] = float(quantity)
                        custom_basket += item['unit_cost_usd'] * item['quantity']
    
    return render_template('custom_basket.html', 
                           cities=cities, 
                           selected_city=selected_city, 
                           items=items,
                           reference_basket=reference_basket,
                           custom_basket=custom_basket)



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
