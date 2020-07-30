from flask import Flask, jsonify, request
import json
import networkx as nx
import json
import requests
from datetime import datetime
from pathlib import Path
import re
import networkx as nx
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

def get_graph_string(json_file):
    try:
        graph = parse_json(json_file)
    except(IOError):
        print('File was not found:')
        print(node_path)

    return graph

def parse_timestamp(timestamp):
        try:
            cast_timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            print('Failed datetime(timestamp) casting:')
            print(timestamp)
            cast_timestamp = timestamp
        return cast_timestamp

def parse_scheme_id(scheme_id):
    try:
        cast_scheme_id = int(scheme_id)
    except (ValueError, TypeError):
        print('Failed int(schemeID) casting:')
        print(scheme_id)
        cast_scheme_id = scheme_id
    return cast_scheme_id


def parse_node_id(node_id):
    try:
        cast_node_id = int(node_id)
    except (ValueError, TypeError):
        print('Failed int(nodeID) casting:')
        print(node_id)
        cast_node_id = node_id
    return cast_node_id


def parse_edge_id(edge_id):
    try:
        case_edge_id = int(edge_id)
    except (ValueError, TypeError):
        print('Failed int(edgeID) casting:')
        print(edge_id)
        case_edge_id = edge_id
    return case_edge_id

def parse_json(node_set):

    G = nx.DiGraph()
    locution_dict = {}

    for node in node_set['nodes']:

        if 'scheme' in node:
            nID = self.parse_node_id(node['nodeID'])

            G.add_node(self.parse_node_id(node['nodeID']), text=node.get('text', None), type=node.get('type', None),
                       timestamp= parse_timestamp(node.get('timestamp', None)), scheme=node.get('scheme', None),
                       scheme_id= parse_scheme_id(node.get('schemeID', None)))
        else:
            #print(node['nodeID'])
            nID = parse_node_id(node['nodeID'])
            if nID == '501681' or nID == 501681:
                print(node)
            G.add_node(parse_node_id(node['nodeID']), text=node.get('text', None), type=node.get('type', None),
                       timestamp=parse_timestamp(node.get('timestamp', None)))

    for edge in node_set['edges']:
        from_id = parse_edge_id(edge['fromID'])
        to_id = parse_edge_id(edge['toID'])
        G.add_edge(from_id, to_id)

    #for locution in node_set['locutions']:
    #    node_id = self.parse_node_id(locution['nodeID'])
    #    locution_dict[node_id] = locution
    return G
def remove_iso_analyst_nodes(graph):
    analyst_nodes = []
    isolated_nodes = list(nx.isolates(graph))
    for node in isolated_nodes:
        if graph.nodes[node]['type'] == 'L':
            analyst_nodes.append(node)
    graph.remove_nodes_from(analyst_nodes)
    return graph

def get_l_node_list(graph):
    l_nodes =  [(x,y['text']) for x,y in graph.nodes(data=True) if y['type']=='L']
    return l_nodes

def get_loc_prop_pair(graph):
    i_node_ids =  [x for x,y in graph.nodes(data=True) if y['type']=='I']
    locution_prop_pair = []
    for node_id in i_node_ids:
        preds = list(graph.predecessors(node_id))
        for pred in preds:
            node_type=graph.nodes[pred]['type']
            node_text = graph.nodes[pred]['text']

            if node_type == 'YA' and node_text != 'Agreeing':
                ya_preds = list(graph.predecessors(pred))
                for ya_pred in ya_preds:
                    pred_node_type=graph.nodes[ya_pred]['type']
                    pred_node_text=graph.nodes[ya_pred]['text']

                    if pred_node_type == 'L':
                        locution_prop_pair.append((ya_pred, node_id))
    return locution_prop_pair


def get_graph_url(node_path):
    try:
        jsn_string = requests.get(node_path).text
        strng_ind = jsn_string.index('{')
        n_string = jsn_string[strng_ind:]
        dta = json.loads(n_string)
        graph = parse_json(dta)
    except(IOError):
        print('File was not found:')
        print(node_path)

    return graph, dta

def convertToCIS(aif_json_graph, aif_json_data):

    #Deal with nodesetID or JSON file
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

    G = remove_iso_analyst_nodes(aif_json_graph)
    l_nodes = get_l_node_list(G)
    l_node_i_node = get_loc_prop_pair(G)
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
    dir_path = 'http://www.aifdb.org/json/' + str(aif_nodesetID)
    graph, aif_json_data = get_graph_url(dir_path)
    json_file = convertToCIS(graph, aif_json_data)
    return json_file

def is_aif_file(aif_json_file):

    graph = get_graph_string(aif_json_file)
    json_file = convertToCIS(graph, aif_json_file)
    return json_file

def openJsonFile(json_file_name):
    with open(json_file_name) as json_file:
        json_object = json.load(json_file)
    return json_object
#  main thread of execution to start the server
if __name__=='__main__':
    app.run()
