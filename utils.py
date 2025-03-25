# utils.py
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import base64
from io import BytesIO
from db_config import DB_CONFIG
import mysql
import mysql.connector  # This imports the specific connector module



def get_countries():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        query = "SELECT country_name FROM country ORDER BY country_name"
        cursor.execute(query)
        countries = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return countries
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

def get_country_items(country_name):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        query = """
        SELECT i.item_name, i.unit_cost_USD
        FROM item i
        JOIN country c ON i.country_id = c.country_id
        WHERE c.country_name = %s
        ORDER BY i.item_name
        """
        cursor.execute(query, (country_name,))
        items = cursor.fetchall()
        cursor.close()
        connection.close()
        return items
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []



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


def get_job_areas():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        query = "SELECT area_name FROM job_area ORDER BY area_name"
        cursor.execute(query)
        areas = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return areas
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

def search_jobs(country, area, keywords, sort_by='job_title', sort_dir='asc'):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Construir la consulta base
        query = """
        SELECT c.country_name, comp.company_name, ja.area_name, j.job_title, j.month_mean_salary
        FROM job j
        JOIN country c ON j.country_id = c.country_id
        JOIN company comp ON j.company_id = comp.company_id
        JOIN job_area ja ON j.area_id = ja.area_id
        WHERE 1=1
        """
        
        params = []
        
        # Añadir condiciones según la entrada del usuario
        if country and country != 'All':
            query += " AND c.country_name = %s"
            params.append(country)
            
        if area and area != 'All':
            query += " AND ja.area_name = %s"
            params.append(area)
            
        if keywords:
            # Dividir palabras clave y crear condición para cada una
            keyword_list = keywords.split()
            for keyword in keyword_list:
                query += " AND j.job_title LIKE %s"
                params.append(f"%{keyword}%")
        
        # Añadir cláusula ORDER BY
        valid_columns = {
            'country': 'c.country_name',
            'company': 'comp.company_name',
            'area': 'ja.area_name',
            'job_title': 'j.job_title',
            'salary': 'j.month_mean_salary'
        }
        
        order_col = valid_columns.get(sort_by, 'j.job_title')
        order_dir = 'DESC' if sort_dir.lower() == 'desc' else 'ASC'
        
        query += f" ORDER BY {order_col} {order_dir}"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []


