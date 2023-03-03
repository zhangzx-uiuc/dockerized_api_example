from human_graph import read_human_graph
from schema import read_schema
from ie_graph import read_ie_cluster

from matching_graphs import matching_graphs
from prediction import baseline_prediction, new_prediction, generate_pred_values
from write_sdf import generate_task1_instance, generate_task2_instance
from visualization import visualize_task1_str
from copy import deepcopy

import copy
import json
import random
import re
import os


def matching_one_task2_pair(human_g_dir, schema_dir, matching_root_dir, threshold, num, org, doc):
    # read human graph
    (event_graph_s, event_node_idx_s, event_temps_s, event_child_idxs_s), (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s), prim_ids_s = read_schema(schema_dir)
    (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), prim_ids_h = read_human_graph(human_g_dir)


    event_maps, entity_maps, arg_fillers = matching_graphs((event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), prim_ids_h, (entity_graph_h, entity_node_idx_h), \
                                                            (arg_name_dict_h, arg_id_dict_h), (event_graph_s, event_node_idx_s, event_temps_s, event_child_idxs_s), prim_ids_s, \
                                                            (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s), threshold, num, org)

    event_mapping_dir = os.path.join(matching_root_dir, "event-mappings")
    if not os.path.exists(event_mapping_dir):
        os.mkdir(event_mapping_dir)
    
    entity_mapping_dir = os.path.join(matching_root_dir, "entity-mappings")
    if not os.path.exists(entity_mapping_dir):
        os.mkdir(entity_mapping_dir)
    
    arg_filler_dir = os.path.join(matching_root_dir, "arg-fillers")
    if not os.path.exists(arg_filler_dir):
        os.mkdir(arg_filler_dir)
    
    matched_ids_dir = os.path.join(matching_root_dir, "matched-ids")
    if not os.path.exists(matched_ids_dir):
        os.mkdir(matched_ids_dir)

    with open(os.path.join(event_mapping_dir, (org+'-'+doc+'.json')), 'w', encoding="utf-8") as f1:
        output_string = json.dumps(event_maps)
        f1.write(output_string)
    with open(os.path.join(entity_mapping_dir, (org+'-'+doc+'.json')), 'w', encoding="utf-8") as f2:
        output_string = json.dumps(entity_maps)
        f2.write(output_string)
    with open(os.path.join(arg_filler_dir, (org+'-'+doc+'.json')), 'w', encoding="utf-8") as f3:
        output_string = json.dumps(arg_fillers)
        f3.write(output_string)
    
    rev_event_node_idx_s = {v:k for k,v in event_node_idx_s.items()}
    matched_ids = []
    for seidx in event_maps:
        if rev_event_node_idx_s[seidx] not in matched_ids:
            matched_ids.append(rev_event_node_idx_s[seidx])
    with open(os.path.join(matched_ids_dir, (org+'-'+doc+'.json')), 'w', encoding="utf-8") as f4:
        output_string = json.dumps(matched_ids)
        f4.write(output_string)


def matching_one_task1_pair(event_dicts, ie_cluster_dir, schema_dir, matching_root_dir, threshold, num, org, doc):
    # event_dicts: (event_type_mapping, role_type_mapping)
    (event_graph_s, event_node_idx_s, event_temps_s, event_child_idxs_s), (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s), prim_ids_s = read_schema(schema_dir)
    (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), prim_ids_h = read_ie_cluster(ie_cluster_dir, event_dicts[0], event_dicts[1])


    event_maps, entity_maps, arg_fillers = matching_graphs((event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), prim_ids_h, (entity_graph_h, entity_node_idx_h), \
                                                            (arg_name_dict_h, arg_id_dict_h), (event_graph_s, event_node_idx_s, event_temps_s, event_child_idxs_s), prim_ids_s, \
                                                            (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s), threshold, num, org)

    event_mapping_dir = os.path.join(matching_root_dir, "event-mappings")
    if not os.path.exists(event_mapping_dir):
        os.mkdir(event_mapping_dir)
    
    entity_mapping_dir = os.path.join(matching_root_dir, "entity-mappings")
    if not os.path.exists(entity_mapping_dir):
        os.mkdir(entity_mapping_dir)
    
    arg_filler_dir = os.path.join(matching_root_dir, "arg-fillers")
    if not os.path.exists(arg_filler_dir):
        os.mkdir(arg_filler_dir)
    
    matched_ids_dir = os.path.join(matching_root_dir, "matched-ids")
    if not os.path.exists(matched_ids_dir):
        os.mkdir(matched_ids_dir)

    with open(os.path.join(event_mapping_dir, (org+'-'+doc+'.json')), 'w', encoding="utf-8") as f1:
        output_string = json.dumps(event_maps)
        f1.write(output_string)
    with open(os.path.join(entity_mapping_dir, (org+'-'+doc+'.json')), 'w', encoding="utf-8") as f2:
        output_string = json.dumps(entity_maps)
        f2.write(output_string)
    with open(os.path.join(arg_filler_dir, (org+'-'+doc+'.json')), 'w', encoding="utf-8") as f3:
        output_string = json.dumps(arg_fillers)
        f3.write(output_string)
    
    rev_event_node_idx_s = {v:k for k,v in event_node_idx_s.items()}
    matched_ids = []
    for seidx in event_maps:
        if rev_event_node_idx_s[seidx] not in matched_ids:
            matched_ids.append(rev_event_node_idx_s[seidx])
    with open(os.path.join(matched_ids_dir, (org+'-'+doc+'.json')), 'w', encoding="utf-8") as f4:
        output_string = json.dumps(matched_ids)
        f4.write(output_string)


