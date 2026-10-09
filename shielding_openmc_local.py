#!/usr/bin/env python3
"""Compatibility entry point for the configuration-driven OpenMC runner.

Example:
  python shielding_openmc_local.py --profile smoke --cross-sections endfb-viii.1-hdf5/cross_sections.xml
The pre-replacement script is preserved at data/development/legacy_runner.py.
"""
from scripts.run_matrix import main
if __name__=='__main__': main()
