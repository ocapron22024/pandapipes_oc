# Copyright (c) 2020-2024 by Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel, and University of Kassel. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import networkx as nx
import pandas as pd
from pandapipes.topology.create_graph import create_nxgraph
from pandapipes.topology.topology_toolbox import get_all_branch_component_table_names


def calc_distance_to_junction(net, junction, notravjunctions=None, nogojunctions=None,
                              weight="weight"):
    """
    Calculates the shortest distance between a source junction and all junctions connected to it.

     INPUT:
        **net** (pandapipesNet) - Variable that contains a pandapipes network.

        **junction** (integer) - Index of the source junction.


     OPTIONAL:
        **nogojunctions** (integer/list, None) - nogojunctions are not being considered

        **notravjunctions** (integer/list, None) - lines connected to these junctions are not being
                                              considered
        **weight** (string, None) – Edge data key corresponding to the edge weight

     OUTPUT:
        **dist** - Returns a pandas series with containing all distances to the source junction
                   in km. If weight=None dist is the topological distance (int).

     EXAMPLE:
         import pandapipes.topology as top

         dist = top.calc_distance_to_junction(net, 5)

    """
    g = create_nxgraph(net, nogojunctions=nogojunctions,
                       notravjunctions=notravjunctions)
    dist = nx.single_source_dijkstra_path_length(g, junction, weight=weight)
    return pd.Series(dist)


def calc_minimum_distance_to_junctions(net, junctions, notravjunctions=None, nogojunctions=None,
                                       weight="weight"):
    """
    Calculates the shortest distance between multiple source junctions and all junctions connected \
    to it.

     INPUT:
        **net** (pandapipesNet) - Variable that contains a pandapipes network.

        **junction** (integer) - Index of the source junction.


     OPTIONAL:
        **nogojunctions** (integer/list, None) - nogojunctions are not being considered

        **notravjunctions** (integer/list, None) - lines connected to these junctions are not being
                                              considered
        **weight** (string, None) – Edge data key corresponding to the edge weight

     OUTPUT:
        **dist** - Returns a pandas series with containing all distances to the source junction
                   in km. If weight=None dist is the topological distance (int).

     EXAMPLE:
         import pandapipes.topology as top

         dist = top.calc_distance_to_junction(net, 5)

    """
    mg = create_nxgraph(net, notravjunctions=notravjunctions,
                        nogojunctions=nogojunctions, weight=weight)
    junctions = set(junctions)
    junction = junctions.pop()
    mg.add_edges_from([(junction, y, {"weight": 0}) for y in junctions])
    return pd.Series(nx.single_source_dijkstra_path_length(mg, junction))


def unsupplied_junctions(net, mg=None, slacks=None, respect_valves=True):
    """
     Finds junctions, that are not connected to an external grid.

     INPUT:
        **net** (pandapipesNet) - variable that contains a pandapipes network

     OPTIONAL:
        **mg** (NetworkX graph) - NetworkX Graph or MultiGraph that represents a pandapipes network.

        **in_service_only** (boolean, False) - Defines whether only in service junctions should be
            included in unsupplied_junctions.

        **slacks** (set, None) - junctions which are considered as root / slack junctions. If None, all
            existing slack junctions are considered.

        **respect_valves** (boolean, True) - Fixes how to consider valves - only in case of no
            given mg.

     OUTPUT:
        **uj** (set) - unsupplied junctions

     EXAMPLE:
         import pandapipes.topology as top

         top.unsupplied_junctions(net)
    """

    mg = mg or create_nxgraph(net, respect_status_valves=respect_valves)
    if slacks is None:
        slacks = set(net.ext_grid[net.ext_grid.in_service].junction.values)
    not_supplied = set()
    for cc in nx.connected_components(mg):
        if not set(cc) & slacks:
            not_supplied.update(set(cc))
    return not_supplied


def elements_on_path(mg, path, element="pipe"):
    """
     Finds all elements that connect a given path of junctions.

     INPUT:
        **mg** (NetworkX graph) - NetworkX Graph or MultiGraph that represents a pandapipes network.

        **path** (list) - List of connected junctions.

        **element** (string, "l") - element type of type BranchComponent

        **multi** (boolean, True) - True: Applied on a NetworkX MultiGraph
                                    False: Applied on a NetworkX Graph

     OUTPUT:
        **elements** (list) - Returns a list of all elements on the path.

     EXAMPLE:
         import topology as top

         mg = top.create_nxgraph(net)
         elements = top.elements_on_path(mg, [4, 5, 6])

     """
    table_names = get_all_branch_component_table_names()
    if element not in table_names:
        raise ValueError("Invalid element type %s" % element)
    if isinstance(mg, nx.MultiGraph):
        return [edge[1] for b1, b2 in zip(path, path[1:]) for edge in mg.get_edge_data(b1, b2).keys()
                if edge[0] == element]
    else:
        return [mg.get_edge_data(b1, b2)["key"][1] for b1, b2 in zip(path, path[1:])
                if mg.get_edge_data(b1, b2)["key"][0] == element]


if __name__ == '__main__':
    import pandapipes.networks as nw
    net = nw.gas_meshed_delta()
    dist = calc_minimum_distance_to_junctions(net, net.ext_grid.junction.values)
