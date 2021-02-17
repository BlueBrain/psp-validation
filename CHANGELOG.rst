Changelog
=========

Version 0.4.0
-------------

- Update bluepy dependency to 2.1.0.
- Update bglibpy dependency to 4.4.27.
- Fix growing memory issues [NSETM-1356].

Version 0.3.3
-------------

- Add a configuration parameter `min_trace_amplitude` to
  filter out synaptic failures before calculating mean PSPs [NSETM-1166].

Version 0.3.1
-------------

- Update bglibpy dependency to 4.3.15.

Version 0.3.0
-------------

- Changed `projection` argument of `simulation.run_pair_simulation` to `add_projections`. Now it
  is not possible to specify the exact projection to simulate. All projections get simulated.
  You still can specify which projection to query in `pathways.Pathway`. Nothing changed there.

Version 0.2.2
-------------

- Changed the simulation run. Now it always with forward_skip=False. Even if the config file
  was specifying ForwardSkip == True. In this case, omit a warning to warn the user.
- Removed python2 support
- Fix errors of config loading, docs building.
