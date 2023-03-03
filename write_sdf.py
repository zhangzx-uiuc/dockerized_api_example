import copy
from copy import deepcopy

from event_temporal import expand_ids_temporal
from collections import defaultdict

def remove_conflict_temporal_relations(temp_dict):
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

    new_temp_dict = {evt: [] for evt in temp_dict}
    for start, ends in temp_dict.items():
        for end in ends:
            vis = set()
            if start == end:
                continue
            if (not can_reach(end, start)) and not (end in edges[start]):
                edges[start].append(end)
                new_temp_dict[start].append(end)
    return new_temp_dict


def update_digits_list(digits_list, schema_dict):
    for event in schema_dict["events"]:
        digit = event["@id"].split('/')[1]
        if digit in digits_list:
            digits_list.remove(digit)

        if "participants" in event:
            for arg in event["participants"]:
                digit = arg["@id"].split('/')[1]
                if digit in digits_list:
                    digits_list.remove(digit)
    
    for entity in schema_dict["entities"]:
        digit = entity["@id"].split('/')[1]
        if digit in digits_list:
            digits_list.remove(digit)
    
    for relation in schema_dict["relations"]:
        digit = relation["@id"].split('/')[1]
        if digit in digits_list:
            digits_list.remove(digit)

    return digits_list

def modify_qnode(qnode_str):
    qnode = qnode_str.split(':')[-1]
    if qnode.startswith('P'):
        return "wdt:"+qnode
    if qnode.startswith('Q'):
        return "wd:"+qnode

def modify_qnodes(qnodes):
    if type(qnodes) == list:
        new_nodes = []
        for q in qnodes:
            new_nodes.append(modify_qnode(q))
        return new_nodes
    else:
        return modify_qnode(qnodes)

def generate_id_mappings(digits_list, schema_inst, prim_schema_idxs, human_inst=None):
    # generate schema event id mappings.
    # only events, entities, roles, and relations have @ids.
    id_mappings = {}
    # schema events and roles
    for j,event in enumerate(schema_inst["events"]):
        if j in prim_schema_idxs:
            event_id = event["@id"]
            splits = event_id.split('/')
            digit = digits_list.pop(0)
            splits[1] = digit
            splits[0] = "resin:" + splits[0].split(':')[-1]
            new_id = "/".join(splits)
            id_mappings.update({event_id: new_id})

            if "participants" in event:
                args = event["participants"]
                for arg in args:
                    # ibm:Participants/83987/pathogen
                    arg_id = arg["@id"]
                    splits = arg_id.split('/')
                    digit = digits_list.pop(0)
                    splits[1] = digit
                    splits[0] = "resin:" + splits[0].split(':')[-1]
                    new_id = "/".join(splits)
                    id_mappings.update({arg_id: new_id})
    
    # schema entities and relations
    for entity in schema_inst["entities"]:
        entity_id = entity["@id"]
        splits = entity_id.split('/')
        digit = digits_list.pop(0)
        splits[1] = digit
        splits[0] = "resin:" + splits[0].split(':')[-1]
        new_id = "/".join(splits)
        id_mappings.update({entity_id: new_id})
    
    for rel in schema_inst["relations"]:
        rel_id = rel["@id"]
        splits = rel_id.split('/')
        digit = digits_list.pop(0)
        splits[1] = digit
        splits[0] = "resin:" + splits[0].split(':')[-1]
        new_id = "/".join(splits)
        id_mappings.update({rel_id: new_id})
    
    if human_inst is not None:
        # instance events and roles
        for event in human_inst["events"]:
            event_id = event["@id"]
            splits = event_id.split('/')
            digit = digits_list.pop(0)
            splits[1] = digit
            splits[0] = "resin:" + splits[0].split(':')[-1]
            new_id = "/".join(splits)
            id_mappings.update({event_id: new_id})

            if "participants" in event:
                args = event["participants"]
            for arg in args:
                # ibm:Participants/83987/pathogen
                arg_id = arg["@id"]
                splits = arg_id.split('/')
                digit = digits_list.pop(0)
                splits[1] = digit
                splits[0] = "resin:" + splits[0].split(':')[-1]
                new_id = "/".join(splits)
                id_mappings.update({arg_id: new_id})
    
        # schema entities and relations
        for entity in human_inst["entities"]:
            entity_id = entity["@id"]
            splits = entity_id.split('/')
            digit = digits_list.pop(0)
            splits[1] = digit
            splits[0] = "resin:" + splits[0].split(':')[-1]
            new_id = "/".join(splits)
            id_mappings.update({entity_id: new_id})
        
        for rel in human_inst["relations"]:
            rel_id = rel["@id"]
            splits = rel_id.split('/')
            digit = digits_list.pop(0)
            splits[1] = digit
            splits[0] = "resin:" + splits[0].split(':')[-1]
            new_id = "/".join(splits)
            id_mappings.update({rel_id: new_id})
    
    return id_mappings, digits_list        


