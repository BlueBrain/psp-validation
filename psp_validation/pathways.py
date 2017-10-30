"""Repository for pathway queries
"""


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
