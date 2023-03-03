import json
import math
import os
import numpy as np

# from docx import Document
# from docx.shared import Pt
# from docx.shared import RGBColor

from human_graph import read_human_graph
from schema import read_schema
from ie_graph import read_ie_cluster
from read_xpo_json import read_xpo

from event_temporal import expand_temporal, linearize_graph

def visualize_task1_str(instance, event_graph_h, entity_graph_h, expanded_temp_dict_h, expanded_temp_dict_s, prim_ids_h, event_mapping, arg_name_dict_h):
    # with open(human_dir, 'r', encoding="utf-8") as f:
    #     human_g = json.loads(f.read())["instances"][0]
    
    # (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), prim_ids_h = read_ie_cluster(human_dir, event_dicts[0], event_dicts[1])
    # (event_graph_s, old_event_node_idx_s, event_temps_s, event_child_idxs_s), (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s), prim_ids_s = read_schema(schema_dir)

    event_node_idx_s = {}
    for i,event in enumerate(instance["events"]):
        if event["ta1ref"] != "kairos:NULL":
            event_node_idx_s[event['@id']] = i

    instance_nodes = event_graph_h.nodes(data=True)
    entity_nodes = entity_graph_h.nodes(data=True)

    # print(event_temps_h)
    # expanded_temp_dict_h = expand_temporal(event_temps_h, event_child_idxs_h, prim_ids_h)
    # # print(expanded_temp_dict_h)
    # expanded_temp_dict_s = expand_temporal(event_temps_s, event_child_idxs_s, prim_ids_s)

    event_seq_ids = linearize_graph(expanded_temp_dict_h, prim_ids_h)
    
    event_labels = [0 for _ in range(len(event_seq_ids))] # 1 for instantiated, 2 for predicted
    # print(event_seq_ids)

    # construct entity map
    # entity_map = {}
    # # for entity in human_g["entities"]:
    # #     entity_map.update({entity["@id"]: entity["name"]})
    # for i,node in entity_graph_h:
    #     entity_map.update({})

    # # construct event map
    # event_map = {}
    # for event in human_g["events"]:
    #     event_map.update({event["provenance"]: event})

    instantiated, predicted = {}, {}
    for i,event in enumerate(instance["events"]):
        if event["ta1ref"] != "kairos:NULL":
            if "provenance" in event:
                if event["provenance"] != "n/a":
                    instantiated.update({event["@id"]: event})
                    # inst_idx = event_node_idx_h[event_map[event["provenance"]]["@id"]]
                    inst_idx = event_mapping[i][0]
                    if inst_idx in event_seq_ids:
                        pos_idx = event_seq_ids.index(inst_idx)
                        event_labels[pos_idx] = 1
            if "predictionProvenance" in event:
                if event["@id"] not in event["predictionProvenance"]:
                    predicted.update({event["@id"]: event})

    # print(instantiated.keys())
    # print(predicted.keys())
    # print(predicted.keys())
    # print(event_labels)
    # # calculate relation list
    # relation_list = []
    # for rela, rel_list in relations.items():
    #     for rel in rel_list:
    #         relation_list.append((rela, rel))
    # deal with the predicted events:
    # print(predicted.keys())
    # print(expanded_temp_dict.keys())
    core_provs = {}
    for pred_event_id, event in predicted.items():
        # predictions = predicted[pred_event_id]
        # print(pred_event_id)
        se_prov_idx_list = []
        he_prov_idx_list = []

        # print(pred_event_id)
        pred_idx = event_node_idx_s[pred_event_id]
        # print(pred_idx)

        prov_list = event["predictionProvenance"]
        # print(prov_list)
        for prov in prov_list:
            if prov.split(":")[1].startswith("Events"):
                seidx = event_node_idx_s[prov]
                # heidx = event_node_idx_h[event_map[instance["events"][seidx]["provenance"]]["@id"]]
                heidx = event_mapping[seidx][0]

                se_prov_idx_list.append(seidx)
                he_prov_idx_list.append(heidx)
        
        # sorting
        index_list = [event_seq_ids.index(heidx) for heidx in he_prov_idx_list]
        sorted_index_list = np.argsort(index_list).tolist()

        sorted_seidxs = [se_prov_idx_list[idx] for idx in sorted_index_list]
        sorted_heidxs = [he_prov_idx_list[idx] for idx in sorted_index_list]

        pos = -1
        # find the position
        # print(expanded_temp_dict_s)
        for k,se_idx in enumerate(sorted_seidxs):
            if se_idx in expanded_temp_dict_s[pred_idx]:
                pos = k 
        # print(pred_event_id)
        # print(pos)
        # print(sorted_seidxs)
        last_seidx = sorted_seidxs[-1]

        if pos != -1:
            # print(1)
            mapped_pos = event_seq_ids.index(sorted_heidxs[pos])
            event_seq_ids.insert(mapped_pos, str(pred_idx))
            event_labels.insert(mapped_pos, 2)
            core_provs.update({str(pred_idx): sorted_heidxs[pos]})
        elif pred_idx in expanded_temp_dict_s[last_seidx]:
            # print(2)
            last_heidx = sorted_heidxs[-1]
            mapped_pos = event_seq_ids.index(last_heidx)
            event_seq_ids.insert(mapped_pos+1, str(pred_idx))
            event_labels.insert(mapped_pos+1, 2)
            core_provs.update({str(pred_idx): last_heidx})

        else:
            # print(3)
            pass
    
    # print(event_seq_ids)
    # print(event_labels)
    # read ta2 entities:
    ta2_entities = {}
    for entity in instance["entities"]:
        if "ta2qnode" in entity:
            ta2_entities.update({entity["@id"]: entity})

    # print(event_seq_ids)
    # write out
    # print(event_seq_ids)
    # print(event_seq_ids)
    # doc = Document()
    giant_string = ""
    for i in range(len(event_seq_ids)):
        label = event_labels[i]
        idx = int(event_seq_ids[i])
        str_idx = event_seq_ids[i]

        if label != 2: # instance events
            node_i = instance_nodes[idx]
            if label == 1:
                line = str(i+1) + '. ' + "[INSTANTIATED] " + node_i["name"] + ": " + node_i["description"] + ". "
            else:
                line = str(i+1) + '. ' + node_i["name"] + ": " + node_i["description"] + ". "

            roles = arg_name_dict_h[idx] # {entity_idx: role_name}
            role_line = '('
            for ent_idx, role_name in roles.items():
                ta2entityname = entity_nodes[ent_idx]["text"]
                if role_name == None:
                    continue
                role_line += (role_name + "= " + ta2entityname + ', ')

            role_line = role_line[:-2] + ')'
            line += role_line 
            line += ' (Graph G)'

            giant_string = giant_string + line + '\n'
            # line1 = doc.add_paragraph()
            # run1 = line1.add_run(line)
            # if label == 1:
            #     # run1.font.italic = True
            #     run1.font.color.rgb = RGBColor(250, 0, 0)
        
        else: # predicted_events
            event_i = instance["events"][idx]
            line = str(i+1) + '. ' + "[PREDICTED] " + event_i["name"] + ". "
            roles = event_i["participants"]

            if "ta1explanation" in event_i:
                line += event_i["ta1explanation"] + ' '

            role_line = '('
            for role in roles:
                if "values" in role:
                    if type(role["values"]) == list:
                        ta2entity = role["values"][0]["ta2entity"]
                    else:
                        ta2entity = role["values"]["ta2entity"]

                    ta2entityname = ta2_entities[ta2entity]["name"]
                    role_name = role["roleName"]
                    role_line += role_name + "= " + ta2entityname + ', '

            role_line = role_line[:-2] + ')'
            line += role_line

            # add prediction provenance
            line += ", justification=["
            # pred_provs = event_i["prediction"]["predictionProvenance"]
            # pred_prov_idxs = []
            pos_idx = event_seq_ids.index(core_provs[str_idx])
            line += str(pos_idx + 1)
            
            # for prov in pred_provs:
            #     if prov.split(':')[1].startswith("Events"):
            #         prov_idx = event_node_idx_s[prov]
            #         mapped_idx = event_node_idx_h[event_map[instance["events"][prov_idx]["provenance"]]["@id"]]
            #         if mapped_idx in event_seq_ids:
            #             pos_idx = event_seq_ids.index(mapped_idx)
            #             line += str(pos_idx + 1)
            #             line += ","
            # line = line[:-1]
            line += ']'

            line += (" (Schema ID= " + str(idx) + ")")
            giant_string = giant_string + line + '\n'

            # line1 = doc.add_paragraph()
            # run1 = line1.add_run(line)
            # run1.font.bold = True

        # print(line)
    # doc.save(output_dir)
    # with open(output_dir, 'w', encoding="utf-8") as f:
    #     f.write(giant_string)
    return giant_string

