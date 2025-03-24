# app.py
from flask import Flask, render_template
import os
from utils import get_cheapest_countries, create_basket_cost_graph

app = Flask(__name__)

@app.route('/')
def home():
    img_data = create_basket_cost_graph()
    return render_template('home.html', img_data=img_data)

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



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
