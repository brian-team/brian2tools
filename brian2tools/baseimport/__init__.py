"""
baseimport — reconstruct a Brian2 Network from a .brian archive.

    from brian2tools.baseimport import BrianImporter
    net, namespace = BrianImporter().load('snapshot.brian')
    net.run(10*ms)
"""

from .importer import BrianImporter

__all__ = ['BrianImporter']
