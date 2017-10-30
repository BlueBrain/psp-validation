"""Module for experimental data-related types
"""


class Stats(object):
    """Class holding distribution summary statistics
    """
    def __init__(self, mean, sigma):
        self.mean = mean
        self.sigma = sigma

    def __eq__(self, rhs):
        attrs = self.__dict__.keys()
        for attr in attrs:
            if self.__getattribute__(attr) != rhs.__getattribute__(attr):
                return False
        return True

    def __ne__(self, rhs):
        return not self.__eq__(rhs)


class Results(object):
    """Place-holder for experimental results
    """
    def __init__(self,
                 amplitude_stats,
                 synapses_per_connection_stats):

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


class Paper(object):
    """Class with paper summary information

    """
    def __init__(self, title, results):
        self.title = title
        self.results = dict(results)

    def get_result(self, pathway):
        """Get the results for a pathway

        Parameters:
        pathway: name of the pathway
        return:  Results object containing summary statistics
        """
        return self.results[pathway]

    def get_pathways(self):
        """Return the list of pathways used in this paper
        """
        return self.results.keys()

    def __eq__(self, rhs):
        attrs = self.__dict__.keys()
        for attr in attrs:
            if self.__getattribute__(attr) != rhs.__getattribute__(attr):
                return False
        return True

    def __ne__(self, rhs):
        return not self.__eq__(rhs)
