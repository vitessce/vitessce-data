import networkx
import obonet

def load_cl_obo_graph(cl_obo_file):
    graph = obonet.read_obo(cl_obo_file)
    
    # make sure there are no cycles
    assert(networkx.is_directed_acyclic_graph(graph))

    id_to_name = {id_: data.get('name') for id_, data in graph.nodes(data=True)}
    name_to_id = {data['name']: id_ for id_, data in graph.nodes(data=True) if 'name' in data}

    return graph, id_to_name, name_to_id

def init_tree():
    return {
        "datatype": "cell",
        "version": "0.1.2",
        "tree": [
            
        ]
    }