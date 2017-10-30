"""module for protocol handling
"""


class Protocol(object):
    """Class holding protocol parameters
    """
    def __init__(self,
                 holding_I, holding_V,
                 t_stim, t_stop,
                 g_factor, record_dt,
                 post_ttx,
                 clamp_V):

        for key, val in locals().iteritems():
            if not key == 'self':
                setattr(self, key, val)

    def __eq__(self, rhs):
        attrs = self.__dict__.keys()
        for attr in attrs:
            if self.__getattribute__(attr) != rhs.__getattribute__(attr):
                return False
        return True

    def __ne__(self, rhs):
        return not self.__eq__(rhs)
