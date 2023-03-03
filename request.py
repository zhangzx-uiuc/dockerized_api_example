import requests
import json

if __name__ == "__main__":
    
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

    # sample task1 request: {"ce_id", "team", "entity.cs", "event.cs", "temporal.en", "temporal.es", "en.data", "es.data"}
    req = {
        "ce_id": "ce2004",
        "team": "resin",
        "entity.cs": entity_cs_string,
        "event.cs": event_cs_string,
        "temporal.en": temp_en_string,
        "temporal.es": temp_es_string,
        "en.data": en_data,
        "es.data": es_data
    }

    res = requests.post('http://127.0.0.1:2324/prediction/task1', json=req)
    with open("task1_server.json", 'w', encoding="utf-8") as f:
        f.write(json.dumps(json.loads(res.json()["sdf"]), indent=4))


    # sample task2 request: {"ce_id", "team", "graph_g"}
    with open("./task2_graphs_qz8/ce2002abridged_GraphG.json", 'r', encoding='utf-8') as f:
        ggraph = json.loads(f.read())
    
    graph_str = json.dumps(ggraph)
    
    req = {
        "ce_id": "ce2002abridged",
        "team": "cmu",
        "graph_g": graph_str
    }

    res = requests.post('http://127.0.0.1:2324/prediction/task2', json=req)
    with open("task2_server.json", 'w', encoding="utf-8") as f:
        f.write(json.dumps(json.loads(res.json()["sdf"]), indent=4))