def output_task2(matching_root_dir, human_g_dir, schema_dir, pred_res_dict, output_dir, digits_list, pred_threshold, doc, org, org_urls):
    # read human graph
    # pattern = re.compile(r'ibm:|cmu:|isi:|sbu:')
    # org_pattern = re.compile('"ta1ref":"resin:')

    with open(os.path.join(matching_root_dir, "event-mappings", (org+'-'+doc+'.json')), 'r', encoding="utf-8") as f1:
        str_event_maps = json.loads(f1.read())
    with open(os.path.join(matching_root_dir, "entity-mappings", (org+'-'+doc+'.json')), 'r', encoding="utf-8") as f2:
        str_entity_maps = json.loads(f2.read())
    with open(os.path.join(matching_root_dir, "arg-fillers", (org+'-'+doc+'.json')), 'r', encoding="utf-8") as f3:
        str_arg_fillers = json.loads(f3.read())
    with open(os.path.join(matching_root_dir, "matched-ids", (org+'-'+doc+'.json')), 'r', encoding="utf-8") as f4:
        matched_ids = json.loads(f4.read())
    
    event_maps, entity_maps, arg_fillers = {}, {}, {}
    for k,v in str_event_maps.items():
        event_maps.update({int(k): v})
    for k,v in str_entity_maps.items():
        new_v = {}
        for x,y in v.items():
            new_v.update({int(x): y})
        entity_maps.update({int(k): new_v})
    for k,v in str_arg_fillers.items():
        arg_fillers.update({int(k):v})

    (event_graph_s, event_node_idx_s, event_temps_s, event_child_idxs_s), (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s), prim_ids_s = read_schema(schema_dir)
    (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), prim_ids_h = read_human_graph(human_g_dir)

    human_event_nodes = event_graph_h.nodes(data=True)
    human_entity_nodes = entity_graph_h.nodes(data=True)

    # read schema dict
    with open(schema_dir, 'r', encoding="utf-8") as f:
        schema_dict = json.loads(f.read())
    
    with open(human_g_dir, 'r', encoding="utf-8") as f:
        human_dict = json.loads(f.read())["instances"][0]

    # event_maps, entity_maps, arg_fillers = read_matching_results(input_task2_dir)
    # pred_results = new_prediction(event_graph_s, event_node_idx_s, arg_id_dict_s, arg_id_dict_h, event_maps, entity_maps, arg_fillers, pred_res_dict[(org, doc)], pred_threshold)
    pred_res_dict = generate_pred_values(matched_ids, event_node_idx_s, prim_ids_s)
    pred_results = new_prediction(event_graph_s, event_node_idx_s, arg_id_dict_s, arg_id_dict_h, event_maps, entity_maps, arg_fillers, pred_res_dict, pred_threshold)

    # predict_idxs, predict_provs = baseline_prediction(event_graph_s, arg_name_dict_s, event_maps, entity_maps, arg_fillers)

    rev_event_id_h = {value:key for key,value in event_node_idx_h.items()}
    rev_entity_id_h = {value:key for key,value in entity_node_idx_h.items()}

    rev_event_id_s = {value:key for key,value in event_node_idx_s.items()}
    rev_entity_id_s = {value:key for key,value in entity_node_idx_s.items()}
    # print(rev_entity_id_s.keys())
    # print(arg_id_dict_s)
    instance, digits_list = generate_task2_instance((event_maps, entity_maps, arg_fillers), (rev_event_id_s, rev_entity_id_s), (rev_event_id_h, rev_entity_id_h), (event_graph_h, entity_graph_h), (event_graph_s, entity_graph_s), schema_dict, human_dict, digits_list, predict_results=pred_results)
    digit = digits_list.pop(0)
    instance["@id"] = "resin:Instances/" + str(digit) + "/"

    ta2_human_output = {
        "@context": [
            "https://kairos-sdf.s3.amazonaws.com/context/kairos-v1.3.1.jsonld",
            {
                "resin": "https://blender.cs.illinois.edu/kairos/"
            }
        ],
        "sdfVersion": "1.3.1",
        "@id": "resin:Submissions/TA2",
        "version": "resin / 1.0.0",
        "ceID": human_g_dir.split('/')[-1].split('.')[0].split('_')[0],
        "ta2": True,
        "task2": True,
        "instances": [instance]
    }

    ta2_human_output["@context"][-1].update({org: org_urls[org]})

    with open(output_dir, 'w', encoding="utf-8") as f:
        output_string = json.dumps(ta2_human_output, indent=4)
        f.write(output_string)


