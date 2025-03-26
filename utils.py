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
import re



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



def get_cities_by_country(country_name):
    """Get all cities for a specific country."""
    cities = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT c.city_id, c.city_name
        FROM city c
        JOIN country co ON c.country_id = co.country_id
        WHERE co.country_name = %s
        ORDER BY c.city_name
        """
        cursor.execute(query, (country_name,))
        cities = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching cities for country {country_name}: {e}")
    
    return cities

def get_monthly_basket_cost_by_city(city_id):
    """Get the cost of Monthly Basket of Goods for a specific city."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT unit_cost_usd
        FROM item
        WHERE city_id = %s AND item_name = 'Monthly Basket of Goods'
        """
        cursor.execute(query, (city_id,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return result['unit_cost_usd']
        else:
            return None
    except Exception as e:
        print(f"Error fetching Monthly Basket of Goods cost for city ID {city_id}: {e}")
        return None

def calculate_affordability_index(mean_salary, basket_cost):
    """Calculate the Affordability Index."""
    if mean_salary is None or basket_cost is None or basket_cost == 0:
        return None
    return (mean_salary / basket_cost) * 100


def get_mean_salaries_by_area_for_country(country_name):
    """Get mean salaries by job area for a specific country."""
    areas = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT 
            ja.area_name, 
            AVG(j.month_mean_salary) as mean_salary
        FROM job j
        JOIN country co ON j.country_id = co.country_id
        JOIN job_area ja ON j.area_id = ja.area_id
        WHERE co.country_name = %s
        GROUP BY ja.area_name
        ORDER BY ja.area_name
        """
        
        cursor.execute(query, (country_name,))
        areas = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error getting mean salaries by area: {e}")
    
    return areas




def create_affordability_heatmap(country_name):
    """Create a heatmap showing affordability index by job area and city."""
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    import numpy as np
    from io import BytesIO
    import base64
    
    # Get cities for the country
    cities = get_cities_by_country(country_name)
    
    # Get mean salaries by job area
    job_areas = get_mean_salaries_by_area_for_country(country_name)
    
    if not cities or not job_areas:
        return None
    
    # Prepare data for heatmap
    data = []
    city_names = []
    area_names = []
    
    # Store additional data
    avg_salaries = []
    basket_costs = []
    
    for city in cities:
        city_id = city['city_id']
        city_name = city['city_name']
        
        # Get Monthly Basket of Goods cost for this city
        basket_cost = get_monthly_basket_cost_by_city(city_id)
        
        if basket_cost is not None:
            city_names.append(city_name)
            city_data = []
            city_avg_salaries = []
            city_basket_costs = []
            
            for area in job_areas:
                if len(area_names) < len(job_areas):
                    area_names.append(area['area_name'])
                
                mean_salary = area['mean_salary']
                affordability_index = calculate_affordability_index(mean_salary, basket_cost)
                city_data.append(affordability_index if affordability_index is not None else 0)
                city_avg_salaries.append(mean_salary)
                city_basket_costs.append(basket_cost)
            
            data.append(city_data)
            avg_salaries.append(city_avg_salaries)
            basket_costs.append(city_basket_costs)
    
    if not data:
        return None
    
    # Create heatmap
    data_array = np.array(data)
    avg_salaries_array = np.array(avg_salaries)
    basket_costs_array = np.array(basket_costs)
    
    # Transpose the arrays
    data_array = data_array.T
    avg_salaries_array = avg_salaries_array.T
    basket_costs_array = basket_costs_array.T
    
    # Create the plot with adjusted figsize for better width proportion
    plt.rcParams.update({'figure.autolayout': True})
    fig = Figure(figsize=(16, 10))
    
    # Create subplot with specific layout parameters to reduce whitespace
    ax = fig.add_subplot(1, 1, 1)
    
    # Use the viridis colormap
    cmap = plt.cm.viridis
    
    # Create the heatmap
    im = ax.imshow(data_array, cmap=cmap, aspect='auto')  # Add aspect='auto' to adjust aspect ratio
    
    # Set labels for axes
    ax.set_xticks(np.arange(len(city_names)))
    ax.set_yticks(np.arange(len(area_names)))
    ax.set_xticklabels(city_names, rotation=45, ha='right')
    ax.set_yticklabels(area_names)
    
    # Add colorbar with specific location parameters
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="2%", pad=0.1)
    cbar = fig.colorbar(im, cax=cax)
    cbar.ax.set_ylabel('Affordability Index', rotation=-90, va="bottom")
    
    # Add text in each cell
    for i in range(len(area_names)):
        for j in range(len(city_names)):
            affordability_index = data_array[i, j]
            avg_salary = avg_salaries_array[i, j]
            basket_cost = basket_costs_array[i, j]
            
            text_color = "white" if affordability_index < np.max(data_array) / 2 else "black"
            cell_text = f"AS: ${avg_salary:.2f}\nCL: ${basket_cost:.2f}\nAI: {affordability_index:.1f}"
            
            ax.text(j, i, cell_text, ha="center", va="center", color=text_color, fontsize=8)
    
    # Set title
    ax.set_title(f'Affordability Index by Job Area and City in {country_name}')
    
    # Instead of tight_layout, set explicit margins to reduce whitespace
    fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)
    
    # Save to a BytesIO object with tight bounding box
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)
    img_data = base64.b64encode(buf.getvalue()).decode('utf8')
    
    return img_data



