import json
import os

import networkx as nx

from collections import defaultdict
from copy import deepcopy
from tqdm import tqdm

from read_xpo_json import read_xpo
from bs4 import BeautifulSoup
from event_temporal import expand_temporal


def read_ltf_file(xml_string):
    # read the ltf file into a dictionary: {(start_int, end_int): "sentence"}
    char_to_sent = {}
    soup = BeautifulSoup(xml_string, 'lxml-xml')
    lctl_text = soup.find("LCTL_TEXT")
    doc = lctl_text.find("DOC")
    doc_name = doc["id"]
    text = doc.find("TEXT")

    for segment in text.find_all("SEG"):
        sentence = segment.find("ORIGINAL_TEXT").text
        start_char, end_char = segment['start_char'], segment['end_char']
        char_to_sent[(int(start_char), int(end_char))] = sentence

    return char_to_sent, doc_name


def read_file_clusters(en_strings_list, es_string_list):
    ltf_strings_list = en_strings_list + es_string_list
    # cluster_dict: {"ceID": [list of document names]}
    output_dict = {} # {"ceID": {"doc_name1": {(start, end): "sent"}, "doc_name2": {(start, end): "sent"}}}
    for string in ltf_strings_list:
        char_to_sent_dict, docname = read_ltf_file(string)
        output_dict[docname] = char_to_sent_dict
    return output_dict 


def find_sentence_back(doc_id, start, end, doc_info_dict):
    char_to_offset = doc_info_dict[doc_id]
    # print(char_to_offset)
    # print(start)
    # print(end)
    for span in char_to_offset:
        # print(span)
        if span[0] <= start and span[1] >= end:
            sentence = char_to_offset[span]
            return sentence
        
    return "Did not find in the ltf files, Probably due to translation span errors.".upper()


def remove_conflict_temporal_relations(temporal_rels):
    edges = defaultdict(list)
    def can_reach(x, y):
        vis.add(x)
        for edge in edges[x]:
            if edge == y:
                return True
            else:
                if not edge in vis:
                    is_reached = can_reach(edge, y)
                    if is_reached:
                        return True
        return False

    temporal_rels = sorted(temporal_rels, key=lambda x: x[1], reverse=True)
    final_temporal_rels = []
    for rel in tqdm(temporal_rels, total=len(temporal_rels)):
        vis = set()
        # Remove self loop
        if rel[0][1] == rel[0][0]:
            continue
        if (not can_reach(rel[0][1], rel[0][0])) and not (rel[0][1] in edges[rel[0][0]]):
            edges[rel[0][0]].append(rel[0][1])
            final_temporal_rels.append(rel)

    return final_temporal_rels


def read_temporal_list(temp_en_str, temp_es_str):
    temporal_list = []

    en_lines = temp_en_str.split('\n')
    for line in en_lines:
        if len(line) != 0:
            splits = line.split('\t')
            if splits[1] == "TEMPORAL_BEFORE":
                temporal_list.append([[splits[0], splits[2]], float(splits[-1])])
            if splits[1] == "TEMPORAL_AFTER":
                temporal_list.append([[splits[2], splits[0]], float(splits[-1])])
    
    es_lines = temp_es_str.split('\n')
    for line in es_lines:
        if len(line) != 0:
            splits = line.split('\t')
            if splits[1] == "TEMPORAL_BEFORE":
                temporal_list.append([[splits[0], splits[2]], float(splits[-1])])
            if splits[1] == "TEMPORAL_AFTER":
                temporal_list.append([[splits[2], splits[0]], float(splits[-1])])

    # print(len(temporal_list))
    final_temporal_rels = remove_conflict_temporal_relations(temporal_list)
    # print(len(final_temporal_rels))
    output_rels = [rel[0].copy() for rel in final_temporal_rels]
    return output_rels  