def generate_task1_instance(schema_prim_child_idxs, schema_temporal, human_temporal, human_arg_dict, mapping_results, rev_dicts_s, human_graphs, schema_graphs, schema_dict, digits_list, predict_results, prov_dict):
    # mapping_results: [event_maps, entity_maps, arg_fillers]
    # predict_results: [pred_idxs, pred_provs, pred_args]
    # rev_dicts: [rev_event_node_idx, rev_entity_node_idx]
    # human_graphs: [human_event_graph, human_entity_graph]
    # schema_graphs: [schema_event_graph, schema_entity_graph]
    # output: one "instance"
    # prov_dict: {(doc, start, end): prov_id}
    # human_arg_dict: {event_idx: {ta2_entity_idx: role_name}

    # schema_dict: schema instance
    # human_dict: human instance

    # arg_fillers: {schema_event_id: {role_id: [entity_idxs]}}
    # arg_dict: {event_idx: {entity_idx: role_type}} // role_type is a string number like '0', '1', '2'
    # arg_id_dict: {event_idx: {entity_idx: role_arg_id}} // role_arg_id is the @id field for an event participant

    # list of predicted schema event idxs [idx1, idx2, ..., idxN]
    # dict of predicted justifications: {idxN: {"entities": [list of schema entity idxs], "events": [list of schema event idxs]}}
    rev_schema_event_idx, rev_schema_entity_idx = rev_dicts_s[0], rev_dicts_s[1]

    event_maps, entity_maps, arg_fillers = mapping_results

    schema_event_nodes = schema_graphs[0].nodes(data=True)
    inst_event_nodes = human_graphs[0].nodes(data=True)

    schema_entity_nodes = schema_graphs[1].nodes(data=True)
    inst_entity_nodes = human_graphs[1].nodes(data=True)

    pred_idxs, pred_provs, pred_args = predict_results

    # Step 1: We generate id mappings: 
    id_mappings, digits_list = generate_id_mappings(digits_list, schema_dict, schema_prim_child_idxs)

    # Step 2: We summarize all the schema events:
    ta2_events = []
    # print(event_maps)
    schema_events = deepcopy(schema_dict["events"])
    schema_entities = deepcopy(schema_dict["entities"])
    schema_relations = deepcopy(schema_dict["relations"])

    added_inst_event_idxs = []

    # we need to first generate all ta2 entities
    entity_idx_to_id = {}
    ta2_entities = []
    for i,entity in enumerate(schema_entities):
        ta2_entity = deepcopy(entity)
        ta2_entity["@id"] = id_mappings[ta2_entity["@id"]]
        ta2_entities.append(ta2_entity)
    
    # all ta2 extracted entities are added here.
    for i,entity in inst_entity_nodes:
        digit = digits_list.pop(0)
        new_entity_id = "resin:Entities/" + digit + "/" + "_".join(entity["qlabels"][0].split())
        entity_idx_to_id.update({i: new_entity_id})
        ta2_entity = {
            "@id": new_entity_id,
            "name": entity["text"],
            "ta2qnode": entity["qnodes"][0],
            "ta2qlabel": entity["qlabels"][0]
        }
        ta2_entities.append(deepcopy(ta2_entity))
    

    origin_idx_to_id = {}
    human_idx_to_id = {}
    # event_num = 0
    # first we add all schema events (instantiated and uninstantiated)
    insted_event_idxs = []
    for i,event in enumerate(schema_events):
        if i in schema_prim_child_idxs: # we only add the events in the sub-schema
            ta2_event = deepcopy(event)
            ta2_event["ta1ref"] = ta2_event["@id"]
            ta2_event_id = id_mappings[ta2_event["@id"]]
            ta2_event["@id"] = ta2_event_id
            origin_idx_to_id[i] = ta2_event_id

            private_data = {"sentence": "", "trigger": ""}

            # OPTIONAL: change childrens and outlinks (in place)
            assert ("children" not in ta2_event)
            if "children" in ta2_event:
                children = ta2_event["children"]
                for child in children:
                    if "outlinks" in child:
                        outlinks = child["outlinks"]
                        for j in range(len(outlinks)):
                            outlinks[j] = id_mappings[outlinks[j]]
                    child["child"] = id_mappings[child["child"]]

            # instantiated events
            if i in event_maps:
                inst_i, inst_conf = event_maps[i]
                insted_event_idxs.append(inst_i)
                added_inst_event_idxs.append(inst_i)

                # prov_id = prov_dict[human_events[inst_i]["provenance"]
                provs = [prov_dict[prov] for prov in inst_event_nodes[inst_i]["provenance"]]

                ta2_event["provenance"] = provs[0] if len(provs) == 1 else provs
                ta2_event["confidence"] = round(inst_conf, 4) if len(provs) == 1 else [round(inst_conf, 4) for _ in range(len(provs))]
                # add ta2 qnodes and qlabels
                ta2_event["ta2qnode"] = inst_event_nodes[inst_i]["qnodes"][0]
                ta2_event["ta2qlabel"] = inst_event_nodes[inst_i]["qlabels"][0]
                # add participants
                # {schema_event_idx: {role_id: [entity_idxs]}}
                human_idx_to_id[inst_i] = ta2_event_id

                private_data["sentence"] = inst_event_nodes[inst_i]["description"]
                private_data["trigger"] = inst_event_nodes[inst_i]["trigger"]

                # add in participants
                if "participants" in ta2_event:
                    args = ta2_event["participants"]

                    arg_filler_i = arg_fillers[i]
                    for arg in args:
                        if arg["@id"] in arg_filler_i:
                            inst_entity_idxs = arg_filler_i[arg["@id"]]
                            if len(inst_entity_idxs) == 1:
                                inst_entity_idx = inst_entity_idxs[0]
                                provenances = [prov_dict[prov] for prov in inst_entity_nodes[inst_entity_idx]["provenance"]]
                                prov_list = provenances[0] if len(provenances) == 1 else provenances
                                values = {
                                    "ta2entity": entity_idx_to_id[inst_entity_idx],
                                    "provenance": prov_list,
                                    "confidence": round(inst_conf, 4) if len(provenances) == 1 else [round(inst_conf, 4) for _ in range(len(provenances))]
                                }
                            else:
                                values = []
                                for idx in inst_entity_idxs:
                                    provenances = [prov_dict[prov] for prov in inst_entity_nodes[idx]["provenance"]]
                                    prov_list = provenances[0] if len(provenances) == 1 else provenances
                                    value = {
                                        "ta2entity": entity_idx_to_id[idx],
                                        "provenance": prov_list,
                                        "confidence": round(inst_conf, 4) if len(provenances) == 1 else [round(inst_conf, 4) for _ in range(len(provenances))]
                                    }
                                    values.append(deepcopy(value))
                            
                            arg["values"] = values
            
            else:
                ta2_event["predictionProvenance"] = [ta2_event_id]
                ta2_event["confidence"] = 0.01

                private_data["sentence"] = ta2_event["ta1explanation"]

                if i in pred_idxs:
                    # pred_idxs, pred_provs, pred_args
                    # list of predicted schema event idxs [idx1, idx2, ..., idxN]
                    # dict of predicted justifications: {idxN: {"entities": [list of schema entity idxs], "events": [list of schema event idxs], "confidence": 0.347}}
                    # dict of predicted entities: {idxN: {role_id: inst_entity_idx}}
                    pred_provs_i = pred_provs[i]
                    pred_prov_ids = []
                    for event_idx in pred_provs_i["events"]:
                        pred_prov_ids.append(id_mappings[rev_schema_event_idx[event_idx]])
                    for entity_idx in pred_provs_i["entities"]:
                        pred_prov_ids.append(id_mappings[rev_schema_entity_idx[entity_idx]])
                    pred_conf = pred_provs_i["confidence"]
                    # prediction = {
                    #     "predictionProvenance": pred_prov_ids,
                    #     "confidence": round(pred_conf, 4)
                    # }                  
                    # ta2_event["prediction"] = prediction
                    ta2_event["predictionProvenance"] = pred_prov_ids
                    ta2_event["confidence"] = round(pred_conf, 4)

                    # then we change predicted arguments
                    if "participants" in ta2_event:
                        pred_args_i = pred_args[i]
                        for arg in ta2_event["participants"]:
                            if arg["@id"] in pred_args_i:
                                pred_inst_idx = pred_args_i[arg["@id"]]
                                provenances = [prov_dict[prov] for prov in inst_entity_nodes[pred_inst_idx]["provenance"]]
                                prov_list = provenances[0] if len(provenances) == 1 else provenances
                                values = {
                                    "ta2entity": entity_idx_to_id[pred_inst_idx],
                                    "provenance": prov_list,
                                    "confidence": round(pred_conf, 4) if len(provenances) == 1 else [round(pred_conf, 4) for _ in range(len(provenances))]
                                }

                                arg["values"] = values
                # else:
                #     continue
            # OPTIONAL: change event participants (in place)
            if "relations" in ta2_event:
                ta2_event.pop("relations")
            if "participants" in ta2_event:
                args = ta2_event["participants"]
                for arg in args:
                    arg["@id"] = id_mappings[arg["@id"]]
                    arg["entity"] = id_mappings[arg["entity"]]
            
            
            ta2_event["privateData"] = private_data
            ta2_events.append(deepcopy(ta2_event))
    
    # then we add back in all the ta2 events with kairos:NULL
    for k, inst_event in inst_event_nodes:
        if k not in insted_event_idxs:
            new_ta2_event = {}
            # @id
            digit = digits_list.pop(0)

            new_id = "resin:Events/" + digit + '/' + inst_event["trigger"]
            new_ta2_event["@id"] = new_id
            # ta1ref, name, description, ta1explanation, qnode, qlabel
            new_ta2_event['ta1ref'] = "kairos:NULL"
            new_ta2_event['name'] = inst_event["qlabels"][0]
            new_ta2_event['description'] = inst_event["description"]
            new_ta2_event['ta1explanation'] = "An uninstantiated TA2 event."
            new_ta2_event['ta2qnode'] = inst_event['qnodes'][0] if len(inst_event['qnodes']) == 1 else inst_event['qnodes']
            new_ta2_event['ta2qlabel'] = inst_event['qlabels'][0] if len(inst_event['qlabels']) == 1 else inst_event['qlabels']
            # provenance, confidence
            provenances = [prov_dict[prov] for prov in inst_event["provenance"]]
            new_ta2_event['provenance'] = provenances[0] if len(provenances) == 1 else provenances
            new_ta2_event['confidence'] = 1.0 if len(provenances) == 1 else [1.0 for _ in range(len(provenances))]

            private_data = {"sentence": inst_event["description"], "trigger": inst_event["trigger"]}
            # participants
            ppts = []
            event_args = human_arg_dict[k]
            for entity_idx, role_name in event_args.items():
                digit = digits_list.pop(0)
                role_id = "resin:Participants/" + digit + '/'
                entity_idd = entity_idx_to_id[entity_idx]
                ent_provenances = [prov_dict[prov] for prov in inst_entity_nodes[entity_idx]["provenance"]]

                ent_prov = ent_provenances[0] if len(ent_provenances) == 1 else ent_provenances
                ent_confs = 1.0 if len(ent_provenances) == 1 else [1.0 for _ in range(len(ent_provenances))]

                new_ppt = {
                    "@id": role_id,
                    "roleName": role_name,
                    "entity": entity_idd,
                    "values": {
                        "ta2entity": entity_idd,
                        "provenance": ent_prov,
                        "confidence": ent_confs
                    }
                }
                ppts.append(deepcopy(new_ppt))
            
            human_idx_to_id[k] = new_id

            new_ta2_event["participants"] = deepcopy(ppts)
            new_ta2_event["privateData"] = private_data

            ta2_events.append(deepcopy(new_ta2_event))
        
    # then we add relations, we should consider all possible relations with expanded temporal dict 
    # we first add back the original non-temporal relations (none of them are instantiated)
    prov_0 = list(prov_dict.values())[0]
    ta2_relations = []
    for i,rel in enumerate(schema_relations):
        ta2_rel = deepcopy(rel)
        if ta2_rel["relationPredicate"].split(':')[-1] != "Q79030196":
            ta2_rel["@id"] = id_mappings[ta2_rel["@id"]]
            ta2_rel["relationSubject"] = id_mappings[ta2_rel["relationSubject"]]
            ta2_rel["relationObject"] = id_mappings[ta2_rel["relationObject"]]
            ta2_rel["ta1ref"] = ta2_rel["@id"]
            ta2_relations.append(deepcopy(ta2_rel))
    
    # We need to summarize all relations here for all events in TA2
    relation_dict = {} # {new_relation_id: [list of new_relation ids]}
    # add in all of the original_schema_idx
    for j,event in enumerate(ta2_events):
        if event["@id"] not in relation_dict:
            relation_dict[event["@id"]] = []
    
    # first run this part: trust schema temporal relations
    for start_idx, end_idxs in schema_temporal.items():
        start_id = origin_idx_to_id[start_idx]
        for end_idx in end_idxs:
            end_id = origin_idx_to_id[end_idx]
            if start_id not in relation_dict[end_id] and end_id not in relation_dict[start_id]:
                relation_dict[start_id].append(end_id)
    
    # first run this part: trust instance temporal relations
    for start_idx, end_idxs in human_temporal.items():
        start_id = human_idx_to_id[start_idx]
        for end_idx in end_idxs:
            end_id = human_idx_to_id[end_idx]
            if start_id not in relation_dict[end_id] and end_id not in relation_dict[start_id]:
                relation_dict[start_id].append(end_id)
    
    new_relation_dict = remove_conflict_temporal_relations(relation_dict)
    # finally do an expansion on all included ta2 events 
    expanded_relation_id_dict = expand_ids_temporal(new_relation_dict)
    for key, value in expanded_relation_id_dict.items():
        if key in value:
            print(key)

    # write out relations
    for start_id, end_ids in expanded_relation_id_dict.items():
        for end_id in end_ids:
            digit = digits_list.pop(0)
            new_rel = {
                "@id": "resin:Relations/" + digit + "/",
                "name": "before",
                "relationSubject": start_id,
                "relationPredicate": "wd:Q79030196",
                "relationObject": end_id,
                "relationSubject_prov": prov_0,
                "relationProvenance": prov_0,
                "relationObject_prov": prov_0,
                "confidence": 1.0
            }
            ta2_relations.append(new_rel.copy())

    
    digit = digits_list.pop(0)
    ''' modify schema instantiations here '''
    instance = {
        "@id": "resin:Instances/" + digit + '/',
        "ta1ref": schema_dict["@id"],
        "name": "Disease outbreak",
        "description": "Instantiation and prediction results for " + schema_dict["@id"],
        "confidence": 1.0000,
        # "schemaInstantiations": [id_mappings[root_id]], 
        "events": ta2_events,
        "entities": ta2_entities,
        "relations": ta2_relations
    }

    return instance, digits_list