def output_task1(matching_root_dir, human_g_dir, schema_dir, pred_res_dict, event_dicts, output_dir, digits_list, pred_threshold, doc, org, org_urls, prov_dict, prov_linker):
    # read human graph
    # pattern = re.compile(r'ibm:|cmu:|isi:|sbu:')
    # org_pattern = re.compile('"ta1ref":"resin:')

    with open(os.path.join(matching_root_dir, "event-mappings", (org+'-'+doc+'.json')), 'r', encoding="utf-8") as f1:
        str_event_maps = json.loads(f1.read())
    with open(os.path.join(matching_root_dir, "entity-mappings", (org+'-'+doc+'.json')), 'r', encoding="utf-8") as f2:
        str_entity_maps = json.loads(f2.read())
    with open(os.path.join(matching_root_dir, "arg-fillers", (org+'-'+doc+'.json')), 'r', encoding="utf-8") as f3:
        str_arg_fillers = json.loads(f3.read())
    with open(os.path.join(matching_root_dir, "matched-ids", (org+'-'+doc+'.json')), 'r', encoding="utf-8") as f4:
        matched_ids = json.loads(f4.read())
    
    event_maps, entity_maps, arg_fillers = {}, {}, {}
    for k,v in str_event_maps.items():
        event_maps.update({int(k): v})
    for k,v in str_entity_maps.items():
        new_v = {}
        for x,y in v.items():
            new_v.update({int(x): y})
        entity_maps.update({int(k): new_v})
    for k,v in str_arg_fillers.items():
        arg_fillers.update({int(k):v})
    # print(event_maps)
    

    (event_graph_s, event_node_idx_s, event_temps_s, event_child_idxs_s), (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s), prim_ids_s = read_schema(schema_dir)
    (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), prim_ids_h = read_ie_cluster(human_g_dir, event_dicts[0], event_dicts[1])

    human_event_nodes = event_graph_h.nodes(data=True)
    human_entity_nodes = entity_graph_h.nodes(data=True)

    # read schema dict
    with open(schema_dir, 'r', encoding="utf-8") as f:
        schema_dict = json.loads(f.read())

    # event_maps, entity_maps, arg_fillers = read_matching_results(input_task2_dir)
    # pred_results = new_prediction(event_graph_s, event_node_idx_s, arg_id_dict_s, arg_id_dict_h, event_maps, entity_maps, arg_fillers, pred_res_dict[(org, doc)], pred_threshold)
    pred_res_dict = generate_pred_values(matched_ids, event_node_idx_s, prim_ids_s)
    pred_results = new_prediction(event_graph_s, event_node_idx_s, arg_id_dict_s, arg_id_dict_h, event_maps, entity_maps, arg_fillers, pred_res_dict, pred_threshold)

    # predict_idxs, predict_provs = baseline_prediction(event_graph_s, arg_name_dict_s, event_maps, entity_maps, arg_fillers)

    rev_event_id_h = {value:key for key,value in event_node_idx_h.items()}
    rev_entity_id_h = {value:key for key,value in entity_node_idx_h.items()}

    rev_event_id_s = {value:key for key,value in event_node_idx_s.items()}
    rev_entity_id_s = {value:key for key,value in entity_node_idx_s.items()}
    # print(rev_entity_id_s.keys())
    # print(arg_id_dict_s)
    instance, digits_list = generate_task1_instance((event_maps, entity_maps, arg_fillers), (rev_event_id_s, rev_entity_id_s), (event_graph_h, entity_graph_h), (event_graph_s, entity_graph_s), schema_dict, digits_list, pred_results, prov_dict)
    # mapping_results, rev_dicts_s, human_graphs, schema_graphs, schema_dict, digits_list, predict_results, prov_dict
    digit = digits_list.pop(0)
    instance["@id"] = "resin:Instances/" + str(digit) + "/"

    prov_items = []
    for key,value in prov_linker.items():
        prov_items.append(copy.deepcopy(value))

    ta2_human_output = {
        "@context": [
            "https://kairos-sdf.s3.amazonaws.com/context/kairos-v1.3.1.jsonld",
            {
                "resin": "https://blender.cs.illinois.edu/kairos/"
            }
        ],
        "sdfVersion": "1.3.1",
        "@id": "resin:Submissions/TA2",
        "version": "resin / 1.0.0",
        "ceID": human_g_dir.split('/')[-1].split('.')[0].split('_')[0],
        "ta2": True,
        "task2": True,
        "instances": [instance],
        "provenanceData": prov_items
    }

    ta2_human_output["@context"][-1].update({org: org_urls[org]})

    with open(output_dir, 'w', encoding="utf-8") as f:
        output_string = json.dumps(ta2_human_output, indent=4)
        f.write(output_string)


