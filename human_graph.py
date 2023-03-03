import json
import networkx as nx

from utils import extract_headwords, expand_children, print_networkx_graph
from event_temporal import expand_temporal
from write_sdf import remove_conflict_temporal_relations

def read_human_graph(human_graph):    
    graph_dict = human_graph["instances"][0]
    event_graph = nx.DiGraph()
    event_node_idx = {}
    event_node_num = 0

    primitive_ids = []
    event_temps = {} # {event_idx: [list of descendant event idxs]}, keys and values include both primitive events and non-primitive events.
    event_children = {} # {event_idx: list of its children}, a temporary variable.

    # read the entity-entity relation graph
    entity_graph = nx.DiGraph()
    entity_node_idx = {}
    entity_node_num = 0

    for entity in graph_dict["entities"]:
        if "ta2qlabel" in entity:
            if type(entity["ta2qlabel"]) != list:
                qlabels = [entity["ta2qlabel"]]
                qnodes = [entity["ta2qnode"]]
            else:
                qlabels = entity["ta2qlabel"]  
                qnodes = entity["ta2qnode"]       
        else:
            qlabels = []
            qnodes = []      

        entity_graph.add_node(entity_node_num, id=entity["@id"], name=entity["name"], qnodes=qnodes, qlabels=qlabels, text=entity["name"], provenance=entity["@id"].split('/')[-1])
        entity_node_idx.update({entity["@id"]: entity_node_num})
        entity_node_num += 1        

    for relation in graph_dict["relations"]:
        if relation["relationSubject"] in entity_node_idx and relation["relationObject"] in entity_node_idx:
            start = entity_node_idx[relation["relationSubject"]]
            end = entity_node_idx[relation["relationObject"]]
            entity_graph.add_edge(start, end, type=relation["relationPredicate"])

    for i,event in enumerate(graph_dict["events"]):
        if "ta2qlabel" in event:
            if type(event["ta2qlabel"]) != list:
                qlabels = [event["ta2qlabel"]]
                qnodes = [event["ta2qnode"]]
            else:
                qlabels = event["ta2qlabel"]
                qnodes = [event["ta2qnode"]]
        else:
            qlabels = []
            qnodes = []

        if "children" in event and len(event["children"]) != 0:
            primitive = False
        else:
            primitive = True
            primitive_ids.append(i)

        description = event.get("description", "")
        event_graph.add_node(event_node_num, id=event["@id"], qnodes=qnodes, qlabels=qlabels, name=event["name"], description=description, primitive=primitive, children=[], importances=[], children_gate="N/A", ta1exp="", provenance=event["provenance"])
        event_node_idx.update({event["@id"]: event_node_num})
        event_node_num += 1

    for i,event in enumerate(graph_dict["events"]):
        event_node_i = event_graph.nodes(data=True)[i]
        if "ta1explanation" in event:
            event_node_i["ta1exp"] = event["ta1explanation"]

        if not event_node_i["primitive"]:
            event_children[i] = []
            children_list = event["children"]
            event_node_i["children_gate"] = event["children_gate"]
            for child in children_list:
                child_idx = event_node_idx[child["child"]]
                event_children[i].append(child_idx)
                importance = child.get("importance", 1.0)
                event_node_i["children"].append(child_idx)
                event_node_i["importances"].append(importance)

    for relation in graph_dict["relations"]:
        if relation["relationSubject"] in event_node_idx and relation["relationObject"] in event_node_idx:
            start = event_node_idx[relation["relationSubject"]]
            end = event_node_idx[relation["relationObject"]]
            event_graph.add_edge(start, end, type="temporal") 
            if start not in event_temps:
                event_temps[start] = [end]
            else:
                if end not in event_temps[start]:
                    event_temps[start].append(end)

    for event in graph_dict["events"]:
        event_id = event["@id"]
        if "children" in event:
            for child in event["children"]:
                if "outlinks" in child:
                    neighbors = child["outlinks"]
                    for neighbor in neighbors:
                        start = event_node_idx[child["child"]]
                        end = event_node_idx[neighbor]
                        event_graph.add_edge(start, end, type="temporal")
                        if start not in event_temps:
                            event_temps[start] = [end]
                        else:
                            if end not in event_temps[start]:
                                event_temps[start].append(end)

        # the event event temporal relation could also exist in the outlinks
        if "outlinks" in event:
            for neighbor in event["outlinks"]:
                start = event_node_idx[event_id]
                end = event_node_idx[neighbor]
                event_graph.add_edge(start, end, type="temporal")
                if start not in event_temps:
                    event_temps[start] = [end]
                else:
                    if end not in event_temps[start]:
                        event_temps[start].append(end)

        # could also exist in relations (ISI Schema)
        if "relations" in event:
            for rel in event["relations"]:
                if rel["relationSubject"] in entity_node_idx and rel["relationObject"] in entity_node_idx:
                    start = entity_node_idx[rel["relationSubject"]]
                    end = entity_node_idx[rel["relationObject"]]
                    entity_graph.add_edge(start, end, type=rel["relationPredicate"])
                if rel["relationSubject"] in event_node_idx and rel["relationObject"] in event_node_idx:
                    start = event_node_idx[rel["relationSubject"]]
                    end = event_node_idx[rel["relationObject"]]
                    if start not in event_temps:
                        event_temps[start] = [end]
                    else:
                        if end not in event_temps[start]:
                            event_temps[start].append(end)

    event_child_idxs = expand_children(event_children) # expanding event children

    # read arguments
    # read participants: event argument roles:
    # output: arg_name_dict: {event_idx: {ta2_entity_idx: role_name}} // role_name is the keyword or other textual descriptions of the event argument role.
    # output: arg_id_dict: {event_idx: {ta2_entity_idx: role_id}} // role_arg_id is the @id field for an argument
    arg_name_dict, arg_id_dict = {}, {}
    for i,event in enumerate(graph_dict["events"]):
        event_idx = event_node_idx[event["@id"]]
        if event_idx not in arg_name_dict:
            arg_name_dict.update({event_idx: {}})
            arg_id_dict.update({event_idx: {}})
        # if not participants, we keep the event_idx key as an empty dict
        if "participants" in event:
            arguments = event["participants"]
            # if i == 14:
            #     print(arguments)
            for arg in arguments:
                role_type = arg["roleName"]
                values = arg["values"]

                if values["ta2entity"] in entity_node_idx:
                    entity_idx = entity_node_idx[values["ta2entity"]]
                elif values["ta2entity"] in event_node_idx:
                    entity_idx = event_node_idx[values["ta2entity"]]
                else:
                    continue
                # if i == 14:
                #     print(arg)
                arg_name_dict[event_idx].update({entity_idx: role_type})
                arg_id_dict[event_idx].update({entity_idx: arg["@id"]})
    # print(entity_node_idx)
    # print(arg_id_dict[14])
    # for node in event_graph.nodes(data=True):
    #     print(node)
    # for node in entity_graph.nodes(data=True):
    #     print(node)
    # print(event_child_idxs)
    # print(event_temps)
    # print(primitive_ids)
    expanded = expand_temporal(event_temps, event_child_idxs, primitive_ids)
    new_temporal = remove_conflict_temporal_relations(expanded)

    return (event_graph, event_node_idx, new_temporal, event_child_idxs), (entity_graph, entity_node_idx), (arg_name_dict, arg_id_dict), primitive_ids


if __name__ == "__main__":
    # files = ["ce2002abridged", "ce2002full", "ce2002critical", "ce2004abridged", "ce2004full", "ce2004newcritical"]
    files = ["ce2002abridged"]

    for filename in files:
        graph_file_dir = "./task2_graphs_qz8/" + filename + "_GraphG.json"
        print(graph_file_dir)
        read_human_graph(graph_file_dir)