def generate_task2_instance(schema_prim_child_idxs, schema_temporal, human_prim_idxs, human_temporal, human_arg_dict, mapping_results, rev_dicts_s, human_graphs, schema_graphs, schema_dict, digits_list, predict_results):
    # mapping_results: [event_maps, entity_maps, arg_fillers]
    # predict_results: [pred_idxs, pred_provs, pred_args]
    # rev_dicts: [rev_event_node_idx, rev_entity_node_idx]
    # human_graphs: [human_event_graph, human_entity_graph]
    # schema_graphs: [schema_event_graph, schema_entity_graph]
    # output: one "instance"
    # prov_dict: {(doc, start, end): prov_id}
    # human_arg_dict: {event_idx: {ta2_entity_idx: role_name}

    # schema_dict: schema instance
    # human_dict: human instance

    # arg_fillers: {schema_event_id: {role_id: [entity_idxs]}}
    # arg_dict: {event_idx: {entity_idx: role_type}} // role_type is a string number like '0', '1', '2'
    # arg_id_dict: {event_idx: {entity_idx: role_arg_id}} // role_arg_id is the @id field for an event participant

    # list of predicted schema event idxs [idx1, idx2, ..., idxN]
    # dict of predicted justifications: {idxN: {"entities": [list of schema entity idxs], "events": [list of schema event idxs]}}
    rev_schema_event_idx, rev_schema_entity_idx = rev_dicts_s[0], rev_dicts_s[1]

    event_maps, entity_maps, arg_fillers = mapping_results

    schema_event_nodes = schema_graphs[0].nodes(data=True)
    inst_event_nodes = human_graphs[0].nodes(data=True)

    schema_entity_nodes = schema_graphs[1].nodes(data=True)
    inst_entity_nodes = human_graphs[1].nodes(data=True)

    pred_idxs, pred_provs, pred_args = predict_results

    # Step 1: We generate id mappings: 
    id_mappings, digits_list = generate_id_mappings(digits_list, schema_dict, schema_prim_child_idxs)

    # Step 2: We summarize all the schema events:
    ta2_events = []
    schema_events = deepcopy(schema_dict["events"])
    schema_entities = deepcopy(schema_dict["entities"])
    schema_relations = deepcopy(schema_dict["relations"])

    added_inst_event_idxs = []

    # we need to first generate all ta2 entities
    entity_idx_to_id = {}
    ta2_entities = []
    for i,entity in enumerate(schema_entities):
        ta2_entity = deepcopy(entity)
        ta2_entity["@id"] = id_mappings[ta2_entity["@id"]]
        ta2_entities.append(ta2_entity)
    
    # all ta2 extracted entities are added here.
    for i,entity in inst_entity_nodes:
        digit = digits_list.pop(0)
        new_entity_id = "resin:Entities/" + digit + "/" + "_".join(entity["qlabels"][0].split())
        entity_idx_to_id.update({i: new_entity_id})
        ta2_entity = {
            "@id": new_entity_id,
            "name": entity["text"],
            "ta2qnode": entity["qnodes"][0],
            "ta2qlabel": entity["qlabels"][0]
        }
        ta2_entities.append(deepcopy(ta2_entity))
    

    origin_idx_to_id = {}
    human_idx_to_id = {}
    # event_num = 0
    # first we add all schema events (instantiated and uninstantiated)
    insted_event_idxs = []
    for i,event in enumerate(schema_events):
        if i in schema_prim_child_idxs: # we only add the events in the sub-schema
            ta2_event = deepcopy(event)
            ta2_event["ta1ref"] = ta2_event["@id"]
            ta2_event_id = id_mappings[ta2_event["@id"]]
            ta2_event["@id"] = ta2_event_id
            origin_idx_to_id[i] = ta2_event_id

            private_data = {"sentence": "", "trigger": ""}

            # OPTIONAL: change childrens and outlinks (in place)
            assert ("children" not in ta2_event)
            if "children" in ta2_event:
                children = ta2_event["children"]
                for child in children:
                    if "outlinks" in child:
                        outlinks = child["outlinks"]
                        for j in range(len(outlinks)):
                            outlinks[j] = id_mappings[outlinks[j]]
                    child["child"] = id_mappings[child["child"]]

            # instantiated events
            if i in event_maps:
                inst_i, inst_conf = event_maps[i]
                insted_event_idxs.append(inst_i)
                added_inst_event_idxs.append(inst_i)

                # prov_id = prov_dict[human_events[inst_i]["provenance"]

                ta2_event["provenance"] = inst_event_nodes[inst_i]["provenance"]
                ta2_event["confidence"] = round(inst_conf, 4) 
                # add ta2 qnodes and qlabels
                ta2_event["ta2qnode"] = inst_event_nodes[inst_i]["qnodes"][0]
                ta2_event["ta2qlabel"] = inst_event_nodes[inst_i]["qlabels"][0]
                # add participants
                human_idx_to_id[inst_i] = ta2_event_id

                private_data["sentence"] = inst_event_nodes[inst_i]["description"]
                # add in participants
                if "participants" in ta2_event:
                    args = ta2_event["participants"]

                    arg_filler_i = arg_fillers[i]
                    for arg in args:
                        if arg["@id"] in arg_filler_i:
                            inst_entity_idxs = arg_filler_i[arg["@id"]]
                            if len(inst_entity_idxs) == 1:
                                inst_entity_idx = inst_entity_idxs[0]
                                values = {
                                    "ta2entity": entity_idx_to_id[inst_entity_idx],
                                    "provenance": inst_entity_nodes[inst_entity_idx]["provenance"],
                                    "confidence": round(inst_conf, 4)
                                }
                            else:
                                values = []
                                for idx in inst_entity_idxs:
                                    value = {
                                        "ta2entity": entity_idx_to_id[idx],
                                        "provenance": inst_entity_nodes[idx]["provenance"],
                                        "confidence": round(inst_conf, 4)
                                    }
                                    values.append(deepcopy(value))
                            
                            arg["values"] = values
            
            else:
                ta2_event["predictionProvenance"] = [ta2_event_id]
                ta2_event["confidence"] = 0.01

                private_data["sentence"] = ta2_event["ta1explanation"]

                if i in pred_idxs:
                    # pred_idxs, pred_provs, pred_args
                    # list of predicted schema event idxs [idx1, idx2, ..., idxN]
                    # dict of predicted justifications: {idxN: {"entities": [list of schema entity idxs], "events": [list of schema event idxs], "confidence": 0.347}}
                    # dict of predicted entities: {idxN: {role_id: inst_entity_idx}}
                    pred_provs_i = pred_provs[i]
                    pred_prov_ids = []
                    for event_idx in pred_provs_i["events"]:
                        pred_prov_ids.append(id_mappings[rev_schema_event_idx[event_idx]])
                    for entity_idx in pred_provs_i["entities"]:
                        pred_prov_ids.append(id_mappings[rev_schema_entity_idx[entity_idx]])
                    pred_conf = pred_provs_i["confidence"]
                    # prediction = {
                    #     "predictionProvenance": pred_prov_ids,
                    #     "confidence": round(pred_conf, 4)
                    # }                  
                    # ta2_event["prediction"] = prediction
                    ta2_event["predictionProvenance"] = pred_prov_ids
                    ta2_event["confidence"] = round(pred_conf, 4)

                    # then we change predicted arguments
                    if "participants" in ta2_event:
                        pred_args_i = pred_args[i]
                        for arg in ta2_event["participants"]:
                            if arg["@id"] in pred_args_i:
                                pred_inst_idx = pred_args_i[arg["@id"]]
                                values = {
                                    "ta2entity": entity_idx_to_id[pred_inst_idx],
                                    "provenance": inst_entity_nodes[pred_inst_idx]["provenance"],
                                    "confidence": round(pred_conf, 4)
                                }

                                arg["values"] = values
                # else:
                #     continue
            # OPTIONAL: change event participants (in place)
            if "relations" in ta2_event:
                ta2_event.pop("relations")
            if "participants" in ta2_event:
                args = ta2_event["participants"]
                for arg in args:
                    arg["@id"] = id_mappings[arg["@id"]]
                    arg["entity"] = id_mappings[arg["entity"]]
            
            
            ta2_event["privateData"] = private_data
            ta2_events.append(deepcopy(ta2_event))
    
    # then we add back in all the ta2 events with kairos:NULL
    for k, inst_event in inst_event_nodes:
        if k not in insted_event_idxs and k in human_prim_idxs:
            new_ta2_event = {}
            # @id
            digit = digits_list.pop(0)

            new_id = "resin:Events/" + digit + '/'
            new_ta2_event["@id"] = new_id
            # ta1ref, name, description, ta1explanation, qnode, qlabel
            new_ta2_event['ta1ref'] = "kairos:NULL"
            new_ta2_event['name'] = inst_event["qlabels"][0]
            new_ta2_event['description'] = inst_event["description"]
            new_ta2_event['ta1explanation'] = "An uninstantiated TA2 event."
            new_ta2_event['ta2qnode'] = inst_event['qnodes'][0] if len(inst_event['qnodes']) == 1 else inst_event['qnodes']
            new_ta2_event['ta2qlabel'] = inst_event['qlabels'][0] if len(inst_event['qlabels']) == 1 else inst_event['qlabels']
            # provenance, confidence
            new_ta2_event['provenance'] = inst_event["provenance"]
            new_ta2_event['confidence'] = 1.0

            private_data = {"sentence": inst_event["description"], "trigger": ""}
            # participants
            ppts = []
            event_args = human_arg_dict[k]
            for entity_idx, role_name in event_args.items():
                digit = digits_list.pop(0)
                role_id = "resin:Participants/" + digit + '/'
                entity_idd = entity_idx_to_id[entity_idx]

                new_ppt = {
                    "@id": role_id,
                    "roleName": role_name,
                    "entity": entity_idd,
                    "values": {
                        "ta2entity": entity_idd,
                        "provenance": inst_entity_nodes[entity_idx]["provenance"],
                        "confidence": 1.0
                    }
                }
                ppts.append(deepcopy(new_ppt))
            
            human_idx_to_id[k] = new_id

            new_ta2_event["participants"] = deepcopy(ppts)
            new_ta2_event["privateData"] = private_data

            ta2_events.append(deepcopy(new_ta2_event))
        
    # then we add relations, we should consider all possible relations with expanded temporal dict 
    # we first add back the original non-temporal relations (none of them are instantiated)

    ta2_relations = []
    for i,rel in enumerate(schema_relations):
        ta2_rel = deepcopy(rel)
        if ta2_rel["relationPredicate"].split(':')[-1] != "Q79030196":
            ta2_rel["@id"] = id_mappings[ta2_rel["@id"]]
            ta2_rel["relationSubject"] = id_mappings[ta2_rel["relationSubject"]]
            ta2_rel["relationObject"] = id_mappings[ta2_rel["relationObject"]]
            ta2_rel["ta1ref"] = ta2_rel["@id"]
            ta2_relations.append(deepcopy(ta2_rel))
    
    # We need to summarize all relations here for all events in TA2
    relation_dict = {} # {new_relation_id: [list of new_relation ids]}
    # add in all of the original_schema_idx
    for j,event in enumerate(ta2_events):
        if event["@id"] not in relation_dict:
            relation_dict[event["@id"]] = []
    
    # first run this part: trust instance temporal relations
    for start_idx, end_idxs in human_temporal.items():
        start_id = human_idx_to_id[start_idx]
        for end_idx in end_idxs:
            end_id = human_idx_to_id[end_idx]
            if start_id not in relation_dict[end_id] and end_id not in relation_dict[start_id]:
                relation_dict[start_id].append(end_id)
    
    # first run this part: trust schema temporal relations
    for start_idx, end_idxs in schema_temporal.items():
        start_id = origin_idx_to_id[start_idx]
        for end_idx in end_idxs:
            end_id = origin_idx_to_id[end_idx]
            if start_id not in relation_dict[end_id] and end_id not in relation_dict[start_id]:
                relation_dict[start_id].append(end_id)
    
    new_relation_dict = remove_conflict_temporal_relations(relation_dict)
    # finally do an expansion on all included ta2 events 
    expanded_relation_id_dict = expand_ids_temporal(new_relation_dict)
    for key, value in expanded_relation_id_dict.items():
        if key in value:
            print(key)

    # finally do an expansion on all included ta2 events 
    expanded_relation_id_dict = expand_ids_temporal(relation_dict)

    # write out relations
    for start_id, end_ids in expanded_relation_id_dict.items():
        for end_id in end_ids:
            digit = digits_list.pop(0)
            new_rel = {
                "@id": "resin:Relations/" + digit + "/",
                "name": "before",
                "relationSubject": start_id,
                "relationPredicate": "wd:Q79030196",
                "relationObject": end_id,
                "ta1ref": "kairos:NULL",
                "relationSubject_prov": "n/a",
                "relationProvenance": "n/a",
                "relationObject_prov": "n/a"
            }
            ta2_relations.append(new_rel.copy())
    
    digit = digits_list.pop(0)
    ''' modify schema instantiations here '''
    instance = {
        "@id": "resin:Instances/" + digit + '/',
        "ta1ref": schema_dict["@id"],
        "name": "Disease outbreak",
        "description": "Instantiation and prediction results for " + schema_dict["@id"],
        "confidence": 1.0000,
        # "schemaInstantiations": [id_mappings[root_id]], 
        "events": ta2_events,
        "entities": ta2_entities,
        "relations": ta2_relations
    }

    return instance, digits_list



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

    orgs = ["sbu"]

    for org in orgs:
        schema_file_dir = "./schemas_qz9/" + org + "-schemalib.json"
        schema_events, event_node_idxs, entity_graph, entity_node_idxs, primitive_idxs, global_graph = read_schema(schema_file_dir)
    
    # print(schema_events.keys())

    # match_one_schema(event_graph_h, schema_events['sbu:Events/15022/natural-disaster-progression']["nx_graph"], event_temps_h, schema_events['sbu:Events/15022/natural-disaster-progression']["temporal"], 0.8, 1)
    # match_events(event_graph_h, schema_events, event_temps_h, 0.8, 2)

    evt_map, ent_map, arg_filler, root_id = matching_graphs(event_graph_h, event_temps_h, arg_name_dict_h, schema_events, 0.8, 2, orgs[0])

    pred_dict, matched_ids = generate_pred_values(evt_map, event_node_idxs, primitive_idxs)
    print(pred_dict)
    pidxs, pprovs, pargs = new_prediction(schema_events[root_id]["prim_child_idxs"], event_node_idxs, schema_events[root_id]["arg_id_dict"], arg_id_dict_h, evt_map, ent_map, arg_filler, pred_dict, 0.3)
    print(pidxs)
            

