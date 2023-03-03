import json
import networkx as nx

from copy import deepcopy

from utils import extract_headwords, expand_children, print_networkx_graph
from event_temporal import expand_temporal

def get_root_nodes(event_children, nodes_num):
    # input: {parent_id: [list of children ids]} both primitive and non-primitive events are possible.
    # output: list of root nodes
    parent_set = set()
    for parent,children in event_children.items():
        for child in children:
            if child not in parent_set:
                parent_set.add(child)

    root_idxs = []
    for i in range(nodes_num):
        if i not in parent_set:
            root_idxs.append(i)

    return root_idxs
    

def expand_primitive_children(event_children):
    # event_children: {event_idx: [list of its children]}
    # OUTPUT: expanded_children: {event_idx: [list of all its descendant primitive events (leaf nodes)]}

    expanded_children = {}
    for event_idx in event_children:
        expanded_children.update({event_idx: []})

    # do BFS for every single node
    for event_idx in event_children:
        queue = [event_idx]
        while len(queue) != 0:
            start_idx = queue.pop(0)
            if start_idx not in event_children:
                if start_idx not in expanded_children[event_idx]:
                    expanded_children[event_idx].append(start_idx)
            else:
                for child in event_children[start_idx]:
                    queue.append(child)
    
    return expanded_children 


def expand_all_children(event_children):
    # event_children: {event_idx: [list of its children]}
    # OUTPUT: expanded_children: {event_idx: [list of all its descendant primitive events (leaf nodes)]}

    expanded_children = {}
    for event_idx in event_children:
        expanded_children.update({event_idx: []})

    # do BFS for every single node
    for event_idx in event_children:
        queue = [event_idx]
        while len(queue) != 0:
            start_idx = queue.pop(0)
            if start_idx not in event_children:
                if start_idx not in expanded_children[event_idx]:
                    expanded_children[event_idx].append(start_idx)
            else:
                if start_idx not in expanded_children[event_idx]:
                    expanded_children[event_idx].append(start_idx)
                for child in event_children[start_idx]:
                    queue.append(child)
    
    return expanded_children 


