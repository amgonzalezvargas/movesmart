# app.py
from flask import Flask
import os
from utils import create_basket_cost_graph, create_html_content

app = Flask(__name__)

@app.route('/')
def hello():
    img_data = create_basket_cost_graph()
    html = create_html_content(img_data)
    return html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