def process_events_cluster(event_cs_string, en_data, es_data):
    # process events in the file as a dict
    # {
    #     "event_id":{
    #         "type": "Life.Die",
    #         "args": [(entity_id1, role_name1), (entity_id2, role_name2)],
    #         "mentions": [
    #               [doc_name, 111, 222, sentence], 
    #               [doc_name, 111, 222, sentence], 
    #          ],
    #     }
    # }
    # file_string_dict = {ceID: {doc_name: {(): "sentence"}}}
    # output_dict = {}
    # for ce_id in file_string_dict:
        # output_dict[ce_id] = {}
    
    file_sent_dict = read_file_clusters(en_data, es_data)
    output_event_dict = {}
    lines = event_cs_string.split('\n')
    event_id_to_lines = {}
    # read out all the lines related to one entity id.
    for i in range(len(lines)): # look up the text sentences
        line = lines[i]
        if len(line) != 0:
            parsed_line = line.split('\t')
            event_id = parsed_line[0]
            
            if event_id not in event_id_to_lines:
                event_id_to_lines[event_id] = [line]
            else:
                event_id_to_lines[event_id].append(line)
    
    # building event cs dict according to their starting strings
    # print(event_id_to_lines)
    # print(file_sent_dict.keys())

    for event_id in event_id_to_lines:
        event_lines = event_id_to_lines[event_id]

        mentions_list = [] # list of mentions (doc_name, start_idx, end_idx, sent)
        args = []

        for line in event_lines:
            split_line = line.split('\t')
            if split_line[1] == "type":
                event_type = split_line[2].split("#")[-1]

            if split_line[1] == "mention.actual":
                occur = split_line[3].split(":")
                doc_name = occur[0]
                start_idx = int(occur[1].split('-')[0])
                end_idx = int(occur[1].split('-')[1])

                if end_idx - start_idx <= 1:
                    continue

                text = split_line[2][1:-1]

                sentence = find_sentence_back(doc_name, start_idx, end_idx, file_sent_dict)
                mention_info = (doc_name, start_idx, end_idx, text, sentence) # need to modify here to read in sentence

                if mention_info not in mentions_list:
                    mentions_list.append(mention_info)
            # print(split_line[1])
            if split_line[2].startswith(":"): # argument_line
                # role_names = split_line[1].split('#')[1].split('.')
                # role_names = split_line[1].split('#')[1].split('.')
                role_name = ".".join(split_line[1].split('.')[:-1])
                # role_name = ".".join(role_names[:-1])
                ent_id = split_line[2]
                args.append([ent_id, role_name])
        
        if len(args) == 0:
            continue
        
        if len(mentions_list) == 0:
            continue
        event_info = {
            "type": event_type,
            "arguments": deepcopy(args),
            "mentions": deepcopy(mentions_list)
        }
        # print(event_info)
        output_event_dict.update({event_id: event_info})

    with open("event_debug.json", 'w', encoding="utf-8") as f:
        f.write(json.dumps(output_event_dict, indent=4))
    return output_event_dict


def process_entities_cluster(entity_cs_string):
    # rev_cluster_dict = {doc_name: cluster_name}
    # file_string_dict = {cluster_name: {}}
    # entity_dict of each cluster:
    # {
    #     "Entity_EDL_0064583": {
    #         "type": "PER",
    #         "mentions":[
    #             ["VOA_EN_NW_2016.03.17.3242564", 1362, 1367],
    #             ["VOA_EN_NW_2016.03.17.3242564", 1362, 1367]
    #         ],
    #         "qnode": "NIL",
    #         "qlabel": "NIL",
    #         "text": "United States", one canonical mention.
    #     }
    # }
    output_entity_dict = {}

    lines = entity_cs_string.split('\n')
    entity_id_to_lines = {}

    # read out all the lines related to one entity id.
    for i in range(len(lines)):
        line = lines[i]
        if len(line) != 0:
            parsed_line = line.split('\t')
            entity_id = parsed_line[0]
            
            if entity_id not in entity_id_to_lines:
                entity_id_to_lines[entity_id] = [line]
            else:
                entity_id_to_lines[entity_id].append(line)
    
    # split the entities
    for entity_id in entity_id_to_lines:
        entity_lines = entity_id_to_lines[entity_id] 

        mentions_list = [] # list of [doc_name, start_char, end_char]
        # print(entity_lines)
        # print(entity_lines[1].split('\t'))
        text = entity_lines[1].split('\t')[2][1:-1]
        qnode = "NIL"
        qlabel = "NIL"

        for line in entity_lines:
            split_line = line.split('\t')
            if split_line[1].endswith("mention"):
                occur = split_line[3].split(":")
                doc_name = occur[0]
                start_idx = int(occur[1].split('-')[0])
                end_idx = int(occur[1].split('-')[1])
                if end_idx - start_idx <= 1:
                    continue
                if (doc_name, start_idx, end_idx) not in mentions_list:
                    mentions_list.append((doc_name, start_idx, end_idx))
                
                if split_line[1].startswith("canonical"):
                    text = split_line[2][1:-1]

            if split_line[1] == "link":
                if split_line[2].endswith('\n'):
                    qnode = split_line[2][:-1]
                else:
                    qnode = split_line[2]

            if split_line[1] == "qlabel":
                if split_line[2].endswith('\n'):
                    qlabel = split_line[2][:-1]
                else:
                    qlabel = split_line[2]
            
            if split_line[1] == "type":
                entity_type = split_line[2].split('#')[-1]
        
        if len(mentions_list) == 0:
            continue
        entity_info = {
            "type": entity_type,
            "mentions": mentions_list,
            "qnode": qnode,
            "qlabel": qlabel,
            "text": text
        }
        output_entity_dict.update({entity_id: deepcopy(entity_info)})

    with open("entity_debug.json", 'w', encoding="utf-8") as f:
        f.write(json.dumps(output_entity_dict, indent=4))

    return output_entity_dict


