"""Repository for pathway queries
"""
import itertools

from bluepy.v2.enums import Cell


class Pathway(object):
    """Class wolding the queries necessary to obtain pre- and \
            post-synaptic cells
    """
    def __init__(self, presynaptic_cell_query, postsynaptic_cell_query):
        self.presynaptic_cell_query = presynaptic_cell_query
        self.postsynaptic_cell_query = postsynaptic_cell_query

    def __eq__(self, rhs):
        attrs = self.__dict__.keys()
        for attr in attrs:
            if self.__getattribute__(attr) != rhs.__getattribute__(attr):
                return False
        return True

    def __ne__(self, rhs):
        return not self.__eq__(rhs)


# Neuron group expressions

# General
EXC = 'MType.synapse_class=="EXC"'
INH = 'MType.synapse_class=="INH"'
MC = 'MType.name.like("L%_MC")'

#Distal Targeting INH
DISTAR_INH = 'Or(MType.name.like("L%_MC"), MType.name.like("L%_BTC"), MType.name.like("L%_DBC"), MType.name.like("L%_BP"))'
BC = 'Or(MType.name.like("L%_NBC"), MType.name.like("L%_LBC"), MType.name.like("L%_SBC"))'
PV_FS = 'Or(MType.name.like("L%_NBC"), MType.name.like("L%_LBC"), MType.name.like("L%_SBC"), MType.name.like("L%_ChC"))'

INH_OTHER = 'And(MType.synapse_class=="INH", Not(%s), Not(%s))' % (PV_FS, DISTAR_INH)


# Specific
L5_TTPC = 'Or(MType.name=="L5_TTPC1", MType.name=="L5_TTPC2")'
L5_STPC = 'MType.name=="L5_STPC"'
L5_MC = 'MType.name=="L5_MC"'
L5_BC = 'Or(MType.name=="L5_SBC", MType.name=="L5_LBC", MType.name=="L5_NBC")'
L5_PC = 'And(MType.morph_class=="PYR", Neuron.layer==5)'

L2_PC = 'And(MType.name=="L23_PC", Neuron.layer==2)'
L2_BTC = 'And(MType.name=="L23_BTC", Neuron.layer==2)'
L3_PC = 'And(MType.name=="L23_PC", Neuron.layer==3)'
L23_PC = 'MType.name=="L23_PC"'
L23_LBC = 'MType.name=="L23_LBC"'
L23_NBC = 'MType.name=="L23_NBC"'
L23_BC = 'Or(MType.name=="L23_SBC", MType.name=="L23_LBC", MType.name=="L23_NBC")'
L23_NBC_LBC = 'Or(MType.name=="L23_LBC", MType.name=="L23_NBC")'
L23_MC = 'MType.name=="L23_MC"'
L23_BTC = 'MType.name=="L23_BTC"'
L23_DBC = 'MType.name=="L23_DBC"'
L23_BP = 'MType.name=="L23_BP"'
L23_NGC = 'MType.name=="L23_NGC"'
L23_SBC = 'MType.name=="L23_SBC"'
L23_ChC = 'MType.name=="L23_ChC"'

L4_EXC = 'And(MType.synapse_class=="EXC", Neuron.layer==4)'
L4_SS = 'MType.name=="L4_SS"'

L6_TPC_L1 = 'MType.name=="L6_TPC_L1"'

exc_exc_pathways = {
        'L5_TTPC-L5_TTPC' : Pathway(L5_TTPC, L5_TTPC),
        'L4_EXC-L4_EXC'   : Pathway(L4_EXC, L4_EXC),
        'L4_SS-L23_PC'    : Pathway(L4_SS, L23_PC),
        'L5_STPC-L5_STPC' : Pathway(L5_STPC, L5_STPC),
        'L23_PC-L23_PC'   : Pathway(L23_PC, L23_PC),
        'L4_SS-L5_TTPC'   : Pathway(L4_SS, L5_TTPC)
        }

