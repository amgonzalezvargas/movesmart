# app.py
from flask import Flask, render_template, request
import os
from utils import get_cities, get_city_items, compare_city_items, get_countries, create_salaries_chart



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



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
