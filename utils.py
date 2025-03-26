# utils.py
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import base64
from io import BytesIO
from db_config import DB_CONFIG
import mysql
import mysql.connector  # This imports the specific connector module
import numpy as np

def create_html_content(img_data):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cost of Living Analysis</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                text-align: center;
                background-color: #f5f5f5;
            }}
            h1 {{
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            .description {{
                margin: 20px 0;
                text-align: left;
                line-height: 1.6;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Cost of Living Analysis</h1>
            <div class="description">
                <p>Este gráfico muestra los 10 países donde la "Canasta Básica Mensual" (Monthly Basket of Goods) 
                tiene el menor costo unitario en USD. Estos datos ayudan a identificar los países con menor costo de vida.</p>
            </div>
            <img src="data:image/png;base64,{img_data}" alt="Cheapest Countries Chart">
        </div>
    </body>
    </html>
    '''



def get_cities():
    """Get all cities from the database, including country information."""
    cities = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Updated query to join city and country tables
        cursor.execute("""
        SELECT c.city_name, co.country_name
        FROM city c
        JOIN country co ON c.country_id = co.country_id
        ORDER BY co.country_name, c.city_name
        """)
        cities = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching cities: {e}")
    return cities


def get_city_items(city_info):
    """Get all items for a specific city.
    city_info parameter can be just city_name or in "Country - City" format"""
    items = []
    try:
        # Extract just the city name if in "Country - City" format
        if " - " in city_info:
            city_name = city_info.split(" - ")[1]
        else:
            city_name = city_info
            
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT i.item_id, i.item_name, i.unit_cost_usd, i.item_cat_id
        FROM item i
        JOIN city c ON i.city_id = c.city_id
        WHERE c.city_name = %s
        """
        cursor.execute(query, (city_name,))
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching items for city {city_info}: {e}")
    
    return items



def compare_city_items(left_items, right_items):
    """Compare items between two cities and match by item name, ordering by item_cat_id."""
    # Create dictionaries using item_name as key instead of item_id
    left_dict = {item['item_name']: item for item in left_items}
    right_dict = {item['item_name']: item for item in right_items}
    
    # Get all unique item names
    all_item_names = set(left_dict.keys()) | set(right_dict.keys())
    
    # Filter out "Monthly Basket of Goods" if it exists to add it at the end
    basket_item = "Monthly Basket of Goods"
    has_basket = basket_item in all_item_names
    if has_basket:
        all_item_names.remove(basket_item)
    
    # Sort other items by item_cat_id
    def get_cat_id(name):
        if name in left_dict and 'item_cat_id' in left_dict[name]:
            return left_dict[name]['item_cat_id']
        elif name in right_dict and 'item_cat_id' in right_dict[name]:
            return right_dict[name]['item_cat_id']
        return 999  # Default high value for unknown categories
    
    ordered_items = sorted(all_item_names, key=lambda name: (get_cat_id(name), name))
    
    # Add "Monthly Basket of Goods" at the end if it exists
    if has_basket:
        ordered_items.append(basket_item)
    
    comparison_results = []
    for item_name in ordered_items:
        left_item = left_dict.get(item_name)
        right_item = right_dict.get(item_name)
        
        left_cost = left_item['unit_cost_usd'] if left_item else None
        right_cost = right_item['unit_cost_usd'] if right_item else None
        
        # Determine which is cheaper
        left_class = ""
        right_class = ""
        
        if left_cost is not None and right_cost is not None:
            if left_cost < right_cost:
                left_class = "cheaper"
                right_class = "expensive"
            elif right_cost < left_cost:
                left_class = "expensive"
                right_class = "cheaper"
            else:
                left_class = "equal"
                right_class = "equal"
        
        # Check if this is the basket item to add special highlighting
        highlight_class = "highlight-basket" if item_name == basket_item else ""
        
        comparison_results.append({
            'item_name': item_name,
            'left_cost': left_cost,
            'right_cost': right_cost,
            'left_class': left_class,
            'right_class': right_class,
            'highlight_class': highlight_class
        })
    
    return comparison_results


def get_countries():
    """Get all countries from the database."""
    countries = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT country_name FROM country ORDER BY country_name")
        countries = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching countries: {e}")
    return countries

def get_mean_salaries_by_area(country_name):
    """Get mean salaries grouped by job area for a specific country."""
    mean_salaries = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT ja.area_id, ja.area_name, AVG(j.month_mean_salary) AS mean_salary 
            FROM job j 
            JOIN job_area ja ON j.area_id = ja.area_id 
            JOIN country c ON j.country_id = c.country_id 
            WHERE c.country_name = %s 
            GROUP BY ja.area_id, ja.area_name 
            ORDER BY mean_salary DESC
        """, (country_name,))
        mean_salaries = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching mean salaries for {country_name}: {e}")
    return mean_salaries

def create_salaries_chart(country_name):
    """Create a bar chart showing mean salaries by job area."""
    # Get the data
    
    mean_salaries = get_mean_salaries_by_area(country_name)
    
    if not mean_salaries:
        return None
    
    # Extract data for plotting
    areas = [item['area_name'] for item in mean_salaries]
    salaries = [item['mean_salary'] for item in mean_salaries]
    
    # Create the plot
    fig = Figure(figsize=(12, 6))
    ax = fig.add_subplot(1, 1, 1)
    
    # Generate a colormap with different colors for each bar
    import matplotlib.cm as cm
    colors = cm.viridis(np.linspace(0, 1, len(areas)))
    
    # Create the bar chart
    bars = ax.bar(range(len(areas)), salaries, color=colors)
    
    # Set labels and title
    ax.set_xlabel('Job Areas')
    ax.set_ylabel('Mean Salary (USD)')
    ax.set_title(f'Mean Salary by Job Area in {country_name}')
    
    # Set x-ticks
    ax.set_xticks(range(len(areas)))
    ax.set_xticklabels(areas, rotation=45, ha='right')
    
    # Add currency formatting to y-axis
    from matplotlib.ticker import FuncFormatter
    def currency_formatter(x, pos):
        return f'${x:,.2f}'
    
    ax.yaxis.set_major_formatter(FuncFormatter(currency_formatter))
    
    # Adjust layout to make room for rotated labels
    fig.tight_layout()
    
    # Save to a BytesIO object
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    img_data = base64.b64encode(buf.getvalue()).decode('utf8')
    
    return img_data


def get_cities_with_countries():
    """Get all cities with their corresponding countries."""
    cities = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.city_name, co.country_name 
            FROM city c
            JOIN country co ON c.country_id = co.country_id
            ORDER BY co.country_name, c.city_name
        """)
        cities = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching cities with countries: {e}")
    return cities

def get_job_areas():
    """Get all job areas from the database."""
    areas = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT area_name FROM job_area ORDER BY area_name")
        areas = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching job areas: {e}")
    return areas

def search_jobs_by_criteria(country_name, city_name, area_name, min_salary, sort_by='month_mean_salary', sort_dir='DESC'):
    """Search for jobs based on country, city, job area, and minimum salary."""
    jobs = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Build the ORDER BY clause based on sort parameters
        order_clause = f"{sort_by} {sort_dir}"
        
        query = """
        SELECT 
            co.country_name,
            ci.city_name,
            ja.area_name,
            j.job_title,
            c.company_name,
            j.contract_type,
            j.month_mean_salary
        FROM job j
        JOIN country co ON j.country_id = co.country_id
        JOIN job_area ja ON j.area_id = ja.area_id
        JOIN company c ON j.company_id = c.company_id
        JOIN city ci ON ci.country_id = co.country_id
        WHERE co.country_name = %s
        AND ci.city_name = %s
        AND ja.area_name = %s
        AND j.month_mean_salary >= %s
        ORDER BY """ + order_clause
        
        cursor.execute(query, (country_name, city_name, area_name, min_salary))
        jobs = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error searching jobs: {e}")
    
    return jobs


def search_jobs_by_country(country_name, area_name, min_salary, sort_by='month_mean_salary', sort_dir='DESC'):
    """Search for jobs based on country, job area, and minimum salary."""
    jobs = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Build the ORDER BY clause based on sort parameters
        order_clause = f"{sort_by} {sort_dir}"
        
        query = """
        SELECT 
            co.country_name,
            ja.area_name,
            j.job_title,
            c.company_name,
            j.contract_type,
            j.month_mean_salary
        FROM job j
        JOIN country co ON j.country_id = co.country_id
        JOIN job_area ja ON j.area_id = ja.area_id
        JOIN company c ON j.company_id = c.company_id
        WHERE co.country_name = %s
        AND ja.area_name = %s
        AND j.month_mean_salary >= %s
        ORDER BY """ + order_clause
        
        cursor.execute(query, (country_name, area_name, min_salary))
        jobs = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error searching jobs: {e}")
    
    return jobs