def generate_prov_info(entity_graph_h, event_graph_h, digits_list):
    human_entity_nodes = entity_graph_h.nodes(data=True)
    human_event_nodes = event_graph_h.nodes(data=True)
    prov_dict = {}
    prov_linker = {}

    for i,node in human_event_nodes:
        node_provs = node["provenance"]
        for prov in node_provs:
            doc_id, start, end = prov
            length = end - start

            digit = digits_list.pop(0)
            prov_id = "resin:Provenance/" + digit + "/"
            prov_dict.update({prov: prov_id})

            new_prov_data = {
                "provenanceID": prov_id,
                "childID": doc_id,
                "mediaType": "text/plain",
                "offset": start,
                "length": length
            }
            prov_linker.update({prov: new_prov_data})
    
    for i,node in human_entity_nodes:
        node_provs = node["provenance"]
        for prov in node_provs:
            doc_id, start, end = prov
            length = end - start

            digit = digits_list.pop(0)
            prov_id = "resin:Provenance/" + digit + "/"
            prov_dict.update({prov: prov_id})

            new_prov_data = {
                "provenanceID": prov_id,
                "childID": doc_id,
                "mediaType": "text/plain",
                "offset": start,
                "length": length
            }
            prov_linker.update({prov: new_prov_data})

    return prov_dict, prov_linker, digits_list