def search_jobs_by_keywords(keywords):
    """Search for jobs containing one or more keywords in the job title."""
    jobs_with_cities = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Split keywords by spaces or commas
        keywords_list = [k.strip() for k in re.split(r'[,\s]+', keywords) if k.strip()]
        
        if not keywords_list:
            return []
        
        # Build the SQL condition for keywords
        keyword_conditions = []
        params = []
        
        for keyword in keywords_list:
            keyword_conditions.append("j.job_title LIKE %s")
            params.append(f"%{keyword}%")
        
        keyword_sql = " OR ".join(keyword_conditions)
        
        # Main query to get jobs matching keywords
        query = f"""
        SELECT 
            co.country_id,
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
        WHERE {keyword_sql}
        ORDER BY co.country_name, ja.area_name
        """
        
        cursor.execute(query, params)
        jobs = cursor.fetchall()
        
        # For each job, get cities in the job's country and their Monthly Basket of Goods cost
        for job in jobs:
            country_id = job['country_id']
            
            # Query to get cities and their Monthly Basket of Goods cost for this country
            city_query = """
            SELECT 
                ci.city_name,
                i.unit_cost_usd
            FROM city ci
            JOIN item i ON ci.city_id = i.city_id
            WHERE ci.country_id = %s AND i.item_name = 'Monthly Basket of Goods'
            ORDER BY ci.city_name
            """
            
            cursor.execute(city_query, (country_id,))
            cities = cursor.fetchall()
            
            # Add cities to the job entry
            job_entry = job.copy()
            job_entry['cities'] = cities
            
            # Add the job entry to the results
            jobs_with_cities.append(job_entry)
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error searching jobs by keywords: {e}")
    
    return jobs_with_cities



def get_city_items_for_basket(city_info):
    """Get all items for a specific city, excluding Monthly Basket of Goods."""
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
        SELECT i.item_id, i.item_name, i.unit_cost_usd
        FROM item i
        JOIN city c ON i.city_id = c.city_id
        WHERE c.city_name = %s
        AND i.item_name != 'Monthly Basket of Goods'
        ORDER BY i.item_name
        """
        cursor.execute(query, (city_name,))
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching items for city {city_info}: {e}")
    
    return items

def get_reference_basket_cost(city_info):
    """Get the cost of the reference Monthly Basket of Goods for a city."""
    try:
        # Extract just the city name if in "Country - City" format
        if " - " in city_info:
            city_name = city_info.split(" - ")[1]
        else:
            city_name = city_info
            
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT i.unit_cost_usd
        FROM item i
        JOIN city c ON i.city_id = c.city_id
        WHERE c.city_name = %s
        AND i.item_name = 'Monthly Basket of Goods'
        """
        cursor.execute(query, (city_name,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return result['unit_cost_usd']
        else:
            return None
    except Exception as e:
        print(f"Error fetching reference basket cost for city {city_info}: {e}")
        return None
