from flask import Flask, request, render_template
from flask_restx import Api, Resource
from runner import *
from runner import api as rebuild_wchat

app = Flask(__name__,template_folder='templates')

@app.route('/')
def home():
   return render_template('home.html')

api = Api(app)
api.add_namespace(rebuild_wchat)


if __name__ == "__main__":

        app.run( port=5000)
       