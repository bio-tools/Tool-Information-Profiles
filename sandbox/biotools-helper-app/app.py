import csv
from flask import Flask, redirect, url_for, request, render_template
# from flask_socketio import SocketIO, emit
import random
import requests

from rdflib import ConjunctiveGraph
from jinja2 import Template
import json
from pyshacl import validate

from crawl_and_lift import rdfize, get_shape
import sys
# sys.path.append('../fairmetrics_interface_tests')

# Command line exec
import subprocess
from subprocess import Popen
from subprocess import PIPE
from subprocess import run

app = Flask(__name__)
# socketio = SocketIO(app)

#bioschema_dump = ConjunctiveGraph()
#g.parse("bise-linked-data-webapp/static/data/neubias-dump-20180129.ttl", format="turtle")

#bioschema_dump.parse("static/data/neubias-latest.ttl", format="turtle")
#print(str(len(bioschema_dump)) + ' triples in bio.tools BioSchema RDF graph')

shape = ConjunctiveGraph()
shape = get_shape()

@app.before_first_request
def before_first_request_func():
    print("This function will run once")

@app.route('/')
def index():
    return render_template('index.html', validation_results=[])

@app.route('/curation_needs')
def curation_needs():
    return render_template('demo_curation_needs.html')

@app.route('/profile_vis')
def profile_vis():
    vis_data = {}
    with open('../../profiles/ifbToolInfoProfile.json', 'r') as f:
        profile = json.load(f)
        for r in profile['rules']:
            # print(json.dumps(r, indent=True))
            for t in r['types']:
                req = r['requirement']
                if not t in vis_data.keys():
                    vis_data[t] = {req: []}

                if not req in vis_data[t].keys():
                    vis_data[t][req] = []

                for at in r['attributes']:
                    vis_data[t][req].append(at)

    print(json.dumps(vis_data, indent=True))
    return render_template('profile_vis.html', data=vis_data)


@app.route('/quality_check', methods=['GET', 'POST'])
def quality_check():
    print(str(request.form))

    tool_id = None

    if 'random action' in request.form :
        with open('./static/data/data-full.json') as json_file:
            data = json.load(json_file)
            tool_id = random.choice(data)
    elif 'check action' in request.form :
        if request.form.get('biotoolsID'):
            tool_id = request.form.get('biotoolsID')
    else:
        return render_template('index.html', validation_results=[])

    if not tool_id:
        return render_template('index.html', validation_results=[])
    else:
        app.logger.info("Checking annotation quality for " + tool_id)
        url = 'https://bio.tools/api/tool/' + tool_id + '?format=json'

        r = requests.get(url)
        tool = r.json()

        data_tool = ConjunctiveGraph()
        data_tool.parse(data=rdfize(tool), format="json-ld")

        print(data_tool.serialize(format="turtle").decode())

        print(len(shape))

        r = validate(data_graph=data_tool,
                     data_graph_format='turtle',
                     shacl_graph=shape,
                     shacl_graph_format='turtle',
                     ont_graph=None,
                     inference='rdfs',
                     abort_on_error=False,
                     meta_shacl=False,
                     debug=True)

        conforms, results_graph, results_text = r

        report_query = """
            SELECT ?node ?path WHERE {
                ?v rdf:type sh:ValidationReport ;
                   sh:result ?r .
                ?r sh:focusNode ?node ;
                   sh:sourceShape ?s . 
                ?s sh:path ?path . 
            }
        """

        res = {'tool_id':tool_id, 'node':[], 'path':[]}
        results = results_graph.query(report_query)
        for r in results:
            res['node'].append(str(r['node']))
            res['path'].append(str(r['path']))
            app.logger.info('The tool `{}` should be fixed, '
                            'it is missing information for field {}'.format(str(r['node']), str(r['path'])))

        print(str(len(results)) + ' actions needed to fix mandatory')
        print(json.dumps(res, indent=True))

        return render_template('index.html', validation_results=res, id=tool_id)

if __name__ == "__main__":
    # context = ('server.crt', 'server.key')
    # app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=context)
    app.run(host='0.0.0.0', port=5000, debug=True)
    # socketio.run(app)