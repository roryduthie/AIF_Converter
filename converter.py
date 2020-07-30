from flask import Flask, jsonify, request
import json
from .centrality import Centrality
from werkzeug.contrib.fixers import ProxyFix
# initialize our Flask application
app= Flask(__name__)

@app.route("/aifdb-cispace/<ids>", methods=["GET"])
def getAifdbCIS(ids):
    cis_js = is_nodeset(ids)
    return cis_js


@app.route("/json-cispace", methods=["POST"])
def getAifCIS():
    if request.method=='POST':
        posted_data = request.get_json()
        cis_js = is_aif_file(posted_data)
        return cis_js



@app.route("/cispace-json", methods=["POST"])
def getCISAif():
    if request.method=='POST':
        posted_data = request.get_json()
        aif_js = convertCisToAIF(posted_data)
        aif_js = json.dumps(aif_js)
        return aif_js

def convertToCIS(aif_json_graph, aif_json_data):

    #Deal with nodesetID or JSON file
    from centrality import Centrality
    schemes = {'LPK': 'PositionToKnow', 'LEO': 'ExpertOpinion', 'LAN': 'Analogy', 'LCE':'CauseToEffect', 'LID':'Default Inference', 'LCS':'Default Inference', 'LPV':'Default Inference', 'LPP': 'Default Preference'}
    new_data = {}
    new_data['nodes'] = []
    new_data['edges'] = []
    new_data['timest'] = ""
    new_data['isshared'] = "false"
    new_data['description'] = ""
    new_data['graphID'] = ""
    new_data['title'] = ""
    new_data['userID'] = ""

    centra = Centrality()

    G = centra.remove_iso_nodes(aif_json_graph)
    l_nodes = centra.get_l_node_list(G)
    l_node_i_node = centra.get_loc_prop_pair(G)
    #Input json file with nodes and edges
    #data = openJsonFile(aif_json_file)
    data = aif_json_data

    for i,node in enumerate(data['nodes']):
        text = node['text']
        node_type = node['type']
        timestamp = node['timestamp']
        nodeID = node['nodeID']

        if node_type == "I":
            l_id, l_text = get_l_node_text(nodeID, l_node_i_node, l_nodes)
            if ':' in l_text:
                sourceName = l_text.split(":", 1)[0]
            else:
                sourceName = ''

            new_data['nodes'].append({
                'nodeID': nodeID,
                'type' : node_type,
                'text' : text,
                'source' : sourceName,
                'dtg' : timestamp,
                'input': 'null',
                'islocked' : 'false',
                'uncert': 'Confirmed',
                'cmt': 'N/A',
                'graphID': ''
            })
        if node_type == "RA":
            try:
                cis_scheme_val =  list(schemes.keys())[list(schemes.values()).index(text)]
            except:
                cis_scheme_val = ''
            new_data['nodes'].append({
                'nodeID': nodeID,
                'type' : node_type,
                'text' : cis_scheme_val,
                'source' : '',
                'dtg' : timestamp,
                'input': 'null',
                'islocked' : 'false',
                'uncert': 'Confirmed',
                'cmt': 'N/A',
                'graphID': ''
            })
        if node_type == "CA":
            new_data['nodes'].append({
                'nodeID': nodeID,
                'type' : node_type,
                'text' : '',
                'source' : '',
                'dtg' : timestamp,
                'input': 'null',
                'islocked' : 'false',
                'uncert': 'Confirmed',
                'cmt': 'N/A',
                'graphID': ''
            })
        if node_type == "PA":
            new_data['nodes'].append({
                'nodeID': nodeID,
                'type' : 'RA',
                'text' : 'LPP',
                'source' : '',
                'dtg' : timestamp,
                'input': 'null',
                'islocked' : 'false',
                'uncert': 'Confirmed',
                'cmt': 'N/A',
                'graphID': ''
            })

    for edge in data['edges']:
        eid = edge['edgeID']
        fromID = edge['fromID']
        toID = edge['toID']

        is_from = is_i_s_node(data, fromID)
        is_to = is_i_s_node(data, toID)

        if is_from and is_to:


            new_data['edges'].append({
                    'edgeID': eid,
                    'target' : toID,
                    'source' : fromID
            })
    return json.dumps(new_data)



