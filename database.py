"""Lazy-Forwarder zu Uni-threaded-rod.database.

Kein Top-Level-Import des Rod-Moduls -> dieses Modul laedt sich auch dann
fehlerfrei, wenn Rod (noch) nicht aktiv ist. Damit crasht das Sleeve-Addon
nicht mehr beim Install/Enable.
"""
from .rod_link import get_rod_database


def get_standards():
    try:
        return get_rod_database().THREAD_STANDARDS
    except Exception:
        return {}


def get_diameter_items_for_standard(standard_key):
    try:
        return get_rod_database().get_diameter_items_for_standard(standard_key)
    except Exception:
        return []


def resolve_thread_parameters(standard_key, token):
    return get_rod_database().resolve_thread_parameters(standard_key, token)


# Backwards-compat: STANDARDS als Property-aehnliches Lazy-Objekt.
class _LazyStandards:
    def __getitem__(self, key):
        return get_standards()[key]

    def __iter__(self):
        return iter(get_standards())

    def items(self):
        return get_standards().items()

    def keys(self):
        return get_standards().keys()

    def values(self):
        return get_standards().values()

    def get(self, key, default=None):
        return get_standards().get(key, default)

    def __contains__(self, key):
        return key in get_standards()

    def __len__(self):
        return len(get_standards())


STANDARDS = _LazyStandards()
