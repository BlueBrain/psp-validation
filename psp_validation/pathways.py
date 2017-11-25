"""Repository for pathway queries
"""
import itertools

from bluepy.v2.enums import Cell

from psp_validation import PSPError


class ConnectionFilter(object):
    """
    Filter (pre_gid, post_gid, [nsyn]) tuples by different criteria.

    Args:
        circuit: bluepy.v2.Circuit instance

        unique_gids: use GIDs only once
        min_nsyn: min synapse count for connection
        max_dist_x: max distance along X axis between pre- and post- synaptic soma
        max_dist_y: max distance along Y axis between pre- and post- synaptic soma
        max_dist_z: max distance along Z axis between pre- and post- synaptic soma

    NB:
        * using `unique_gids` makes ConnectionFilter stateful
        * using `min_syn` requires (pre_gid, post_gid, nsyn) input tuples
    """
    def __init__(
        self, circuit, unique_gids=False, min_nsyn=None,
        max_dist_x=None, max_dist_y=None, max_dist_z=None
    ):
        self.circuit = circuit
        self.min_nsyn = min_nsyn
        self.max_dist_x = max_dist_x
        self.max_dist_y = max_dist_y
        self.max_dist_z = max_dist_z
        if unique_gids:
            self.used_gids = set()
        else:
            self.used_gids = None

    def __call__(self, conn):
        pre_gid, post_gid = conn[:2]
        if self.used_gids is not None:
            if (pre_gid in self.used_gids) or (post_gid in self.used_gids):
                return False
        if self.min_nsyn is not None:
            if conn[2] < self.min_nsyn:
                return False
        if self.max_dist_x is not None:
            x1, x2 = self.circuit.cells.get([pre_gid, post_gid])[Cell.X]
            if abs(x1 - x2) > self.max_dist_x:
                return False
        if self.max_dist_y is not None:
            y1, y2 = self.circuit.cells.get([pre_gid, post_gid])[Cell.Y]
            if abs(y1 - y2) > self.max_dist_y:
                return False
        if self.max_dist_z is not None:
            z1, z2 = self.circuit.cells.get([pre_gid, post_gid])[Cell.Z]
            if abs(z1 - z2) > self.max_dist_z:
                return False
        if self.used_gids is not None:
            self.used_gids.add(pre_gid)
            self.used_gids.add(post_gid)
        return True


def get_pairs(circuit, pre, post, n_pairs, constraints=None, projection=None):
    """
    Get 'n_pairs' connected pairs specified by `query` and optional `constraints`.

    Args:
        circuit: bluepy.v2.Circuit instance
        pre: presynaptic cell group (BluePy.v2 query)
        post: postsynaptic cell group (BluePy.v2 query)
        n_pairs: number of pairs to return
        constraints: dict passed as kwargs to `ConnectionFilter`
        projection: projection name (None for main connectome)

    Returns:
        List of `n` (pre_gid, post_gid) pairs (or fewer if could not find enough)
    """
    if projection is None:
        connectome = circuit.connectome
    else:
        connectome = circuit.projection(projection)
    iter_connections = connectome.iter_connections(pre=pre, post=post, shuffle=True)
    if constraints is not None:
        iter_connections = itertools.ifilter(
            ConnectionFilter(circuit, **constraints),
            iter_connections
        )
    return [conn[:2] for conn in itertools.islice(iter_connections, n_pairs)]


def get_synapse_type(circuit, cell_group):
    """
    Get synapse type for `cell_group` cells.

    Raise an Exception if there are cells of more than one synapse type.
    """
    syn_types = circuit.cells.get(cell_group, Cell.SYNAPSE_CLASS).unique()
    if len(syn_types) != 1:
        raise PSPError(
            "Cell group should consist of cells with same synapse type, found: [{}]".format(
                ",".join(syn_types)
            )
        )
    return syn_types[0]
