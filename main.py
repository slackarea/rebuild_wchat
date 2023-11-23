from flask import Flask, render_template
from flask_restx import Api, Resource
import os
from runner import *
from runner import api as rebuild_wchat

app = Flask(__name__, template_folder='templates')

# host_port = os.environ.get('FLASK_RUN_PORT')

@app.route('/')
def home():
    return render_template('home.html')

@app.errorhandler(500)
def internal_error(error):
    return "500 error"

@app.errorhandler(404)
def not_found(error):
    return "404 error",404

api = Api(app)
api.add_namespace(rebuild_wchat)

if __name__ == '__main__':
    app.run(debug=True)