def task1_predict(ceid, team, team_urls, schema_dir, entity_cs_string, event_cs_string, temp_en_string, temp_es_string, em, rm, en_data, es_data, matching_threshold, prediction_threshold, cand_num, topn):
    digits_list = [str(i).zfill(5) for i in range(0, 100000)]

    (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), primitive_ids_h = read_ie_cluster(entity_cs_string, event_cs_string, temp_en_string, temp_es_string, em, rm, en_data, es_data)
    schema_events, event_node_idxs, entity_graph, entity_node_idxs, primitive_idxs, global_graph = read_schema(schema_dir)
    with open(schema_dir, 'r', encoding="utf-8") as f:
        schema_dict = json.loads(f.read())

    matching_results, matching_num = matching_graphs(event_graph_h, event_temps_h, arg_name_dict_h, schema_events, matching_threshold, cand_num, team)
    matched = {k:v["matched_num"] for k,v in matching_num.items()}
    top_id_list = [i[0] for i in sorted(matched.items(), key=lambda item:item[1], reverse=True)]

    prov_dict, prov_linker, digits_list = generate_prov_info(entity_graph_h, event_graph_h, digits_list)
    prov_items = []
    for key,value in prov_linker.items():
        prov_items.append(copy.deepcopy(value))

    rev_event_id_s = {v:k for k,v in event_node_idxs.items()}
    rev_entity_id_s = {v:k for k,v in entity_node_idxs.items()}

    instances = []

    for i in range(topn):
        if i < len(top_id_list):
            root_id = top_id_list[i]
            confidence = matching_num[root_id]["matched_num"] / len(event_node_idx_h)

            evt_map = matching_results[root_id]["event_maps"]
            ent_map = matching_results[root_id]["entity_maps"]
            arg_filler = matching_results[root_id]["arg_fillers"]

            pred_dict, matched_ids = generate_pred_values(evt_map, event_node_idxs, primitive_idxs)

            pidxs, pprovs, pargs = new_prediction(schema_events[root_id]["prim_child_idxs"], event_node_idxs, schema_events[root_id]["arg_id_dict"], arg_id_dict_h, evt_map, ent_map, arg_filler, pred_dict, prediction_threshold)

            instance, digits_list = generate_task1_instance(schema_events[root_id]["prim_child_idxs"], schema_events[root_id]["temporal"], event_temps_h, arg_name_dict_h, (evt_map, ent_map, arg_filler), (rev_event_id_s, rev_entity_id_s), (event_graph_h, entity_graph_h), (global_graph, entity_graph), schema_dict, digits_list, (pidxs, pprovs, pargs), prov_dict)
            # schema_prim_child_idxs, schema_temporal, human_temporal, human_arg_dict, mapping_results, rev_dicts_s, human_graphs, schema_graphs, schema_dict, digits_list, predict_results, prov_dict
            instance["confidence"] = confidence
            instances.append(deepcopy(instance))

    task1_output = {
        "@context": [
            "https://kairos-sdf.s3.amazonaws.com/context/kairos-v1.4.1.jsonld",
            {
                "resin": "https://blender.cs.illinois.edu/kairos/"
            }
        ],
        "sdfVersion": "1.4.1",
        "@id": "resin:Submissions/TA2",
        "version": "resin / 1.0.0",
        "ceID": ceid,
        "ta2": True,
        "task2": False,
        "instances": instances,
        "provenanceData": prov_items
    }

    task1_output["@context"][-1].update({team: team_urls[team]})
    task1_string = json.dumps(task1_output)
    # HRF
    # visualize_task1(task1_output, human_dir, schema_dir, output_dir, event_dicts, event_mapping)
    # hrf_file_dir = os.path.join(hrf_dir, (team +"-resin-task1-"+ceid+".txt"))
    
    with open("./"+team+".json", 'w', encoding="utf-8") as f:
        f.write(json.dumps(task1_output, indent=4))

    # return task1_string, hrf
    return task1_string


def task2_predict(ceid, team, team_urls, schema_dir, graph_g, matching_threshold, prediction_threshold, cand_num, topn):
    digits_list = [str(i).zfill(5) for i in range(0, 100000)]

    (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), primitive_ids_h = read_human_graph(graph_g)
    schema_events, event_node_idxs, entity_graph, entity_node_idxs, primitive_idxs, global_graph = read_schema(schema_dir)

    with open(schema_dir, 'r', encoding="utf-8") as f:
        schema_dict = json.loads(f.read())

    matching_results, matching_num = matching_graphs(event_graph_h, event_temps_h, arg_name_dict_h, schema_events, matching_threshold, cand_num, team)
    matched = {k:v["matched_num"] for k,v in matching_num.items()}
    top_id_list = [i[0] for i in sorted(matched.items(), key=lambda item:item[1], reverse=True)]

    rev_event_id_s = {v:k for k,v in event_node_idxs.items()}
    rev_entity_id_s = {v:k for k,v in entity_node_idxs.items()}

    instances = []

    for i in range(topn):
        if i < len(top_id_list):
            root_id = top_id_list[i]
            confidence = matching_num[root_id]["matched_num"] / len(event_node_idx_h)

            evt_map = matching_results[root_id]["event_maps"]
            ent_map = matching_results[root_id]["entity_maps"]
            arg_filler = matching_results[root_id]["arg_fillers"]

            pred_dict, matched_ids = generate_pred_values(evt_map, event_node_idxs, primitive_idxs)

            pidxs, pprovs, pargs = new_prediction(schema_events[root_id]["prim_child_idxs"], event_node_idxs, schema_events[root_id]["arg_id_dict"], arg_id_dict_h, evt_map, ent_map, arg_filler, pred_dict, prediction_threshold)

            instance, digits_list = generate_task2_instance(schema_events[root_id]["prim_child_idxs"], schema_events[root_id]["temporal"], primitive_ids_h, event_temps_h, arg_name_dict_h, (evt_map, ent_map, arg_filler), (rev_event_id_s, rev_entity_id_s), (event_graph_h, entity_graph_h), (global_graph, entity_graph), schema_dict, digits_list, (pidxs, pprovs, pargs))
            # schema_prim_child_idxs, schema_temporal, human_temporal, human_arg_dict, mapping_results, rev_dicts_s, human_graphs, schema_graphs, schema_dict, digits_list, predict_results, prov_dict
            instance["confidence"] = confidence
            instances.append(deepcopy(instance))


    task1_output = {
        "@context": [
            "https://kairos-sdf.s3.amazonaws.com/context/kairos-v1.4.1.jsonld",
            {
                "resin": "https://blender.cs.illinois.edu/kairos/"
            }
        ],
        "sdfVersion": "1.4.1",
        "@id": "resin:Submissions/TA2",
        "version": "resin / 1.0.0",
        "ceID": ceid,
        "ta2": True,
        "task2": True,
        "instances": instances
    }

    task1_output["@context"][-1].update({team: team_urls[team]})
    task1_string = json.dumps(task1_output)
    
    with open("./"+team+".json", 'w', encoding="utf-8") as f:
        f.write(json.dumps(task1_output, indent=4))

    # return task1_string, hrf
    return task1_string


