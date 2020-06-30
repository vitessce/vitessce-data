import networkx

from constants import COLUMNS, CL_ROOT_ID
from utils import (
    load_cl_obo_graph,
    init_cell_sets_tree,
    dict_to_tree,
    sort_paths_up_cell_ontology
)


# Generate a tree of cell sets representing
# the clusters from the Leiden clustering
# algorithm.
def generate_leiden_cluster_cell_sets(df):
    tree = init_cell_sets_tree()

    leiden_clusters_children = []
    for cluster_name, cluster_df in df.groupby("leiden"):
        leiden_clusters_children.append({
            "name": cluster_name,
            "set": [
                [x, None]
                for x in cluster_df[COLUMNS.CELL_ID.value].unique().tolist()
            ],
        })

    tree["tree"].append({
        "name": "Leiden Clustering",
        "children": leiden_clusters_children
    })

    return tree


# Generate a tree of cell sets
# representing the cell type annotations,
# arranged on one level (not heirarchical).
def generate_cell_type_flat_cell_sets(df):
    tree = init_cell_sets_tree()

    cell_type_annotation_children = []
    for cell_type, cell_type_df in df.groupby(COLUMNS.ANNOTATION.value):
        set_cell_ids = cell_type_df[COLUMNS.CELL_ID.value].values.tolist()
        set_cell_scores = (
            cell_type_df[COLUMNS.PREDICTION_SCORE.value]
            .values.tolist()
        )
        set_value = [list(x) for x in zip(set_cell_ids, set_cell_scores)]

        cell_type_annotation_children.append({
            "name": cell_type,
            "set": set_value,
        })

    tree["tree"].append({
        "name": "Cell Type Annotations",
        "children": cell_type_annotation_children
    })
    return tree


# Generate a tree of cell sets
# for hierarchical cell type annotations.
def generate_cell_type_cell_sets(df, cl_obo_file):
    tree = init_cell_sets_tree()

    # Load the cell ontology DAG
    graph, id_to_name, name_to_id = load_cl_obo_graph(cl_obo_file)

    # Using the cell ontology DAG,
    # get all possible paths up to the root from
    # a given node_id value.
    def get_parents(node_id):
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
        node_parents = list(graph.out_edges(node_id, keys=True))

        up_dag_paths = []
        for node_parent in node_parents:
            _, curr_parent_id, relationship = node_parent
            if relationship == "is_a":
                parent_paths = get_parents(curr_parent_id)
                for parent_path in parent_paths:
                    up_dag_paths.append([node_id] + parent_path)
        return up_dag_paths

    ancestors_and_sets = []

    for cell_type, cell_type_df in df.groupby(COLUMNS.ANNOTATION.value):
        try:
            node_id = name_to_id[cell_type]
        except KeyError:
            print((
                f"ERROR: annotation '{cell_type}' does "
                "not match any node in the cell ontology."
            ))
            continue

        # Get all of the possible paths up to the root
        # from the current node.
        paths_up = get_parents(node_id)
        # Get the names of each node in each path.
        named_paths_up = [
            [id_to_name[n_id] for n_id in path_nodes]
            for path_nodes in paths_up
        ]
        print((
            f"WARNING: {id_to_name[node_id]} has {len(paths_up)} paths"
            f" up to {CL_ROOT_ID} ({id_to_name[CL_ROOT_ID]})."
        ))

        # Sort potential paths "up the hierarchy" by our preferences,
        # to avoid "functional" parent nodes like "motile cell"
        sorted_named_paths_up = sort_paths_up_cell_ontology(named_paths_up)

        named_ancestors = sorted_named_paths_up[0]
        named_ancestors_reversed = list(reversed(named_ancestors))
        # Get a list of (cell_id, prediction_score) tuples for the set.
        set_value = [
            list(x)
            for x in zip(
                cell_type_df[COLUMNS.CELL_ID.value].values.tolist(),
                cell_type_df[COLUMNS.PREDICTION_SCORE.value].values.tolist()
            )
        ]

        ancestors_and_sets.append((
            named_ancestors_reversed,
            set_value
        ))

    # Pop off all ancestors that are the same for all cell types.
    # e.g. 'cell', 'native cell', ...
    ancestor_list_lens = [len(x[0]) for x in ancestors_and_sets]
    min_ancestor_list_len = min(ancestor_list_lens)
    assert min_ancestor_list_len >= 1
    for level in range(min_ancestor_list_len - 1):
        unique_level_cell_types = set()
        for ancestors, cell_set in ancestors_and_sets:
            unique_level_cell_types.add(ancestors[0])

        if len(unique_level_cell_types) == 1:
            for ancestors, cell_set in ancestors_and_sets:
                ancestors.pop(0)
        else:
            break

    # Construct a hierarchy of cell types.
    def find_or_create_parent(d, keys, child):
        key = keys[0]

        if key in d and isinstance(d[key], dict):
            result = d[key]
        else:
            result = d[key] = dict()

        if len(keys) == 1:
            result["any"] = child
            return result
        else:
            new_keys = keys.copy()
            new_keys.pop(0)
            return find_or_create_parent(result, new_keys, child)

    h = dict()
    for ancestors, cell_set in ancestors_and_sets:
        find_or_create_parent(h, ancestors, cell_set)

    # Try removing the extra hierarchy level for the "any" set,
    # if it is an "only-child"
    def try_remove_any_level(v):
        if type(v) is dict:
            keys = list(v.keys())
            if len(keys) == 1 and keys[0] == "any":
                # Return the value associated with the "any" property,
                # since "any" has no siblings.
                return v["any"]
            else:
                # This is a dict with multiple values, so recursively
                # try this function on all of its values.
                return dict(
                    zip(
                        keys,
                        list(map(try_remove_any_level, v.values()))
                    )
                )
        else:
            # This is not a dict, so just return as-is.
            return v

    # Try removing all of the single-child "any" levels
    # now that the hierarchy has been created as a dict.
    h = try_remove_any_level(h)

    tree["tree"] = [
        dict_to_tree("Cell Type Annotations", h)
    ]
    return tree
