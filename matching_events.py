from nltk.corpus import wordnet
from utils import extract_headword
from event_temporal import expand_temporal
from utils import cal_temp_num

import numpy as np
import random
import re
import difflib
import json


def get_similarity(string_a, string_b):
    return difflib.SequenceMatcher(a=string_a.lower(), b=string_b.lower()).ratio()


def extract_headword(input_string):
    # we extract the first token of the input string as the head word.
    # the strings are splitted by - and space.
    input_splits = re.split(' |_', input_string)
    output_string = input_splits[0].lower()
    return output_string


def get_keyword(node):
    if len(node["qlabels"]) == 0:
        name_splits = re.split(' |_', node["name"])
        name_key = name_splits[0].lower()
        return name_key
    else:
        return extract_headword(node["qlabels"][0])


def generate_qlabel_to_idx(instance_nodes, schema_nodes):
    # INPUT: list of instance nodes and schema nodes
    # OUTPUT: {"instance_qlabel": [[list of instance idxs], [list of schema idxs]]}
    qlabel_to_idx = {}
    for i,node in instance_nodes:
        if node["primitive"]:
            keyword = node["key"]
            if keyword not in qlabel_to_idx:
                qlabel_to_idx.update({keyword: [[i], []]})
            else:
                qlabel_to_idx[keyword][0].append(i)

    for i,node in schema_nodes:
        if node["primitive"]:
            keyword = node["key"]
            if keyword in qlabel_to_idx:
                qlabel_to_idx[keyword][1].append(i)

    return qlabel_to_idx

def generate_one_mapping(qlabel_to_idx):
    # FUNCTION: randomly generate one mapping for all the many-one, many-many, and one-many mappings
    # INPUT: qlabel_to_idx: {"instance_qlabel": [[list of instance idxs], [list of schema idxs]]}
    # OUTPUT: generate one mapping randomly {inst_idx: schema_idx}
    init_dict = {}
    for keyword in qlabel_to_idx:
        inst_idxs, schema_idxs = qlabel_to_idx[keyword]
        inst_num, schema_num = len(inst_idxs), len(schema_idxs)
        if inst_num >= 1 and schema_num >= 1 and (inst_num * schema_num != 1):
            if inst_num > schema_num:
                sampled_idxs = random.sample(range(0, inst_num), schema_num)
                for i,idx in enumerate(sampled_idxs):
                    init_dict.update({inst_idxs[idx]: schema_idxs[i]})
            else:
                sampled_idxs = random.sample(range(0, schema_num), inst_num)
                for i,idx in enumerate(sampled_idxs):
                    init_dict.update({inst_idxs[i]: schema_idxs[idx]})
    # print(init_dict)
    return init_dict

def generate_one_matching(instance_nodes, schema_nodes, qlabel_to_idx, threshold):
    # FUNCTION: randomly generate one matching matching_idx, conf
    # INPUT: qlabel_to_idx: {"instance_qlabel": [[list of instance idxs], [list of schema idxs]]}
    # OUTPUT: two lists with length instance_num
    instance_num, schema_num = len(instance_nodes), len(schema_nodes)
    init_mapping, init_conf = [-1 for m in range(instance_num)], [0.0 for n in range(instance_num)]

    mapped_inst_idxs, mapped_schema_idxs = set(), set()

    # Firstly, we lock down all the one-to-one mappings
    for keyword in qlabel_to_idx:
        inst_idxs, schema_idxs = qlabel_to_idx[keyword]
        if len(inst_idxs) == 1 and len(schema_idxs) == 1:
            init_mapping[inst_idxs[0]] = schema_idxs[0]
            init_conf[inst_idxs[0]] = 1.0
            mapped_inst_idxs.add(inst_idxs[0])
            mapped_schema_idxs.add(schema_idxs[0])

    
    # Secondly, we randomly generate a mapping dict for many-many, many-one, one-many
    map_dict = generate_one_mapping(qlabel_to_idx)
    for key,value in map_dict.items():
        init_mapping[key] = value
        init_conf[key] = 1.0
        mapped_inst_idxs.add(key)
        mapped_schema_idxs.add(value)
    
    # Thirdly, we obtain all the remaining possible mappings
    for i,inode in instance_nodes:
        if i not in mapped_inst_idxs:
            if inode["primitive"] and (i not in mapped_schema_idxs):
                inst_key = inode["key"]
                inst_wordnets = wordnet.synsets(inst_key)
                s_idxs, s_confs = [], []
                if len(inst_wordnets) == 0:
                    # match through string similarity
                    for j,snode in schema_nodes:
                        if (j not in mapped_schema_idxs) and snode["primitive"]:
                            sim = get_similarity(inst_key, snode["key"])
                            s_idxs.append(j)
                            s_confs.append(sim)
                else:
                    # match through wordnet similarity
                    for j,snode in schema_nodes:
                        if (j not in mapped_schema_idxs) and snode["primitive"]:
                            schema_key = snode["key"]
                            schema_wordnets = wordnet.synsets(schema_key)
                            if len(schema_wordnets) != 0:
                                sim = inst_wordnets[0].wup_similarity(schema_wordnets[0])
                                s_idxs.append(j)
                                s_confs.append(sim)
                
                if len(s_idxs) != 0:
                    max_idx = np.argmax(s_confs)
                    if s_confs[max_idx] >= threshold:
                        mapped_inst_idxs.add(i)
                        mapped_schema_idxs.add(s_idxs[max_idx])
                        init_mapping[i] = s_idxs[max_idx]
                        init_conf[i] = s_confs[max_idx]
            
    return init_mapping, init_conf


