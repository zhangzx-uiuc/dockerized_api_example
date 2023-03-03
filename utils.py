import re
import networkx as nx


def expand_children(event_children):
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
                

def extract_headword(input_string):
    # we extract the first token of the input string as the head word.
    # the strings are splitted by - and space.
    input_splits = re.split(' |_|-', input_string)
    output_string = input_splits[0]
    return output_string

def extract_headwords(input_strings):
    outputs = []
    for string in input_strings:
        outputs.append(extract_headword(string))
    return string

def read_role_name(input_role_string):
    # acquire a role_position and role_name_string
    return

def cal_temp_num(temp_dict):
    temp_num = 0
    for key in temp_dict:
        temp_num += (len(temp_dict[key]))
    return temp_num


def print_networkx_graph(graph):
    print('='*20)
    for node in graph.nodes(data=True):
        print(node)
    print('-'*20)
    for edge in graph.edges(data=True):
        print(edge)
    print(len(graph.edges))

def print_graphs(event_graph, event_node_idx, entity_graph, entity_node_idx, arg_dict):
    print('='*20)
    for node in event_graph.nodes(data=True):
        print(node)
    print('-'*20)
    for edge in event_graph.edges(data=True):
        print(edge)
    print(len(event_graph.edges))

    print('='*20)
    for node in entity_graph.nodes(data=True):
        print(node)
    print('-'*20)
    for edge in entity_graph.edges(data=True):
        print(edge)
    print(len(entity_graph.edges))
    # print(arg_dict)


if __name__ == "__main__":
    e = {1:[2,3], 2:[4,5,6], 3:[6,7], 6:[8,9]}
    f = expand_children(e)
    print(f)