'''
def visualize_task1(task1_sdf, event_graph_h, entity_graph_h, expanded_temp_dict_h, expanded_temp_dict_s, prim_ids_h, event_mapping, arg_name_dict_h, output_dir):
    instance = task1_sdf["instances"][0]
    # with open(human_dir, 'r', encoding="utf-8") as f:
    #     human_g = json.loads(f.read())["instances"][0]
    
    # (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), prim_ids_h = read_ie_cluster(human_dir, event_dicts[0], event_dicts[1])
    # (event_graph_s, old_event_node_idx_s, event_temps_s, event_child_idxs_s), (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s), prim_ids_s = read_schema(schema_dir)

    event_node_idx_s = {}
    for i,event in enumerate(instance["events"]):
        if event["ta1ref"] != "kairos:NULL":
            event_node_idx_s[event['@id']] = i

    instance_nodes = event_graph_h.nodes(data=True)
    entity_nodes = entity_graph_h.nodes(data=True)

    # print(event_temps_h)
    # expanded_temp_dict_h = expand_temporal(event_temps_h, event_child_idxs_h, prim_ids_h)
    # # print(expanded_temp_dict_h)
    # expanded_temp_dict_s = expand_temporal(event_temps_s, event_child_idxs_s, prim_ids_s)

    event_seq_ids = linearize_graph(expanded_temp_dict_h, prim_ids_h)
    
    event_labels = [0 for _ in range(len(event_seq_ids))] # 1 for instantiated, 2 for predicted
    # print(event_seq_ids)

    # construct entity map
    # entity_map = {}
    # # for entity in human_g["entities"]:
    # #     entity_map.update({entity["@id"]: entity["name"]})
    # for i,node in entity_graph_h:
    #     entity_map.update({})

    # # construct event map
    # event_map = {}
    # for event in human_g["events"]:
    #     event_map.update({event["provenance"]: event})

    instantiated, predicted = {}, {}
    for i,event in enumerate(instance["events"]):
        if event["ta1ref"] != "kairos:NULL":
            if "provenance" in event:
                if event["provenance"] != "n/a":
                    instantiated.update({event["@id"]: event})
                    # inst_idx = event_node_idx_h[event_map[event["provenance"]]["@id"]]
                    inst_idx = event_mapping[i][0]
                    if inst_idx in event_seq_ids:
                        pos_idx = event_seq_ids.index(inst_idx)
                        event_labels[pos_idx] = 1
            if "prediction" in event:
                predicted.update({event["@id"]: event})

    # print(instantiated.keys())
    # print(predicted.keys())
    # print(predicted.keys())
    # print(event_labels)
    # # calculate relation list
    # relation_list = []
    # for rela, rel_list in relations.items():
    #     for rel in rel_list:
    #         relation_list.append((rela, rel))
    # deal with the predicted events:
    # print(predicted.keys())
    # print(expanded_temp_dict.keys())
    core_provs = {}
    for pred_event_id, event in predicted.items():
        # predictions = predicted[pred_event_id]
        # print(pred_event_id)
        se_prov_idx_list = []
        he_prov_idx_list = []

        # print(pred_event_id)
        pred_idx = event_node_idx_s[pred_event_id]
        # print(pred_idx)

        prov_list = event["prediction"]["predictionProvenance"]
        # print(prov_list)
        for prov in prov_list:
            if prov.split(":")[1].startswith("Events"):
                seidx = event_node_idx_s[prov]
                # heidx = event_node_idx_h[event_map[instance["events"][seidx]["provenance"]]["@id"]]
                heidx = event_mapping[seidx][0]

                se_prov_idx_list.append(seidx)
                he_prov_idx_list.append(heidx)
        
        # sorting
        index_list = [event_seq_ids.index(heidx) for heidx in he_prov_idx_list]
        sorted_index_list = np.argsort(index_list).tolist()

        sorted_seidxs = [se_prov_idx_list[idx] for idx in sorted_index_list]
        sorted_heidxs = [he_prov_idx_list[idx] for idx in sorted_index_list]

        pos = -1
        # find the position
        # print(expanded_temp_dict_s)
        for k,se_idx in enumerate(sorted_seidxs):
            if se_idx in expanded_temp_dict_s[pred_idx]:
                pos = k 
        # print(pred_event_id)
        # print(pos)
        last_seidx = sorted_seidxs[-1]

        if pos != -1:
            # print(1)
            mapped_pos = event_seq_ids.index(sorted_heidxs[pos])
            event_seq_ids.insert(mapped_pos, str(pred_idx))
            event_labels.insert(mapped_pos, 2)
            core_provs.update({str(pred_idx): sorted_heidxs[pos]})
        elif pred_idx in expanded_temp_dict_s[last_seidx]:
            # print(2)
            last_heidx = sorted_heidxs[-1]
            mapped_pos = event_seq_ids.index(last_heidx)
            event_seq_ids.insert(mapped_pos+1, str(pred_idx))
            event_labels.insert(mapped_pos+1, 2)
            core_provs.update({str(pred_idx): last_heidx})

        else:
            # print(3)
            pass
    
    # print(event_seq_ids)
    # print(event_labels)
    # read ta2 entities:
    ta2_entities = {}
    for entity in instance["entities"]:
        if "ta2qnode" in entity:
            ta2_entities.update({entity["@id"]: entity})

    # print(event_seq_ids)
    # write out
    # print(event_seq_ids)
    # print(event_seq_ids)
    doc = Document()
    for i in range(len(event_seq_ids)):
        label = event_labels[i]
        idx = int(event_seq_ids[i])
        str_idx = event_seq_ids[i]

        if label != 2: # instance events
            node_i = instance_nodes[idx]
            line = str(i+1) + '. ' + node_i["name"] + ": " + node_i["description"] + ". "

            roles = arg_name_dict_h[idx] # {entity_idx: role_name}
            role_line = '('
            for ent_idx, role_name in roles.items():
                ta2entityname = entity_nodes[ent_idx]["text"]
                if role_name == None:
                    continue
                role_line += (role_name + "= " + ta2entityname + ', ')

            role_line = role_line[:-2] + ')'
            line += role_line 
            line += ' (Graph G)'
            line1 = doc.add_paragraph()
            run1 = line1.add_run(line)
            if label == 1:
                # run1.font.italic = True
                run1.font.color.rgb = RGBColor(250, 0, 0)
        
        else: # predicted_events
            event_i = instance["events"][idx]
            line = str(i+1) + '. ' + event_i["name"] + ". "
            roles = event_i["participants"]

            if "ta1explanation" in event_i:
                line += event_i["ta1explanation"] + ' '

            role_line = '('
            for role in roles:
                if "values" in role:
                    if type(role["values"]) == list:
                        ta2entity = role["values"][0]["ta2entity"]
                    else:
                        ta2entity = role["values"]["ta2entity"]

                    ta2entityname = ta2_entities[ta2entity]["name"]
                    role_name = role["roleName"]
                    role_line += role_name + "= " + ta2entityname + ', '

            role_line = role_line[:-2] + ')'
            line += role_line

            # add prediction provenance
            line += ", justification=["
            # pred_provs = event_i["prediction"]["predictionProvenance"]
            # pred_prov_idxs = []
            pos_idx = event_seq_ids.index(core_provs[str_idx])
            line += str(pos_idx + 1)
            
            # for prov in pred_provs:
            #     if prov.split(':')[1].startswith("Events"):
            #         prov_idx = event_node_idx_s[prov]
            #         mapped_idx = event_node_idx_h[event_map[instance["events"][prov_idx]["provenance"]]["@id"]]
            #         if mapped_idx in event_seq_ids:
            #             pos_idx = event_seq_ids.index(mapped_idx)
            #             line += str(pos_idx + 1)
            #             line += ","
            # line = line[:-1]
            line += ']'

            line += (" (Schema ID= " + str(idx) + ")")
            line1 = doc.add_paragraph()
            run1 = line1.add_run(line)
            run1.font.bold = True

        # print(line)
    doc.save(output_dir)






def visualize_task2(ta2_dir, human_dir, schema_dir, output_dir):
    with open(ta2_dir, 'r', encoding="utf-8") as f:
        instance = json.loads(f.read())["instances"][0]
    
    with open(human_dir, 'r', encoding="utf-8") as f:
        human_g = json.loads(f.read())["instances"][0]
    
    (event_graph_h, event_node_idx_h, event_temps_h, event_child_idxs_h), (entity_graph_h, entity_node_idx_h), (arg_name_dict_h, arg_id_dict_h), prim_ids_h = read_human_graph(human_dir)
    (event_graph_s, old_event_node_idx_s, event_temps_s, event_child_idxs_s), (entity_graph_s, entity_node_idx_s), (arg_name_dict_s, arg_id_dict_s), prim_ids_s = read_schema(schema_dir)

    event_node_idx_s = {}
    for i,event in enumerate(instance["events"]):
        if event["ta1ref"] != "kairos:NULL":
            event_node_idx_s[event['@id']] = i

    instance_nodes = event_graph_h.nodes(data=True)

    expanded_temp_dict_h = expand_temporal(event_temps_h, event_child_idxs_h, prim_ids_h)
    expanded_temp_dict_s = expand_temporal(event_temps_s, event_child_idxs_s, prim_ids_s)

    event_seq_ids = linearize_graph(expanded_temp_dict_h, prim_ids_h)

    event_labels = [0 for _ in range(len(event_seq_ids))] # 1 for instantiated, 2 for predicted
    print(event_seq_ids)

    # construct entity map
    entity_map = {}
    for entity in human_g["entities"]:
        entity_map.update({entity["@id"]: entity["name"]})

    # construct event map
    event_map = {}
    for event in human_g["events"]:
        event_map.update({event["provenance"]: event})

    instantiated, predicted = {}, {}
    for i,event in enumerate(instance["events"]):
        if event["ta1ref"] != "kairos:NULL":
            if "provenance" in event:
                if event["provenance"] != "n/a":
                    instantiated.update({event["@id"]: event})
                    inst_idx = event_node_idx_h[event_map[event["provenance"]]["@id"]]
                    if inst_idx in event_seq_ids:
                        pos_idx = event_seq_ids.index(inst_idx)
                        event_labels[pos_idx] = 1
            if "prediction" in event:
                predicted.update({event["@id"]: event})

    print(instantiated.keys())
    print(predicted.keys())
    # print(predicted.keys())
    # print(event_labels)
    # # calculate relation list
    # relation_list = []
    # for rela, rel_list in relations.items():
    #     for rel in rel_list:
    #         relation_list.append((rela, rel))
    # deal with the predicted events:
    # print(predicted.keys())
    # print(expanded_temp_dict.keys())
    core_provs = {}
    for pred_event_id, event in predicted.items():
        # predictions = predicted[pred_event_id]
        # print(pred_event_id)
        se_prov_idx_list = []
        he_prov_idx_list = []

        # print(pred_event_id)
        pred_idx = event_node_idx_s[pred_event_id]
        # print(pred_idx)

        prov_list = event["prediction"]["predictionProvenance"]
        # print(prov_list)
        for prov in prov_list:
            if prov.split(":")[1].startswith("Events"):
                seidx = event_node_idx_s[prov]
                heidx = event_node_idx_h[event_map[instance["events"][seidx]["provenance"]]["@id"]]

                se_prov_idx_list.append(seidx)
                he_prov_idx_list.append(heidx)
        
        # sorting
        index_list = [event_seq_ids.index(heidx) for heidx in he_prov_idx_list]
        sorted_index_list = np.argsort(index_list).tolist()

        sorted_seidxs = [se_prov_idx_list[idx] for idx in sorted_index_list]
        sorted_heidxs = [he_prov_idx_list[idx] for idx in sorted_index_list]

        pos = -1
        # find the position
        # print(expanded_temp_dict_s)
        for k,se_idx in enumerate(sorted_seidxs):
            if se_idx in expanded_temp_dict_s[pred_idx]:
                pos = k 
        # print(pred_event_id)
        # print(pos)
        last_seidx = sorted_seidxs[-1]

        if pos != -1:
            # print(1)
            mapped_pos = event_seq_ids.index(sorted_heidxs[pos])
            event_seq_ids.insert(mapped_pos, str(pred_idx))
            event_labels.insert(mapped_pos, 2)
            core_provs.update({str(pred_idx): sorted_heidxs[pos]})
        elif pred_idx in expanded_temp_dict_s[last_seidx]:
            # print(2)
            last_heidx = sorted_heidxs[-1]
            mapped_pos = event_seq_ids.index(last_heidx)
            event_seq_ids.insert(mapped_pos+1, str(pred_idx))
            event_labels.insert(mapped_pos+1, 2)
            core_provs.update({str(pred_idx): last_heidx})

        else:
            # print(3)
            pass
    
    # print(event_seq_ids)
    # print(event_labels)
    # read ta2 entities:
    ta2_entities = {}
    for entity in instance["entities"]:
        if "ta2qnode" in entity:
            ta2_entities.update({entity["@id"]: entity})

    # print(event_seq_ids)
    # write out
    # print(event_seq_ids)
    # print(event_seq_ids)
    doc = Document()
    for i in range(len(event_seq_ids)):
        label = event_labels[i]
        idx = int(event_seq_ids[i])
        str_idx = event_seq_ids[i]

        if label != 2: # instance events
            node_i = instance_nodes[idx]
            line = str(i+1) + '. ' + node_i["name"] + ": " + node_i["description"] + ". "

            roles = human_g["events"][idx]["participants"]
            role_line = '('
            for role in roles:
                ta2entity = role["values"]["ta2entity"]
                if ta2entity.startswith("nist:Events"):
                    continue
                role_name = role["roleName"]
                
                ta2entityname = entity_map[ta2entity]
                role_line += role_name + "= " + ta2entityname + ', '

            role_line = role_line[:-2] + ')'
            line += role_line 
            line += ' (Graph G)'
            line1 = doc.add_paragraph()
            run1 = line1.add_run(line)
            if label == 1:
                # run1.font.italic = True
                run1.font.color.rgb = RGBColor(250, 0, 0)
        
        else: # predicted_events
            event_i = instance["events"][idx]
            line = str(i+1) + '. ' + event_i["name"] + ". "
            roles = event_i["participants"]

            if "ta1explanation" in event_i:
                line += event_i["ta1explanation"] + ' '

            role_line = '('
            for role in roles:
                if "values" in role:
                    if type(role["values"]) == list:
                        ta2entity = role["values"][0]["ta2entity"]
                    else:
                        ta2entity = role["values"]["ta2entity"]

                    ta2entityname = ta2_entities[ta2entity]["name"]
                    role_name = role["roleName"]
                    role_line += role_name + "= " + ta2entityname + ', '

            role_line = role_line[:-2] + ')'
            line += role_line

            # add prediction provenance
            line += ", justification=["
            # pred_provs = event_i["prediction"]["predictionProvenance"]
            # pred_prov_idxs = []
            pos_idx = event_seq_ids.index(core_provs[str_idx])
            line += str(pos_idx + 1)
            
            # for prov in pred_provs:
            #     if prov.split(':')[1].startswith("Events"):
            #         prov_idx = event_node_idx_s[prov]
            #         mapped_idx = event_node_idx_h[event_map[instance["events"][prov_idx]["provenance"]]["@id"]]
            #         if mapped_idx in event_seq_ids:
            #             pos_idx = event_seq_ids.index(mapped_idx)
            #             line += str(pos_idx + 1)
            #             line += ","
            # line = line[:-1]
            line += ']'

            line += (" (Schema ID= " + str(idx) + ")")
            line1 = doc.add_paragraph()
            run1 = line1.add_run(line)
            run1.font.bold = True

        # print(line)
    doc.save(output_dir)


if __name__ == "__main__":
    org_list = ["cmu", "sbu", "ibm", "resin", "isi"]
    org_list = ["resin"]
    # doc_list = ["ce2002abridged", "ce2002critical", "ce2002full", "ce2004abridged", "ce2004newcritical", "ce2004full"]

    # org_list = ["cmu"]
    doc_list = ["ce2002abridged"]

    role_xpo_dir = "./xpo_v3.2_freeze_exp.json"
    event_m, role_m = read_xpo(role_xpo_dir)

    # org_list = ["isi"]
    # doc_list = ["ce2002abridged"]
    # task2_graph_dir = "./task2_graphs_qz8"
    # schema_graph_dir = "./schemas_qz8"
    # task2_sdf_dir = "./task2_outputs_qz8/sdf"
    # task2_hrf_dir = "./task2_outputs_qz8/hrf"

    # for team in org_list:
    #     for graph in doc_list:

    #         h_dir = os.path.join(task2_graph_dir, (graph + "_GraphG.json"))
    #         s_dir = os.path.join(schema_graph_dir, (team + "-schemalib.json"))
    #         sdf_dir = os.path.join(task2_sdf_dir, (team + "-resin-task2-" + graph + ".json"))
    #         hrf_dir = os.path.join(task2_hrf_dir, (team + "-resin-task2-" + graph + ".docx"))

    #         visualize_task2(sdf_dir, h_dir, s_dir, hrf_dir)
    
    task1_graph_dir = "./task1_graphs_qz8/json"
    schema_graph_dir = "./schemas_qz8"
    task1_sdf_dir = "./task1_outputs_qz8/sdf"
    task1_hrf_dir = "./task1_outputs_qz8/hrf"
    task1_results_dir = "./task1_outputs_qz8"

    task1_graph_dir = "./task1_graphs_dryrun2"
    schema_graph_dir = "./schemas_qz8"
    task1_sdf_dir = "./task1_outputs_dryrun2/sdf"
    task1_hrf_dir = "./task1_outputs_dryrun2/hrf"
    task1_results_dir = "./task1_outputs_dryrun2"

    graphs = ["ce2002", "ce2004", "ce2039"]
    graphs = os.listdir(task1_graph_dir)
    # graphs = ["ce2002"]

    for team in org_list:
        for graph in graphs:
            print(team, graph)
            h_dir = os.path.join(task1_graph_dir, graph)
            s_dir = os.path.join(schema_graph_dir, (team + "-schemalib.json"))
            sdf_dir = os.path.join(task1_sdf_dir, (team + "-resin-task1-" + graph + ".json"))
            hrf_dir = os.path.join(task1_hrf_dir, (team + "-resin-task1-" + graph + ".docx"))

            event_map_dir = os.path.join(task1_results_dir, "matching", "event-mappings", (team+'-'+graph+'.json'))
            print(event_map_dir)
            with open(event_map_dir, 'r', encoding="utf-8") as f1:
                str_event_maps = json.loads(f1.read())
            event_maps = {}
            for k,v in str_event_maps.items():
                event_maps.update({int(k): v})

            visualize_task1(sdf_dir, h_dir, s_dir, hrf_dir, (event_m, role_m), event_maps)
'''