def generate_matchings(instance_nodes, schema_nodes, qlabel_to_idx, threshold, num):
    accu_num = 0
    mappings, confs = [], []
    while len(mappings) < num:
        one_mapping, one_conf = generate_one_matching(instance_nodes, schema_nodes, qlabel_to_idx, threshold)
        if one_mapping not in mappings:
            mappings.append(one_mapping.copy())
            confs.append(one_conf.copy())
            accu_num = 0
        else:
            accu_num += 1
        if accu_num > 10:
            break
    return mappings, confs 


def calculate_violate_num(mapping, schema_nodes, inst_temp_dict, schema_temp_dict):
    # the two temp dicts are both expanded temp_dicts
    # print(schema_temp_dict.keys())
    violate_num = 0
    inst_mapped_idxs, schema_mapped_idxs = [], []
    for i,idx in enumerate(mapping):
        if idx != -1:
            inst_mapped_idxs.append(i)
            schema_idx = schema_nodes[idx]["idx"]
            schema_mapped_idxs.append(schema_idx)
    
    length = len(inst_mapped_idxs)
    for i in range(length):
        for j in range(i+1, length):
            inst_s, inst_e = inst_mapped_idxs[i], inst_mapped_idxs[j]
            schema_s, schema_e = schema_mapped_idxs[i], schema_mapped_idxs[j]
            # print(schema_s, schema_e)
            if (inst_e in inst_temp_dict[inst_s] and schema_s in schema_temp_dict[schema_e]) or (inst_s in inst_temp_dict[inst_e] and schema_e in schema_temp_dict[schema_s]):
                violate_num += 1

    return violate_num