def read_schema(schema_dir):
    with open(schema_dir, 'r', encoding="utf-8") as f:
        schema_dict = json.loads(f.read())
    
    # Step 1: We need to read in entities first.
    entity_graph = nx.DiGraph()
    entity_node_idxs = {}
    entity_node_num = 0

    for entity in schema_dict["entities"]: 
        if "qlabel" in entity:
            if type(entity["qlabel"]) != list:
                qlabels = [entity["qlabel"]]
                qnodes = [entity["qnode"]]
            else:
                qlabels = entity["qlabel"]       
                qnodes = entity["qnode"]       
        else:
            qlabels = []
            qnodes = []       

        entity_graph.add_node(entity_node_num, id=entity["@id"], qnodes=qnodes, qlabels=qlabels, name=entity["name"])
        entity_node_idxs.update({entity["@id"]: entity_node_num})
        entity_node_num += 1

    for relation in schema_dict["relations"]:
        if relation["relationSubject"] in entity_node_idxs and relation["relationObject"] in entity_node_idxs:
            start = entity_node_idxs[relation["relationSubject"]]
            end = entity_node_idxs[relation["relationObject"]]
            entity_graph.add_edge(start, end, type=relation["relationPredicate"])
    
    # Step 2: We do one pass on the events to get event_node_idxs
    event_node_idxs = {}
    event_node_num = 0
    for i,event in enumerate(schema_dict["events"]):
        event_node_idxs.update({event["@id"]: event_node_num})
        event_node_num += 1
    
    # print("total number ", len(event_node_idxs))
    
    # Step 3: We do a second pass on the event_graph to find out the root idxs
    event_children = {}
    primitive_idxs = []
    for i,event in enumerate(schema_dict["events"]):
        if "children" in event and len(event["children"]) != 0:
            child_idx_list = []
            children = event["children"]
            for child in children:
                child_idx = event_node_idxs[child["child"]]
                if child_idx not in child_idx_list:
                    child_idx_list.append(child_idx)
            event_children[i] = child_idx_list.copy()
        else:
            primitive_idxs.append(i)
    
    root_idxs = get_root_nodes(event_children, event_node_num)
    prim_child_idxs = expand_primitive_children(event_children) # expanding event children
    all_child_idxs = expand_all_children(event_children)
    # prim_child_idxs:= {event_idx: [list of the primitive event idxs acting as their children]}, keys include only non-primitive events, values only include primitive events.
    # all_child_idxs:= {event_idx: [list of the event idxs acting as their children]}, keys include only non-primitive events, values include all events (include the parent event itself).

    # Step 4: Read in the temporal relations and we want to get a global version of expanded temporal relations.
    global_temps = {}
    for relation in schema_dict["relations"]:
        if relation["relationSubject"] in event_node_idxs and relation["relationObject"] in event_node_idxs and relation["relationPredicate"] == "wd:Q79030196":
            start = event_node_idxs[relation["relationSubject"]]
            end = event_node_idxs[relation["relationObject"]]

            if start not in global_temps:
                global_temps[start] = [end]
            else:
                if end not in global_temps[start]:
                    global_temps[start].append(end)

    for event in schema_dict["events"]:
        event_id = event["@id"]
        if "children" in event:
            for child in event["children"]:
                if "outlinks" in child:
                    neighbors = child["outlinks"]
                    for neighbor in neighbors:
                        start = event_node_idxs[child["child"]]
                        end = event_node_idxs[neighbor]
                        if start not in global_temps:
                            global_temps[start] = [end]
                        else:
                            if end not in global_temps[start]:
                                global_temps[start].append(end)

        # the event event temporal relation could also exist in the outlinks
        if "outlinks" in event:
            for neighbor in event["outlinks"]:
                start = event_node_idxs[event_id]
                end = event_node_idxs[neighbor]
                if start not in global_temps:
                    global_temps[start] = [end]
                else:
                    if end not in global_temps[start]:
                        global_temps[start].append(end)
        
        # could also exist in relations (ISI Schema)
        if "relations" in event:
            for rel in event["relations"]:
                if rel["relationSubject"] in entity_node_idxs and rel["relationObject"] in entity_node_idxs:
                    start = entity_node_idxs[rel["relationSubject"]]
                    end = entity_node_idxs[rel["relationObject"]]
                    entity_graph.add_edge(start, end, type=rel["relationPredicate"])
                if rel["relationSubject"] in event_node_idxs and rel["relationObject"] in event_node_idxs:
                    start = event_node_idxs[rel["relationSubject"]]
                    end = event_node_idxs[rel["relationObject"]]
                    if start not in global_temps:
                        global_temps[start] = [end]
                    else:
                        if end not in global_temps[start]:
                            global_temps[start].append(end)
    
    # expanding global_temps
    expanded_global_temps = expand_temporal(global_temps, prim_child_idxs, primitive_idxs) # only contains primitive idxs

    schema_events = {}

    # even if we separate the graphs in to multiple sub-schemas, each schema event has its unique original id.
    for root_idx in root_idxs:
        # for each root idx, we want to output:
        # {"event_graph", "arg_dict", "arg_id_dict", "event_temps", "prim_child_idxs"}
        root_event_id = schema_dict["events"][root_idx]["@id"]
        subgraph_idxs = all_child_idxs[root_idx]
        prim_subgraph_idxs = prim_child_idxs[root_idx]

        # Step 5.1: generate subgraph prim child idxs
        sub_prim_child_idxs = {}
        for parent in prim_child_idxs:
            if parent in subgraph_idxs:
                sub_prim_child_idxs[parent] = prim_child_idxs[parent]

        # Step 5.2: read in event nx subgraph
        event_subgraph = nx.DiGraph()
        for i,idx in enumerate(subgraph_idxs):
            event_i = schema_dict["events"][idx]

            if "qlabel" in event_i:
                if type(event_i["qlabel"]) != list:
                    qlabels = [event_i["qlabel"]]
                    qnodes = [event_i["qnode"]]
                else:
                    qlabels = event_i["qlabel"]
                    qnodes = event_i["qnode"]
            else:
                qlabels = []
                qnodes = []
            if "ta1explanation" in event_i:
                ta1_exp = event_i["ta1explanation"]
            else:
                ta1_exp = ""

            if "children" in event_i and len(event_i["children"]) != 0:
                primitive = False
            else:
                primitive = True

            event_subgraph.add_node(i, id=event_i["@id"], idx=idx, qnodes=qnodes, qlabels=qlabels, name=event_i["name"], ta1exp=ta1_exp, primitive=primitive)
        
        # Step 5.3: generate expanded temps for each subgraph.
        subgraph_temps = {}
        for start in expanded_global_temps:
            if start in prim_subgraph_idxs:
                ends = expanded_global_temps[start]
                sub_ends = []
                for end in ends:
                    if end in prim_subgraph_idxs:
                        sub_ends.append(end)
                subgraph_temps[start] = sub_ends
        
        # Step 5.4: Read in event arguments.
        arg_name_dict, arg_id_dict = {}, {}
        for i,idx in enumerate(subgraph_idxs):
            event_i = schema_dict["events"][idx]
            if idx not in arg_name_dict:
                arg_name_dict.update({idx: {}})
                arg_id_dict.update({idx: {}})
            if "participants" in event_i:
                arguments = event_i["participants"]
                for arg in arguments:
                    role_type = arg["roleName"]
                    if arg["entity"] in entity_node_idxs:
                        entity_idx = entity_node_idxs[arg["entity"]]
                        arg_name_dict[idx].update({entity_idx: role_type})
                        arg_id_dict[idx].update({entity_idx: arg["@id"]})
        
        event_inf = {
            "nx_graph": event_subgraph,
            "temporal": subgraph_temps,
            "prim_child_idxs": prim_subgraph_idxs,
            "arg_dict": arg_name_dict,
            "arg_id_dict": arg_id_dict
        }
        
        schema_events.update({root_event_id: deepcopy(event_inf)})
    
    # Step 6: We still need a global event graph as backup.
    global_event_graph = nx.DiGraph()

    for i in range(event_node_num):
        event_i = schema_dict["events"][i]

        if "qlabel" in event_i:
            if type(event_i["qlabel"]) != list:
                qlabels = [event_i["qlabel"]]
                qnodes = [event_i["qnode"]]
            else:
                qlabels = event_i["qlabel"]
                qnodes = event_i["qnode"]
        else:
            qlabels = []
            qnodes = []
        if "ta1explanation" in event_i:
            ta1_exp = event_i["ta1explanation"]
        else:
            ta1_exp = ""

        if "children" in event_i and len(event_i["children"]) != 0:
            primitive = False
        else:
            primitive = True

        global_event_graph.add_node(i, id=event_i["@id"], idx=idx, qnodes=qnodes, qlabels=qlabels, name=event_i["name"], ta1exp=ta1_exp, primitive=primitive)

    return schema_events, event_node_idxs, entity_graph, entity_node_idxs, primitive_idxs, global_event_graph

    

if __name__ == "__main__":
    orgs = ["cmu", "ibm", "isi", "sbu", "resin"]

    for org in orgs:
        schema_file_dir = "./schemas_qz9/" + org + "-schemalib.json"
        print(schema_file_dir)
        read_schema(schema_file_dir)