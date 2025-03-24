# utils.py
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import base64
from io import BytesIO
import mysql.connector
from db_config import DB_CONFIG

def get_cheapest_countries():
    try:
        # Establecer conexión con la base de datos
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Consulta SQL para obtener los 10 países con menor costo unitario de "Monthly Basket of Goods"
        query = """
        SELECT c.country_name, i.unit_cost_USD
        FROM item i
        JOIN country c ON i.country_id = c.country_id
        WHERE i.item_name = 'Monthly Basket of Goods'
        ORDER BY i.unit_cost_USD ASC
        LIMIT 10
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Cerrar cursor y conexión
        cursor.close()
        connection.close()
        
        return results
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        # En caso de error, devolver datos de muestra para que la aplicación no falle
        return [("Error", 0), ("Connecting", 0), ("to", 0), ("Database", 0)]

def create_basket_cost_graph():
    # Obtener datos de la base de datos
    data = get_cheapest_countries()
    
    # Preparar los datos para el gráfico
    countries = [row[0] for row in data]
    costs = [row[1] for row in data]
    
    # Crear figura y gráfico
    fig = Figure(figsize=(12, 6))
    ax = fig.subplots()
    
    # Crear gráfico de barras
    bars = ax.bar(countries, costs, color='skyblue')
    
    # Formatear el gráfico
    ax.set_title('Top 10 Countries with Lowest Monthly Basket of Goods Cost')
    ax.set_xlabel('Country')
    ax.set_ylabel('Unit Cost (USD)')
    ax.set_xticklabels(countries, rotation=45, ha='right')
    
    # Añadir etiquetas con los valores encima de cada barra
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'${height:.2f}',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3),
                   textcoords="offset points",
                   ha='center', va='bottom')
    
    fig.tight_layout()
    
    # Convertir figura a imagen
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    
    img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_data


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