exc_inh_pathways = {
        'L5_TTPC-L5_MC'  : Pathway(L5_TTPC, L5_MC),
        'L5_PC-L5_BC'    : Pathway(L5_PC, L5_BC),
        'L4_EXC-L23_LBC' : Pathway(L4_EXC, L23_LBC),
        'L4_EXC-L23_NBC' : Pathway(L4_EXC, L23_NBC),
        'L4_EXC-L23_MC'  : Pathway(L4_EXC, L23_MC)
        }

inh_exc_pathways = {
        'L5_MC-L5_TTPC'      : Pathway(L5_MC, L5_TTPC),
        'L23_LBC-L23_PC'     : Pathway(L23_LBC, L23_PC),
        'L23_NBC-L23_PC'     : Pathway(L23_NBC, L23_PC),
        'L23_BC-L23_PC'      : Pathway(L23_BC, L23_PC),
        'L23_NBC_LBC-L23_PC' : Pathway(L23_NBC_LBC, L23_PC)
        }

# secondary pathways

exc_exc_secondary_pathways = {
        'L6_TPC_L1-L6_TPC_L1' : Pathway(L6_TPC_L1, L6_TPC_L1)
        }


# Predictions

# lumped pathway # PSP data here are unknown
inh_to_all_lumped_pathways = {
        'BC-EXC'         : Pathway(BC, EXC),
        'PV_FS-EXC'      : Pathway(PV_FS, EXC),
        'MC-EXC'         : Pathway(MC, EXC),
        'DISTAR_INH-EXC' : Pathway(DISTAR_INH, EXC)
        }

# "DISTAR_INH-EXC", "BC-EXC", "PV_FS-EXC", "MC-EXC"

exc_to_all_lumped_pathways = {
        'EXC-BC'        : Pathway(EXC, BC),
        'EXC-PV_FS'     : Pathway(EXC, PV_FS),
        'EXC-MC'        : Pathway(EXC, MC),
        'EXC-INH_OTHER' : Pathway(EXC, INH_OTHER)
        }

# "EXC-BC", "EXC-PV_FS", "EXC-MC", "EXC-INH_OTHER"


_pathways = dict()
_pathways.update(exc_exc_pathways)
_pathways.update(exc_inh_pathways)
_pathways.update(inh_exc_pathways)
_pathways.update(inh_to_all_lumped_pathways)
_pathways.update(exc_to_all_lumped_pathways)
_pathways.update(exc_exc_secondary_pathways)


def get_pathway(label) :
    """Return a pathway for a given label
    """
    return _pathways[label]


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
    def __init__(self, circuit, unique_gids=False, min_nsyn=None, max_dist_x=None, max_dist_y=None, max_dist_z=None):
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
            x1, x2 = self.circuit.cells([pre_gid, post_gid])[Cell.X]
            if abs(x1 - x2) > self.max_dist_x:
                return False
        if self.max_dist_y is not None:
            y1, y2 = self.circuit.cells([pre_gid, post_gid])[Cell.Y]
            if abs(y1 - y2) > self.max_dist_y:
                return False
        if self.max_dist_z is not None:
            z1, z2 = self.circuit.cells([pre_gid, post_gid])[Cell.Z]
            if abs(z1 - z2) > self.max_dist_z:
                return False
        if self.used_gids is not None:
            self.used_gids.add(pre_gid)
            self.used_gids.add(post_gid)
        return True


def get_pairs(circuit, n_pairs, query, constraints=None):
    """
    Get 'n_pairs' connected pairs specified by `query` and optional `constraints`.

    Args:
        circuit: bluepy.v2.Circuit instance
        n_pairs: number of pairs to return
        query: dict passed as kwargs to `circuit.connectome.iter_connections()`
        constraints: dict passed as kwargs to `ConnectionFilter`

    Returns:
        List of `n` (pre_gid, post_gid) pairs (or fewer if could not find enough)
    """
    iter_connections = circuit.connectome.iter_pathway_pairs(**query)
    if constraints is not None:
        iter_connections = itertools.ifilter(
            ConnectionFilter(circuit, **constraints),
            iter_connections
        )
    return [conn[:2] for conn in itertools.islice(iter_connections, n_pairs)]