def match_one_schema(instance_graph, schema_graph, expanded_inst_temp_dict, expanded_schema_temp_dict, threshold, candidate_num):
    # schema_graph, instance_graph: nx graphs.
    # schema_temps, instance_temps: expanded_temp_dict
    # OUTPUT: matching_res, matching_conf: list of length INSTANCE_NUM, each item is a schema node idx.
    # print("Reading Graphs done.")
    # instance_num = len(instance_graph.nodes())
    # schema_num = len(schema_graph.nodes())
    
    # inst_temp_dict, inst_event_children, inst_prim_ids = inst_temps
    # schema_temp_dict, schema_event_children, schema_prim_ids = schema_temps
    # # print(cal_temp_num(inst_temps[0]))
    # # print(cal_temp_num(schema_temps[0]))
    # expanded_inst_temp_dict = expand_temporal(inst_temp_dict, inst_event_children, inst_prim_ids)
    # expanded_schema_temp_dict = expand_temporal(schema_temp_dict, schema_event_children, schema_prim_ids)
    # print(cal_temp_num(expanded_inst_temp_dict))
    # print(cal_temp_num(expanded_schema_temp_dict))

    # print("Temporal dict done.")

    instance_nodes = instance_graph.nodes(data=True)
    schema_nodes = schema_graph.nodes(data=True)

    for i,node in instance_nodes:
        node["key"] = get_keyword(node)
    for i,node in schema_nodes:
        node["key"] = get_keyword(node)

    qlabel_idx = generate_qlabel_to_idx(instance_nodes, schema_nodes) # {qlabel: [[1,3,4], [2,4,5]]}
    
    cand_maps, cand_confs = generate_matchings(instance_nodes, schema_nodes, qlabel_idx, threshold, candidate_num)

    violate_nums = []
    for cand_map in cand_maps:
        num = calculate_violate_num(cand_map, schema_nodes, expanded_inst_temp_dict, expanded_schema_temp_dict)
        violate_nums.append(num)
    
    min_idx = np.argmin(violate_nums)
    matching_res = cand_maps[min_idx]
    matching_conf = cand_confs[min_idx]

    matching_num = sum([0 if idx == -1 else 1 for idx in matching_res])
    return matching_res, matching_conf, matching_num


# def match_events(instance_graph, schema_graph, expanded_inst_temp_dict, expanded_schema_temp_dict, threshold, candidate_num):
def match_events(instance_graph, schema_events, expanded_inst_temp_dict, threshold, candidate_num):
    
    num_dict, results_dict = {}, {}
    for root_id in schema_events:
        schema_nodes = schema_events[root_id]["nx_graph"].nodes(data=True)
        primitive_num = len(schema_events[root_id]["prim_child_idxs"])
        res, conf, num = match_one_schema(instance_graph, schema_events[root_id]["nx_graph"], expanded_inst_temp_dict, schema_events[root_id]["temporal"], threshold, candidate_num)
        for i,item in enumerate(res):
            if item != -1:
                res[i] = schema_nodes[item]["idx"]

        num_dict[root_id] = {"matched_num": num, "total_num": primitive_num}
        results_dict[root_id] = (res, conf)
    
    # print(json.dumps(num_dict, indent=4))

    return results_dict, num_dict 


if __name__ == "__main__":
    # from human_graph import read_human_graph
    # from schema import read_schema

    # # human_graph_dir = "./Quizlet8_GraphG/ce2002abridged_GraphG.json"
    # # human_graph_dir = "./Quizlet8_GraphG/ce2002full_GraphG.json"
    # schema_graph_dir = "./Quizlet8-TA1/Schemas/resin-schemalib.json"
    # # schema_graph_dir = "./Quizlet8-TA1/Schemas/Justice_Consume_Contamination.json"

    # (event_graph_s, event_node_idx_s, event_temps_s, event_child_idxs_s), (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s), prim_ids_s = read_schema(schema_graph_dir)
    # (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), prim_ids_h = read_human_graph(human_graph_dir)
    
    # res, conf = match_events(event_graph_h, event_graph_s, (event_temps_h, event_child_idxs_h, prim_ids_h), (event_temps_s, event_child_idxs_s, prim_ids_s), 0.7, 10)
    # print(res)
    # print(conf)

    # # check if the results make sense
    # # for i,idx in enumerate(res):

    from ie_graph import *
    from schema import *

    xpo_dir = "./xpo_v4.json"
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

    (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), primitive_ids_h = read_ie_cluster(entity_cs_string, event_cs_string, temp_en_string, temp_es_string, em, rm, en_data, es_data)

    orgs = ["cmu", "ibm", "isi", "sbu", "resin"]

    for org in orgs:
        # print(org)
        schema_file_dir = "./schemas_qz9/" + org + "-schemalib.json"
        schema_events, event_node_idxs, entity_graph, entity_node_idxs, primitive_idxs, global_graph = read_schema(schema_file_dir)
        # match_one_schema(event_graph_h, schema_events['sbu:Events/15022/natural-disaster-progression']["nx_graph"], event_temps_h, schema_events['sbu:Events/15022/natural-disaster-progression']["temporal"], 0.8, 1)
        match_events(event_graph_h, schema_events, event_temps_h, 0.75, 2)

