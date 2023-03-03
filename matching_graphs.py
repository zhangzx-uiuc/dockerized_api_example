from matching_events import match_events

from copy import deepcopy

import random
import re
import json


def get_arg_positions(role_name, is_sbu):
    # Need to be improved.
    if not is_sbu:
        input_splits = re.split('-|_', role_name)
        # print(input_splits)
        return input_splits[1].lower()
    else:
        return role_name[1]


def get_arg_pos_dict(arg_name_dict, is_sbu):
    arg_pos_dict = deepcopy(arg_name_dict)
    for key in arg_pos_dict:
        for idx in arg_pos_dict[key]:
            arg_pos_dict[key][idx] = get_arg_positions(arg_pos_dict[key][idx], is_sbu)
    return arg_pos_dict


def matching_graphs(inst_event_graph, inst_temp, arg_name_i, schema_events, threshold, num, team):

    # events: (event_graph, event_node_idx, temp, children), 
    # entities: (entity_graph, entity_node_idx), 
    # arguments: (arg_name_dict, arg_id_dict).
    # threshold: a scalar: tolerance for errors.

    results, results_num =  match_events(inst_event_graph, schema_events, inst_temp, threshold, num)

    graph_results = {}
    for root_id in results:
        res_list, res_conf = results[root_id]
        arg_name_s, arg_id_s = schema_events[root_id]["arg_dict"], schema_events[root_id]["arg_id_dict"]
        # print(root_id)
        if team == "sbu" or team == "ibm":
            arg_pos_i = get_arg_pos_dict(arg_name_i, True)
            arg_pos_s = get_arg_pos_dict(arg_name_s, True)
        else:
            arg_pos_i = get_arg_pos_dict(arg_name_i, False)
            arg_pos_s = get_arg_pos_dict(arg_name_s, False)

        event_maps = {} # from schema to inst {schema_idx: inst_idx}
        for i,idx in enumerate(res_list):
            if idx != -1:
                event_maps.update({idx: (i, res_conf[i])})

        inst_arg_dict = arg_pos_i
        schema_arg_dict = arg_pos_s
        schema_arg_id_dict = arg_id_s

        entity_maps = {} # from schema to inst {schema_idx: {inst_idx: inst_times}}
        arg_fillers = {} # {schema_event_idx: {role_id: [entity_idxs]}}

        for inst_idx, schema_idx in enumerate(res_list):
            
            if schema_idx != -1:
                inst_event_args = inst_arg_dict[inst_idx]
                schema_event_args = schema_arg_dict[schema_idx]
                schema_event_id_args = schema_arg_id_dict[schema_idx]
                arg_fillers.update({schema_idx: {}})
                
                schema_dict = {}
                for idx in schema_event_args:
                    if schema_event_args[idx] not in schema_dict:
                        schema_dict.update({schema_event_args[idx]: [idx]})
                    else:
                        schema_dict[schema_event_args[idx]].append(idx)

                instance_dict = {}
                for idx in inst_event_args:
                    if inst_event_args[idx] not in instance_dict:
                        instance_dict.update({inst_event_args[idx]: [idx]})
                    else:
                        instance_dict[inst_event_args[idx]].append(idx)

                for role in instance_dict:
                    if role in schema_dict:
                        schema_node_idxs = schema_dict[role]
                        schema_node = random.choice(schema_node_idxs)
                        schema_role_id = schema_event_id_args[schema_node]
                        
                        inst_nodes = instance_dict[role]
                        arg_fillers[schema_idx].update({schema_role_id: inst_nodes})
                        
                        if schema_node not in entity_maps:
                            entity_maps.update({schema_node: {}})
                            for node_idx in inst_nodes:
                                entity_maps[schema_node].update({node_idx: 1})
                        else:
                            for k in inst_nodes:
                                if k not in entity_maps[schema_node]:
                                    entity_maps[schema_node].update({k: 1})
                                else:
                                    entity_maps[schema_node][k] += 1

        graph_results[root_id] = {
            "event_maps": deepcopy(event_maps),
            "entity_maps": deepcopy(entity_maps),
            "arg_fillers": deepcopy(arg_fillers)
        }
    
    # print(json.dumps(results_num, indent=4))
    return graph_results, results_num


if __name__ == "__main__":
    # from human_graph import read_human_graph
    # from schema import read_schema

    # human_graph_dir = "./Quizlet8_GraphG/ce2002abridged_GraphG.json"
    # # human_graph_dir = "./Quizlet8_GraphG/ce2002full_GraphG.json"
    # schema_graph_dir = "./Quizlet8-TA1/Schemas/ibm-schemalib.json"
    # # schema_graph_dir = "./Quizlet8-TA1/Schemas/Justice_Consume_Contamination.json"

    # (event_graph_s, event_node_idx_s, event_temps_s, event_child_idxs_s), (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s), prim_ids_s = read_schema(schema_graph_dir)
    # (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), prim_ids_h = read_human_graph(human_graph_dir)

    # matching_graphs((event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), prim_ids_h, (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h),  \
    #                 (event_graph_s, event_node_idx_s, event_temps_s, event_child_idxs_s), prim_ids_s, (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s),  \
    #                 0.8, 1, "ibm")

    from ie_graph import *
    from schema import *
    from matching_events import *

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

    (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), primitive_ids_h = read_ie_cluster(entity_cs_string, event_cs_string, temp_en_string, temp_es_string, em, rm, en_data, es_data)

    orgs = ["cmu", "ibm", "isi", "sbu", "resin"]

    for org in orgs:
        schema_file_dir = "./schemas_qz9/" + org + "-schemalib.json"
        schema_events, event_node_idxs, entity_graph, entity_node_idxs, primitive_idxs, global_graph = read_schema(schema_file_dir)

        matching_graphs(event_graph_h, event_temps_h, arg_name_dict_h, schema_events, 0.75, 2, org)


    