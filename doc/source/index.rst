Introduction
============

``psp-validation`` package is a tool for running pair neuron simulations and extracting postsynaptic potential (PSP) amplitudes from the resulting voltage traces.

It relies on `BluePy <https://bbpcode.epfl.ch/documentation/bluepy-0.11.9/>`_ for querying GID pairs from a circuit, and `BGLibPy <https://bbpcode.epfl.ch/documentation/BGLibPy-3.2>`_ for actually running pair simulations.

.. warning::

    | ``psp-validation`` package is considered to be work in progress and its interface, as well as file formats used might change until 1.0 release.
    | We apologize for possible inconvenience.

.. toctree::
   :maxdepth: 2

   install
   methodology
   tutorial
   files
   cookbook
   changelog


Acknowledgments
===============

``psp-validation`` is a refactored subset of ``ValidationFramework`` toolset originally developed by `Eilif Muller <mailto:eilif.mueller@epfl.ch>`_.


Reporting issues
================

``psp-validation`` is maintained by BlueBrain NSE team at the moment.

Should you face any issue with using it, please submit a ticket to our `issue tracker <https://bbpteam.epfl.ch/project/issues/browse/NSETM>`_; or drop us an `email <mailto: bbp-ou-nse@groupes.epfl.ch>`_.
