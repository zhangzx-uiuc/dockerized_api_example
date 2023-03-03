import json
import random
# import pandas as pd

def baseline_prediction(schema_event_nx_graph, schema_arg_dict, event_maps, entity_maps, arg_fillers):
    ''' inputs '''
    # schema [event_graph, event_node_idx, entity_graph, entity_node_idx, arg_dict, arg_id_dict]
    # instance [event_graph, event_node_idx, entity_graph, entity_node_idx, arg_dict]
    # arg_dict: {event_idx: {entity_idx: role_type}} // role_type is a string number like '0', '1', '2'
    # event_maps: {schema_idx: inst_idx}
    # entity_maps: {schema_idx: [inst_idxs]}
    # arg_fillers: {schema_idx: {role_id: [entity_idxs]}}
    ''' outputs '''
    # list of predicted schema event idxs [idx1, idx2, ..., idxN]
    # dict of predicted justifications: {idxN: {"entities": [list of schema entity idxs], "events": [list of schema event idxs]}}

    # construct reversed inst_entity_idx to schema_entity_idx
    inst_entity_idx_to_schema = {}
    for schema_entity_idx in entity_maps:
        inst_entity_idxs = entity_maps[schema_entity_idx]
        for idx in inst_entity_idxs:
            inst_entity_idx_to_schema.update({idx: schema_entity_idx})


    pred_idxs, pred_provs = [], {}

    for schema_idx in event_maps:
        schema_neighbors = list(schema_event_nx_graph.neighbors(schema_idx)) + list(schema_event_nx_graph.predecessors(schema_idx))
        # print(schema_neighbors)
        # summarize which entities of the current instantiated node have been instantiated
        instance_roles = arg_fillers[schema_idx]
        matched_entity_list = []
        for role_id in instance_roles:
            inst_entities = instance_roles[role_id]
            for ent_idx in inst_entities:
                matched_entity_list.append(inst_entity_idx_to_schema[ent_idx])

        for node in schema_neighbors:
            # nodes that are not instantiated can be predicted.
            if node not in event_maps:
                # first to check if shared entity exists
                shared_entity_idxs = []
                neigh_ent_idxs = schema_arg_dict[node]
                
                for ent in neigh_ent_idxs:
                    if ent in matched_entity_list:
                        shared_entity_idxs.append(ent)
                
                if len(shared_entity_idxs) != 0:
                    # which means that we should predict this event
                    if node not in pred_idxs:
                        pred_idxs.append(node)
                    
                    if node not in pred_provs:
                        pred_provs.update({node: {"events": [schema_idx], "entities": shared_entity_idxs.copy()}})
                    else:
                        if schema_idx not in pred_provs[node]["events"]:
                            pred_provs[node]["events"].append(schema_idx)
                        for shared_id in shared_entity_idxs:
                            if shared_id not in pred_provs[node]["entities"]:
                                pred_provs[node]["entities"].append(shared_id)
    
    return pred_idxs, pred_provs     