def read_xpo(xpo_json_dir):
    with open(xpo_json_dir, 'r', encoding="utf-8") as f:
        xpo_json = json.loads(f.read())
    
    event_type_mapping, role_type_mapping = {}, {}
    
    for qnode, event in xpo_json["events"].items():
        if "ldc_types" in event:
            qnode_str = qnode.split('_')[1]
            qlabel = event["name"]
            # print(event["ldc_types"])
            ldc_types = event["ldc_types"]
            # print(len(ldc_types))
            for ldc_type in ldc_types:
                ldc_type_name = ldc_type["name"].lower()
                if ldc_type_name not in event_type_mapping:
                    event_type_mapping[ldc_type_name] = [(qnode_str, qlabel)]
                else:
                    event_type_mapping[ldc_type_name].append((qnode_str, qlabel))
                # print(ldc_type.keys())

                if "ldc_arguments" in ldc_type:
                    arguments = ldc_type["ldc_arguments"]
                    for argument in arguments:
                        total_role_name = (ldc_type_name + '_' + argument["ldc_name"]).lower()
                        dwd_arg_name = argument["dwd_arg_name"]
                        if total_role_name not in role_type_mapping:
                            role_type_mapping[total_role_name] = [dwd_arg_name]
                        else:
                            role_type_mapping[total_role_name].append(dwd_arg_name)

    # with open("event_map.json", 'w', encoding="utf-8") as f1:
    #     f1.write(json.dumps(event_type_mapping, indent=4))
    # with open("role_map.json", 'w', encoding="utf-8") as f2:
    #     f2.write(json.dumps(role_type_mapping, indent=4))
    
    return event_type_mapping, role_type_mapping 


