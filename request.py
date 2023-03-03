import requests
import json

if __name__ == "__main__":
    
    # sample task2 request: {"ce_id", "team", "graph_g"}
    with open("ce2002abridged_GraphG.json", 'r', encoding='utf-8') as f:
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

