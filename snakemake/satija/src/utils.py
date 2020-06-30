import networkx
import obonet

from constants import CL_ROOT_ID


def load_cl_obo_graph(cl_obo_file):
    graph = obonet.read_obo(cl_obo_file)

    # Make sure there are no cycles.
    assert networkx.is_directed_acyclic_graph(graph)

    id_to_name = {
        id_: data.get('name')
        for id_, data in graph.nodes(data=True)
    }
    name_to_id = {
        data['name']: id_
        for id_, data in graph.nodes(data=True) if 'name' in data
    }

    return graph, id_to_name, name_to_id


# Construct the tree, according to the following schema:
# https://github.com/hubmapconsortium/vitessce/blob/d5f63aa1d08aa61f6b20f6ad6bbfba5fceb6b5ef/src/schemas/cell_sets.schema.json
def init_cell_sets_tree():
    return {
        "datatype": "cell",
        "version": "0.1.3",
        "tree": []
    }


# Merge multiple cell sets trees.
def merge_cell_sets_trees(*args):
    assert len(args) > 1

    result = args[0]
    for arg in args[1:]:
        for level_zero_node in arg["tree"]:
            result["tree"].append(level_zero_node)
    return result


# Recursively convert a nested dict to the tree schema.
def dict_to_tree(name, value):
    if isinstance(value, dict):
        return {
            "name": name,
            "children": [
                dict_to_tree(child_name, child_value)
                for child_name, child_value in value.items()
            ]
        }
    else:
        return {
            "name": name,
            "set": value,
        }


# Given a list of multiple paths up the DAG,
# sort the list according to a heuristic.
def sort_paths_up_cell_ontology(paths_up):
    PREFERENCES = [
        ['animal cell', 'eukaryotic cell', 'native cell', 'cell'],
        ['somatic cell', 'native cell', 'cell'],
        ['nucleate cell', 'native cell', 'cell'],
        ['precursor cell', 'native cell', 'cell'],
    ]
    # Prefer all of the above before "functional" categories like
    # [..., 'motile cell', 'native cell', 'cell']
    WORST_PREFERENCE_INDEX = len(PREFERENCES)

    def get_first_preference_index_and_path_length(path_up):
        path_preference_match_index = WORST_PREFERENCE_INDEX
        for preference_index, preference in enumerate(PREFERENCES):
            if path_up[-len(preference):] == preference:
                path_preference_match_index = preference_index
                break
        # Return a tuple of the first matching preference "path ending"
        # and the path length (to use shorter paths if multiple paths
        # match the same top path ending).
        return (path_preference_match_index, len(path_up))
    return sorted(paths_up, key=get_first_preference_index_and_path_length)


# Using the cell ontology DAG,
# get all possible paths up to the root from
# a given node_id value.
def get_paths_up_cell_ontology(graph, node_id):
    if node_id == CL_ROOT_ID:
        return [
            [node_id]
        ]

    # Get ancestors of the cell type
    # (counterintuitive that the function is called descendants).
    ancestor_term_set = networkx.descendants(graph, node_id)

    # Make sure the cell type has an ancestor
    # with the 'cell' root ID.
    assert CL_ROOT_ID in ancestor_term_set

    # Get the parents of the current node.
    node_parents = graph.out_edges(node_id, keys=True)

    up_dag_paths = []
    for node_parent in node_parents:
        _, curr_parent_id, relationship = node_parent
        if relationship == "is_a":
            parent_paths = get_paths_up_cell_ontology(graph, curr_parent_id)
            for parent_path in parent_paths:
                up_dag_paths.append([node_id] + parent_path)
    return up_dag_paths
