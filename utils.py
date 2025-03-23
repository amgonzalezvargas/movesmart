# utils.py
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import base64
from io import BytesIO

def create_sales_graph():
    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()
    
    categorias = ['Tortugas', 'Sega', 'He-Man', 'Nintendo']
    valores = [25, 40, 30, 55]
    
    ax.bar(categorias, valores, color='skyblue')
    ax.set_title('Ventas por Producto')
    ax.set_ylabel('Unidades Vendidas')
    
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    
    img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_data

def create_html_content(img_data):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard de Ventas</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                text-align: center;
            }}
            h1 {{
                color: #333;
            }}
        </style>
    </head>
    <body>
        <h1>Bienvenido al Dashboard de Ventas</h1>
        <p>Aquí tienes el gráfico de ventas por producto:</p>
        <img src="data:image/png;base64,{img_data}" alt="Gráfico de ventas">
    </body>
    </html>
    '''
