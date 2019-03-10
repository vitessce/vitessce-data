from scipy.cluster.hierarchy import leaves_list, linkage
import pandas as pd

# I found this tutorial very helpful:
# https://joernhees.de/blog/2015/08/26/scipy-hierarchical-clustering-and-dendrogram-tutorial/


def _order_rows(dataframe):
    '''
    >>> df = pd.DataFrame({
    ...   'cell-1': {'a':8, 'b':1, 'c': 7, 'd': 2},
    ...   'cell-2': {'a':1, 'b':1, 'c': 1, 'd': 1},
    ...   'cell-3': {'a':9, 'b':1, 'c': 8, 'd': 2},
    ...   'cell-4': {'a':1, 'b':2, 'c': 1, 'd': 1}
    ... })
    >>> _order_rows(df)
    ['a', 'c', 'b', 'd']

    '''
    row_labels = dataframe.index.tolist()
    if len(row_labels) > 1:
        rows_linkage = linkage(dataframe, 'ward')
        rows_order = leaves_list(rows_linkage).tolist()
        return [row_labels[i] for i in rows_order]
    else:
        return row_labels


def _order(dataframe):
    '''
    >>> df = pd.DataFrame({
    ...   'cell-1': {'a':8, 'b':1, 'c': 7},
    ...   'cell-2': {'a':1, 'b':1, 'c': 1},
    ...   'cell-3': {'a':9, 'b':1, 'c': 8}
    ... })
    >>> _order(df)['rows']
    ['b', 'a', 'c']
    >>> _order(df)['cols']
    ['cell-2', 'cell-1', 'cell-3']

    '''
    col_label_order = _order_rows(dataframe.T)
    row_label_order = _order_rows(dataframe)
    return {'rows': row_label_order, 'cols': col_label_order}


def _to_dataframe(cells):
    '''
    >>> cells = {
    ...   'cell-1': { 'genes': {'a':8, 'b':1, 'c': 7}, 'extra': 'field'},
    ...   'cell-2': { 'genes': {'a':1, 'b':1, 'c': 1}, 'extra': 'field'},
    ...   'cell-3': { 'genes': {'a':9, 'b':1, 'c': 8}, 'extra': 'field'}
    ... }
    >>> _to_dataframe(cells)
       cell-1  cell-2  cell-3
    a       8       1       9
    b       1       1       1
    c       7       1       8

    '''
    clean = {}
    for k, v in cells.items():
        clean[k] = v['genes']
    return pd.DataFrame(clean)


def cluster(cells):
    '''
    >>> cells = {
    ...   'cell-1': { 'genes': {'a':8, 'b':1, 'c': 7}, 'extra': 'field'},
    ...   'cell-2': { 'genes': {'a':1, 'b':1, 'c': 1}, 'extra': 'field'},
    ...   'cell-3': { 'genes': {'a':9, 'b':1, 'c': 8}, 'extra': 'field'}
    ... }
    >>> clustered = cluster(cells)
    >>> clustered['rows']
    ['b', 'a', 'c']
    >>> clustered['cols']
    ['cell-2', 'cell-1', 'cell-3']
    >>> clustered['matrix']
    [[1, 1, 1], [1, 8, 9], [1, 7, 8]]

    '''
    df = _to_dataframe(cells)
    rows_cols = _order(df)
    clustered = df[rows_cols['cols']].loc[rows_cols['rows']]
    return {
        'rows': rows_cols['rows'],
        'cols': rows_cols['cols'],
        'matrix': clustered.values.tolist()
    }