def transform_ie_graph(entity_dict, event_dict, temporal_list, event_type_mapping, role_type_mapping):
    # print(event_dict)
    # print(temporal_list)
    event_graph = nx.DiGraph()
    event_node_idx = {}
    event_node_num = 0
    primitive_ids = []
    event_temps = {} # {event_idx: [list of descendant event idxs]}, keys and values include both primitive events and non-primitive events.
    not_in_num = 0

    for event_id, event in event_dict.items():
        event_type = event["type"].lower()

        if event_type in event_type_mapping:
            linkings = event_type_mapping[event_type]
            qnodes = [linking[0] for linking in linkings]
            qlabels = [linking[1] for linking in linkings]

            provenances = [(mention[0], mention[1], mention[2]) for mention in event["mentions"]]
            event_graph.add_node(event_node_num, id=event_id, qnodes=qnodes, qlabels=qlabels, name=qlabels[0], description=event["mentions"][0][-1], trigger=event["mentions"][0][-2], primitive=True, children=[], importances=[], children_gate="N/A", ta1exp="", provenance=provenances)

            event_node_idx.update({event_id: event_node_num})
            primitive_ids.append(event_node_num)
            event_node_num += 1
        else:
            not_in_num += 1

    # read in temporal relation
    for item in temporal_list:
        start, end = item[0], item[1]
        if start in event_node_idx and end in event_node_idx:
            start_id, end_id = event_node_idx[start], event_node_idx[end]
            if start_id not in event_temps:
                event_temps[start_id] = [end_id]
            else:
                event_temps[start_id].append(end_id)
            event_graph.add_edge(start_id, end_id, type="temporal") 


    event_child_idxs = {} # expanding event children

    # read the entity-entity relation graph
    entity_graph = nx.DiGraph()
    entity_node_idx = {}
    entity_node_num = 0

    for entity_id, entity in entity_dict.items():
        qnodes, qlabels = [entity["qnode"]], [entity["qlabel"]]
        provenances = [(mention[0], mention[1], mention[2]) for mention in entity["mentions"]]
        entity_graph.add_node(entity_node_num, id=entity_id, name=qlabels[0], qnodes=qnodes, qlabels=qlabels, key=qlabels, provenance=provenances, text=entity["text"])
        entity_node_idx.update({entity_id: entity_node_num})
        entity_node_num += 1 
    
    # read arguments
    # read participants: event argument roles:
    # output: arg_name_dict: {event_idx: {ta2_entity_idx: role_name}} // role_name is the keyword or other textual descriptions of the event argument role.
    # output: arg_id_dict: {event_idx: {ta2_entity_idx: role_id}} // role_arg_id is the @id field for an argument
    arg_name_dict, arg_id_dict = {}, {}

    # print(role_type_mapping)
    for event_id, event in event_dict.items():
        event_type = event["type"].lower()

        if event_type in event_type_mapping:
            event_idx = event_node_idx[event_id]
            if event_idx not in arg_name_dict:
                arg_name_dict.update({event_idx: {}})
                arg_id_dict.update({event_idx: {}})

            args = event["arguments"]     
            for arg in args:
                entity_id, role_name = arg[0], arg[1]
                role_name_lower = role_name.lower()
                # print(role_name_lower)
                if role_name_lower in role_type_mapping:
                    xpo_role_name = role_type_mapping[role_name_lower][0]
                    if xpo_role_name is None:
                        continue
                    if entity_id not in entity_node_idx:
                        continue
                    entity_idx = entity_node_idx[entity_id]

                    arg_name_dict[event_idx].update({entity_idx: xpo_role_name})
                    arg_id_dict[event_idx].update({entity_idx: xpo_role_name})

    return (event_graph, event_node_idx, event_temps, event_child_idxs), (entity_graph, entity_node_idx), (arg_name_dict, arg_id_dict), primitive_ids


def read_ie_cluster(entity_cs_string, event_cs_string, temp_en_string, temp_es_string, event_type_mapping, role_type_mapping, en_data, es_data):
    entity_dict = process_entities_cluster(entity_cs_string)
    event_dict = process_events_cluster(event_cs_string, en_data, es_data)
    temporal_list = read_temporal_list(temp_en_string, temp_es_string)

    (event_graph, event_node_idx, event_temps, event_child_idxs), (entity_graph, entity_node_idx), (arg_name_dict, arg_id_dict), primitive_ids = transform_ie_graph(entity_dict, event_dict, temporal_list, event_type_mapping, role_type_mapping)

    expanded_temps = expand_temporal(event_temps, event_child_idxs, primitive_ids)
    return (event_graph, event_node_idx, expanded_temps, event_child_idxs), (entity_graph, entity_node_idx), (arg_name_dict, arg_id_dict), primitive_ids



if __name__ == "__main__":
    
    xpo_dir = "./xpo_v3.2_freeze_exp.json"
    em, rm = read_xpo(xpo_dir)

    with open("./task1_graphs_qz9/coref.json", 'r', encoding="utf-8") as f:
        coref = json.loads(f.read())
    
    with open("./task1_graphs_qz9/temporal.json", 'r', encoding="utf-8") as f:
        temporal = json.loads(f.read())

    entity_cs_string = coref["coref"]["entity.cs"]
    event_cs_string = coref["coref"]["event.cs"]
    # with open("./try.cs", 'w', encoding="utf-8") as f:
        # temporal = json.loads(f.read())
        # f.write(event_cs_string)
    with open("./file.xml", 'w', encoding="utf-8") as f:
        f.write(coref["data"]["en"][0])
    temp_en_string = temporal["temporal_relation"]["en"]["temporal_relation.cs"]
    temp_es_string = temporal["temporal_relation"]["es"]["temporal_relation.cs"]

    en_data = coref["data"]["en"]
    es_data = coref["data"]["es"]

    read_ie_cluster(entity_cs_string, event_cs_string, temp_en_string, temp_es_string, em, rm, en_data, es_data)