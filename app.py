# app.py
from flask import Flask, render_template, request
from utils import get_cities, get_city_items, compare_city_items
import os


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
    comparison_results = []
    
    # Handle form submission
    if request.method == 'POST':
        left_city = request.form.get('left_city')
        right_city = request.form.get('right_city')
        
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
                           comparison_results=comparison_results)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
