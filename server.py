from flask import jsonify
from flask import Flask
from flask import request
from flask import make_response
from flask_cors import CORS
from read_xpo_json import read_xpo
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from run import task1_predict, task2_predict
from read_xpo_json import read_xpo
import nltk
import json

import os


app = Flask(__name__)
CORS(app)

nltk.download('omw-1.4')
nltk.download('wordnet')

# sample task1 request: {"ce_id", "team", "entity.cs", "event.cs", "temporal.en", "temporal.es", "en.data", "es.data"}
# sample task2 request: {"ce_id", "team", "graph_g"}

team_urls = {
    "cmu": "https://www.cmu.edu/",
    "ibm": "https://ibm.com/CHRONOS/",
    "isi": "https://isi.edu/kairos/",
    "resin": "https://blender.cs.illinois.edu/kairos/",
    "sbu": "https://cs.sbu.edu/kairos/"
}

root_dir = "./"

schema_root_dir = os.path.join(root_dir, "schemas_qz9")
xpo_file_dir = os.path.join(root_dir, "xpo_v4.json")

em, rm = read_xpo(xpo_file_dir)

@app.route('/prediction/task1',methods=["POST"])
def return_opinions_task1():
    data_dict = request.json
    entity_cs_string = data_dict["entity.cs"]
    event_cs_string = data_dict["event.cs"]
    temp_en_string = data_dict["temporal.en"]
    temp_es_string = data_dict["temporal.es"]
    en_data = data_dict["en.data"]
    es_data = data_dict["es.data"]
    ceid = data_dict["ce_id"]
    team = data_dict["team"]

    schema_dir = os.path.join(schema_root_dir, team+"-schemalib.json")
    sdf_string = task1_predict(ceid, team, team_urls, schema_dir, entity_cs_string, event_cs_string, temp_en_string, temp_es_string, em, rm, en_data, es_data, 0.8, 0.4, 5, 2)

    return make_response(jsonify({"sdf": sdf_string}), 200)

@app.route('/prediction/task2',methods=["POST"])
def return_opinions_task2():
    data_dict = request.json
    
    ceid = data_dict["ce_id"]
    team = data_dict["team"]
    graph_g_str = data_dict["graph_g"]

    graph_g = json.loads(graph_g_str)
    schema_dir = os.path.join(schema_root_dir, team+"-schemalib.json")
    sdf_string = task2_predict(ceid, team, team_urls, schema_dir, graph_g, 0.8, 0.4, 5, 2)

    return make_response(jsonify({"sdf": sdf_string}), 200)

@app.route('/status',methods=["GET","POST"])
def return_status():
    return make_response(jsonify({'phrase' : 'Up and running'}), 200)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=20212, type=int)
    args = parser.parse_args()
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(args.port)
    IOLoop.instance().start()
