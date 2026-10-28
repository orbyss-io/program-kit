"""Retired paid-bootstrap restore service compatibility entrypoint.

Ordinary native restore/runtime helpers own supported engineering execution.
This service cannot create a request queue or run a supervised restore.
"""
from .authorization import require_active_phase


class BootstrapProvisioner:
    def __init__(self, project, evidence):
        require_active_phase('bootstrap-checkpoint')

    def poll(self, remaining):
        require_active_phase('bootstrap-checkpoint')
