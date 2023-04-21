from flask import Flask
from flask_restx import Api
from runner import *
from runner import api as rebuild_wchat

app = Flask(__name__)
api = Api(app)

api.add_namespace(rebuild_wchat)

if __name__ == "__main__":
        app.run(host="127.0.0.1", port=5000)
       