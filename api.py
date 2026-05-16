"""Sleeve High-Level API. Delegiert die Gewindemechanik an Uni-threaded-rod."""
from .rod_link import get_rod_api


def create_sleeve_data(
    spec="M10",
    length=40.0,
    wall_thickness=3.5,
    outer_add=0.0,
    clearance=0.0,
    preset=None,
    standard="METRIC_ISO",
    starts=1,
    handedness="RIGHT",
    material="8.8",
    fit="6g/6H",
):
    """Berechnet die Geometrie-Eckdaten fuer eine Gewindemuffe.

    Verwendet Rods api.thread() fuer Pitch/Profil und ermittelt daraus die
    Innen-/Aussendurchmesser der Muffe.
    """
    rod_api = get_rod_api()
    thread_data = rod_api.thread(
        spec=spec,
        fit=fit,
        material=material,
        length=length,
        standard=standard,
        internal=True,
        starts=starts,
    )

    nominal = thread_data["diameter_mm"]
    outer_dia = nominal + 2.0 * wall_thickness + outer_add

    return {
        **thread_data,
        "outer_diameter": outer_dia,
        "wall_thickness": wall_thickness,
        "clearance": clearance,
        "preset": preset,
        "handedness": handedness,
    }


# Convenience-Alias
def sleeve(spec="M10", length=40.0, wall_thickness=3.5, **kwargs):
    return create_sleeve_data(spec=spec, length=length, wall_thickness=wall_thickness, **kwargs)
