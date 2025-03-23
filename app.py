# app.py
from flask import Flask, render_template
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

app = Flask(__name__)

@app.route('/')
def index():
    # Generate the figure
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Data for the bar chart
    categories = ['Category A', 'Category B', 'Category C', 'Category D']
    values = [25, 40, 30, 55]
    
    # Create bar chart
    ax.bar(categories, values, color='skyblue')
    ax.set_title('Simple Bar Chart Example')
    ax.set_ylabel('Values')
    
    # Save plot to a temporary buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Encode the image to embed in HTML
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Bar Chart</title>
    </head>
    <body>
        <h1>Simple Bar Chart Example</h1>
        <img src="data:image/png;base64,{image_base64}">
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)
