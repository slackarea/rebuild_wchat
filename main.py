from flask import Flask, render_template
from flask_restx import Api, Resource
import os
from runner import *
from runner import api as rebuild_wchat

app = Flask(__name__, template_folder='templates')

host_port = os.environ.get('HOST_PORT')

@app.route('/')
def home():
    return render_template('home.html', port=host_port)


api = Api(app)
api.add_namespace(rebuild_wchat)

if __name__ == '__main__':
    app.run()
