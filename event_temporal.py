

def add_parents_temporal(temp_dict, event_children, prim_idxs):
    # function: add back the temporal links caused by event parents

    # temp_dict: {event_idx: [list of event idxs happen after event_idx]} 
    # event_children: {event_idx: [list of all primitive idxs]} # keys only include non-primitive events, values only include primitive events.
    # prim_idxs: [a list of primitive event idxs]
    # OUTPUT: a dict that only contains event temporal relations among primitive events

    # Initialize: each prim event should be in the dict
    result_temp_dict = {}
    for idx in prim_idxs:
        result_temp_dict.update({idx: []}) 

    for start_idx in temp_dict:
        if start_idx in result_temp_dict:
            end_idxs = temp_dict[start_idx]
            for end_idx in end_idxs:
                if end_idx in result_temp_dict:
                    # prim -> prim
                    if end_idx not in result_temp_dict[start_idx]:
                        result_temp_dict[start_idx].append(end_idx)
                else:
                    # prim -> nonprim
                    end_children = event_children[end_idx]
                    for child in end_children:
                        if child not in result_temp_dict[start_idx]:
                            result_temp_dict[start_idx].append(child)
        else:
            children = event_children[start_idx]
            end_idxs = temp_dict[start_idx]
            for end_idx in end_idxs:
                if end_idx in result_temp_dict:
                    # nonprim -> prim
                    for child in children:
                        if end_idx not in result_temp_dict[child]:
                            result_temp_dict[child].append(end_idx)
                else:
                    # nonprim -> nonprim
                    end_children = event_children[end_idx]
                    for child_x in children:
                        for child_y in end_children:
                            if child_y not in result_temp_dict[child_x]:
                                result_temp_dict[child_x].append(child_y)
    
    return result_temp_dict


def expand_temporal(temp_dict, event_children, prim_idxs):
    # expand temporal to the largest: includes all possible temporal edges (not only neighbors) as long as it is correct.
    prim_temp_dict = add_parents_temporal(temp_dict, event_children, prim_idxs)
    # print("ADD")
    # prim_temp_dict = {1:[2,3,6], 2:[4,5,6], 3:[5,6], 4:[], 5:[6], 6:[]}

    # conduct a BFS for each node
    expanded_dict = {}
    for idx in prim_temp_dict:
        expanded_dict.update({idx: []})

    for idx in prim_temp_dict:
        # print(idx)
        # print(prim_temp_dict)
        queue = []
        queue.extend(prim_temp_dict[idx])
        hashset = set()
        while len(queue) != 0:
            # print(len(queue))
            first_idx = queue.pop(0)
            # print(first_idx)
            children = prim_temp_dict[first_idx]
            if first_idx not in hashset:
                queue.extend(children)
                hashset.add(first_idx)
                expanded_dict[idx].append(first_idx)
    # print(expanded_dict)
    return expanded_dict


def expand_ids_temporal(temp_dict):
    expanded_dict = {}
    for idx in temp_dict:
        expanded_dict.update({idx: []})
    
    for idx in temp_dict:
        # print(idx)
        # print(prim_temp_dict)
        queue = []
        queue.extend(temp_dict[idx])
        hashset = set()
        while len(queue) != 0:
            # print(len(queue))
            first_idx = queue.pop(0)
            # print(first_idx)
            children = temp_dict[first_idx]
            if first_idx not in hashset:
                queue.extend(children)
                hashset.add(first_idx)
                expanded_dict[idx].append(first_idx)
    
    return expanded_dict



def reduce_temporal(temp_dict, event_children, prim_idxs):
    # reduce the temporal links to the simplest: only includes event-event neighbors.
    expanded_dict = expand_temporal(temp_dict, event_children, prim_idxs)
    # expanded_dict = {1:[2,3,4,5,6], 2:[4,5,6], 3:[5,6], 4:[], 5:[6], 6:[]}

    reduced_dict = {}
    for idx in expanded_dict:
        reduced_dict.update({idx: []})
    
    for idx in expanded_dict:
        targets = expanded_dict[idx]
        for target in targets:
            exist = False
            for mid_idx in targets:
                mid_children = expanded_dict[mid_idx]
                if target in mid_children:
                    exist = True
        
            if not exist:
                reduced_dict[idx].append(target)
    # print(reduced_dict)
    return reduced_dict


def linearize_graph(expanded_dict, prim_ids):
    # Use bubble sort to linearize a graph according to the expanded dict.
    init_list = prim_ids.copy()
    init_len = len(init_list)
    
    for i in range(init_len-1):
        for j in range(0, init_len-1-i):
            if init_list[j] in expanded_dict[init_list[j+1]]:
                temp = init_list[j]
                init_list[j] = init_list[j+1]
                init_list[j+1] = temp 
    
    return init_list



if __name__ == "__main__":
    reduce_temporal([], [], [])
    expand_temporal([], [], [])

                