def convertCisToAIF(cis_json_file):
    schemes = {'LPK': 'PositionToKnow', 'LEO': 'ExpertOpinion', 'LAN': 'Analogy', 'LCE':'CauseToEffect', 'LID':'Default Inference', 'LCS':'Default Inference', 'LPV':'Default Inference', 'LPP': 'Default Preference'}
    new_data = {}
    new_data['nodes'] = []
    new_data['edges'] = []
    new_data['locutions'] = []

    #Input json file with nodes and edges
    data = cis_json_file
    for i,node in enumerate(data['nodes']):
        text = node['text']
        node_type = node['type']
        timestamp = node['dtg']
        source = node['source']
        nodeID = node['nodeID']

        if node_type == 'I' and source == 'null':

            new_data['nodes'].append({
                'nodeID': nodeID,
                'type' : node_type,
                'text' : text,
                'timestamp' : timestamp
            })
        elif node_type == 'I' and source != 'null':
            l_node_id = 'L' + str(i)
            l_node_text = source + ': ' + text
            ya_node_id = 'YA' + str(i)
            new_data['nodes'].append({
                'nodeID': l_node_id,
                'type' : 'L',
                'text' : l_node_text
            })
            new_data['nodes'].append({
                'nodeID': nodeID,
                'type' : node_type,
                'text' : text,
                'timestamp' : timestamp
            })
            new_data['nodes'].append({
                'nodeID': ya_node_id,
                'type' : 'YA',
                'text' : 'Asserting'
            })

            new_data['edges'].append({
                'edgeID': 'e' + str(i),
                'toID' : ya_node_id,
                'fromID' : l_node_id
            })
            new_data['edges'].append({
                'edgeID': 'ee' + str(i),
                'toID' : nodeID,
                'fromID' : ya_node_id
            })
        elif node_type == 'CA':
            new_data['nodes'].append({
                'nodeID': nodeID,
                'type' : node_type,
                'text' : 'Default Conflict'
            })
        elif node_type == 'RA':
            try:
                aif_scheme_val = schemes[text]
            except:
                aif_scheme_val = 'Default Inference'

            new_data['nodes'].append({
                'nodeID': nodeID,
                'type' : node_type,
                'text' : aif_scheme_val
            })

    for edge in data['edges']:
        eid = edge['edgeID']
        fromID = edge['source']
        toID = edge['target']

        new_data['edges'].append({
                'edgeID': eid,
                'toID' : toID,
                'fromID' : fromID
        })


    return new_data
def get_l_node_text(i_node_id, lnode_inode_list, l_node_list):
    for rel_tup in lnode_inode_list:
        lnode_id = rel_tup[0]
        inode_id = rel_tup[1]
        if str(i_node_id) == str(inode_id):
            for tups in l_node_list:
                l_id = tups[0]
                if str(l_id) == str(lnode_id):
                    ltext = tups[1]
                    return l_id, ltext
    return None, ''

def is_i_s_node(aif_data, node_id):
    for i,node in enumerate(aif_data['nodes']):
        nodeID = node['nodeID']
        node_type = node['type']
        if nodeID == node_id:
            if node_type == 'I' or node_type == 'RA' or node_type == 'CA' or node_type == 'PA':
                return True
            else:
                return False
    return False

def is_nodeset(aif_nodesetID):
    centra = Centrality()
    dir_path = 'http://www.aifdb.org/json/' + str(aif_nodesetID)
    graph, aif_json_data = centra.get_graph_url(dir_path)
    json_file = convertToCIS(graph, aif_json_data)
    return json_file

def is_aif_file(aif_json_file):
    centra = Centrality()
    graph = centra.get_graph_string(aif_json_file)
    json_file = convertToCIS(graph, aif_json_file)
    return json_file

def openJsonFile(json_file_name):
    with open(json_file_name) as json_file:
        json_object = json.load(json_file)
    return json_object
#  main thread of execution to start the server
app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__=='__main__':
    app.run()