if __name__ == "__main__":

    # xlsx_dir = "./result_01172022.xls"
    # read_pred_file(xlsx_dir)

    from ie_graph import *
    from schema import *
    from matching_events import *
    from matching_graphs import *
    from prediction import *

    xpo_dir = "./xpo_v3.2_freeze_exp.json"
    em, rm = read_xpo(xpo_dir)

    with open("./task1_graphs_qz9/coref.json", 'r', encoding="utf-8") as f:
        coref = json.loads(f.read())
    
    with open("./task1_graphs_qz9/temporal.json", 'r', encoding="utf-8") as f:
        temporal = json.loads(f.read())

    entity_cs_string = coref["coref"]["entity.cs"]
    event_cs_string = coref["coref"]["event.cs"]

    with open("./file.xml", 'w', encoding="utf-8") as f:
        f.write(coref["data"]["en"][0])
    temp_en_string = temporal["temporal_relation"]["en"]["temporal_relation.cs"]
    temp_es_string = temporal["temporal_relation"]["es"]["temporal_relation.cs"]

    en_data = coref["data"]["en"]
    es_data = coref["data"]["es"]

    (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), primitive_ids_h = read_ie_cluster(entity_cs_string, event_cs_string, temp_en_string, temp_es_string, em, rm, en_data, es_data)

    orgs = ["cmu", "ibm", "isi", "sbu", "resin"]

    hrf = "./task1_outputs_qz9"
    team_urls = {
        "cmu": "https://www.cmu.edu/",
        "ibm": "https://ibm.com/CHRONOS/",
        "isi": "https://isi.edu/kairos/",
        "resin": "https://blender.cs.illinois.edu/kairos/",
        "sbu": "https://cs.sbu.edu/kairos/"
    }

    # ceid, team, team_urls, schema_dir, entity_cs_string, event_cs_string, temp_en_string, temp_es_string, em, rm, en_data, es_data, matching_threshold, prediction_threshold, cand_num, topn

    for org in orgs:
        print(org)
        schema_file_dir = "./schemas_qz9/" + org + "-schemalib.json"
        schema_events, event_node_idxs, entity_graph, entity_node_idxs, primitive_idxs, global_graph = read_schema(schema_file_dir)
        task1_predict("ce2004", org, team_urls, schema_file_dir, entity_cs_string, event_cs_string, temp_en_string, temp_es_string, em, rm, en_data, es_data, 0.8, 0.4, 3, 2)
    
    # with open("./task2_graphs_qz8/ce2002abridged_GraphG.json", 'r', encoding='utf-8') as f:
    #     ggraph = json.loads(f.read())

    # for org in orgs:
    #     schema_file_dir = "./schemas_qz9/" + org + "-schemalib.json"
    #     schema_events, event_node_idxs, entity_graph, entity_node_idxs, primitive_idxs, global_graph = read_schema(schema_file_dir)
    #     task2_predict("ce2002", org, team_urls, schema_file_dir, ggraph, 0.8, 0.4, 3, 2)
    
    
