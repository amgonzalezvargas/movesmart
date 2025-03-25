# utils.py
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import base64
from io import BytesIO
from db_config import DB_CONFIG
import mysql
import mysql.connector  # This imports the specific connector module

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
    """Get all cities from the database."""
    cities = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT city_name FROM city ORDER BY city_name")
        cities = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching cities: {e}")
    
    return cities

def get_city_items(city_name):
    """Get all items for a specific city."""
    items = []
    try:
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
        print(f"Error fetching items for city {city_name}: {e}")
    
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