def new_prediction(schema_prim_ids, schema_event_to_idx, schema_arg_id_dict, inst_arg_id_dict, event_maps, entity_maps, arg_fillers, pred_dict, pred_threshold):
    # pred_dict: {{pred_schema_event_id: pred_event_conf}} already specified by (team, doc)
    ''' inputs '''
    # schema [event_graph, event_node_idx, entity_graph, entity_node_idx, arg_dict, arg_id_dict]
    # instance [event_graph, event_node_idx, entity_graph, entity_node_idx, arg_dict]
    # arg_dict: {event_idx: {entity_idx: role_type}} // role_type is a string number like '0', '1', '2'
    # arg_id_dict: {event_idx: {entity_idx: role_id}} // role_type is a string number like '0', '1', '2'
    # event_maps: {schema_idx: (inst_idx, conf)}
    # entity_maps: {schema_idx: {inst_idx: num of occurrence}]}
    # arg_fillers: {schema_idx: {role_id: [entity_idxs]}}
    ''' outputs '''
    # list of predicted schema event idxs [idx1, idx2, ..., idxN]
    # dict of predicted justifications: {idxN: {"entities": [list of schema entity idxs], "events": [list of schema event idxs], "confidence": 0.347}}
    # dict of predicted entities: {idxN: {role_id: inst_entity_idx}}
    pred_idxs = []
    pred_provs = {}
    pred_args = {}

    for seid in pred_dict:
        seidx = schema_event_to_idx[seid]
        assert (seidx not in event_maps)
        if seidx not in schema_prim_ids:
            continue
        s_roles = schema_arg_id_dict[seidx] # s_roles: {entity_idx: role_id}
        
        # check whether the predicted schema event has any of its arguments instantiated.
        ent_prov_ids, event_prov_idxs = [], []
        pred_args_i = {}
        
        for entity_idx in s_roles:
            role_id = s_roles[entity_idx]
            if entity_idx in entity_maps:
                inst_times = entity_maps[entity_idx]
                max_insted_entity_idx = max(inst_times, key=inst_times.get)
                pred_args_i.update({role_id: max_insted_entity_idx})

                # find out all instantiated events in human graphs that share this entity idx
                for key,value in event_maps.items():
                    inst_event_idx = value[0]
                    inst_event_args = inst_arg_id_dict[inst_event_idx]

                    if max_insted_entity_idx in inst_event_args:
                        event_prov_idxs.append(key)
                        schema_role_dict = arg_fillers[key]
                        rev_dict_key = {k:v for v,k in schema_arg_id_dict[key].items()}
                        for rid in schema_role_dict:
                            inst_ent_idxs = schema_role_dict[rid]
                            if max_insted_entity_idx in inst_ent_idxs:
                                ent_prov_ids.append(rev_dict_key[rid])
                
        
        if len(event_prov_idxs) > 0 and pred_dict[seid] >= pred_threshold:
            pred_idxs.append(seidx)
            pred_provs.update({seidx: {"entities": ent_prov_ids, "events": event_prov_idxs, "confidence": pred_dict[seid]}})
            pred_args.update({seidx: pred_args_i})

    # list of predicted schema event idxs [idx1, idx2, ..., idxN]
    # dict of predicted justifications: {idxN: {"entities": [list of schema entity idxs], "events": [list of schema event idxs], "confidence": 0.347}}
    # dict of predicted entities: {idxN: {role_id: inst_entity_idx}}
    return pred_idxs, pred_provs, pred_args


# replace this with hongwei's algorithm
def generate_pred_values(event_maps, event_node_idx_s, prim_ids):
    matched_ids = []
    rev_event_node_idx_s = {v:k for k,v in event_node_idx_s.items()}
    for event_id in event_maps:
        matched_ids.append(rev_event_node_idx_s[event_id])

    pred_output = {}
    for event_id in event_node_idx_s:
        event_idx = event_node_idx_s[event_id]
        if event_id not in matched_ids and event_idx in prim_ids:
            pred_output[event_id] = random.random()
    return pred_output, matched_ids.copy()



if __name__ == "__main__":
    # xlsx_dir = "./result_01172022.xls"
    # read_pred_file(xlsx_dir)

    from ie_graph import *
    from schema import *
    from matching_events import *
    from matching_graphs import *

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

        matching_results, matching_num = matching_graphs(event_graph_h, event_temps_h, arg_name_dict_h, schema_events, 0.8, 2, org)

        for root_id in matching_results:
            evt_map = matching_results[root_id]["event_maps"]
            ent_map = matching_results[root_id]["entity_maps"]
            arg_filler = matching_results[root_id]["arg_fillers"]

            pred_dict, _ = generate_pred_values(evt_map, event_node_idxs, schema_events[root_id]["prim_child_idxs"])

            pidxs, pprovs, pargs = new_prediction(schema_events[root_id]["prim_child_idxs"], event_node_idxs, schema_events[root_id]["arg_id_dict"], arg_id_dict_h, evt_map, ent_map, arg_filler, pred_dict, 0.3)
            print(root_id)
            print(pidxs)
            # print(pprovs)
            # print(pargs)

