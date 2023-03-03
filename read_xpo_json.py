import json

def read_xpo(xpo_json_dir):
    with open(xpo_json_dir, 'r', encoding="utf-8") as f:
        xpo_json = json.loads(f.read())
    
    event_type_mapping, role_type_mapping = {}, {}
    # event_type_mapping = {ldc_type: [(qnode, qlabel), (qnode, qlabel)]}
    # role_type_mapping = {ldc_type + role_name: [full xpo role names]}
    
    for qnode, event in xpo_json["events"].items():
        if "ldc_types" in event:
            qnode_str = qnode.split('_')[1]
            qlabel = event["name"]
            # print(event["ldc_types"])
            ldc_types = event["ldc_types"]
            # print(len(ldc_types))
            for ldc_type in ldc_types:
                ldc_type_name = ldc_type["name"].lower()
                if ldc_type_name not in event_type_mapping:
                    event_type_mapping[ldc_type_name] = [(qnode_str, qlabel)]
                else:
                    event_type_mapping[ldc_type_name].append((qnode_str, qlabel))

                if "ldc_arguments" in ldc_type:
                    arguments = ldc_type["ldc_arguments"]
                    for argument in arguments:
                        total_role_name = (ldc_type_name + '_' + argument["ldc_name"]).lower()
                        dwd_arg_name = argument["dwd_arg_name"]
                        if total_role_name not in role_type_mapping:
                            role_type_mapping[total_role_name] = [dwd_arg_name]
                        else:
                            role_type_mapping[total_role_name].append(dwd_arg_name)


    with open("event_map.json", 'w', encoding="utf-8") as f1:
        f1.write(json.dumps(event_type_mapping, indent=4))
    with open("role_map.json", 'w', encoding="utf-8") as f2:
        f2.write(json.dumps(role_type_mapping, indent=4))
    
    return event_type_mapping, role_type_mapping      



if __name__ == "__main__":
    xpo_input_dir = "./xpo_v3.2_freeze_exp.json"

    # with open(xpo_input_dir, 'r', encoding='utf-8') as f:
    #     xpo_dict = json.loads(f.read())
    
    # print(xpo_dict.keys())
    read_xpo(xpo_input_dir)
