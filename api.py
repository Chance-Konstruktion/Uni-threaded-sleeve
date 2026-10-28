"""Sleeve High-Level API. Delegiert die Gewindemechanik an Uni-threaded-rod."""
import math

from .rod_link import get_rod_api


def _validate_parameters(length, wall_thickness, outer_add, clearance, starts, handedness, pitch_override):
    """Validiert API-Eingaben, bevor ein Host-Objekt oder Gewinde erzeugt wird."""
    numeric = {
        "Länge": length,
        "Wandstärke": wall_thickness,
        "Außenzugabe": outer_add,
        "Spiel": clearance,
        "Steigungs-Override": pitch_override,
    }
    converted = {}
    for name, value in numeric.items():
        try:
            converted[name] = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} muss eine endliche Zahl sein.") from exc
        if not math.isfinite(converted[name]):
            raise ValueError(f"{name} muss eine endliche Zahl sein.")

    if not 5.0 <= converted["Länge"] <= 500.0:
        raise ValueError("Länge muss zwischen 5 und 500 mm liegen.")
    if converted["Wandstärke"] < 1.0:
        raise ValueError("Wandstärke muss mindestens 1 mm betragen.")
    if converted["Außenzugabe"] < 0.0:
        raise ValueError("Außenzugabe darf nicht negativ sein.")
    if not 0.0 <= converted["Spiel"] <= 1.0:
        raise ValueError("Spiel muss zwischen 0 und 1 mm liegen.")
    if converted["Steigungs-Override"] < 0.0:
        raise ValueError("Steigungs-Override muss 0 (Standard) oder positiv sein.")

    try:
        parsed_starts = int(starts)
        exact_starts = float(starts) == parsed_starts
    except (TypeError, ValueError, OverflowError):
        parsed_starts, exact_starts = 0, False
    if not exact_starts or not 1 <= parsed_starts <= 4:
        raise ValueError("Gängigkeit muss eine ganze Zahl zwischen 1 und 4 sein.")
    if str(handedness).upper() not in {"RIGHT", "LEFT"}:
        raise ValueError("Gewinderichtung muss RIGHT oder LEFT sein.")

    return {
        "length": converted["Länge"],
        "wall_thickness": converted["Wandstärke"],
        "outer_add": converted["Außenzugabe"],
        "clearance": converted["Spiel"],
        "starts": parsed_starts,
        "pitch_override": converted["Steigungs-Override"],
    }


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
    pitch_override=0.0,
):
    """Berechnet die Geometrie-Eckdaten fuer eine Gewindemuffe.

    Verwendet Rods api.thread() fuer Pitch/Profil und ermittelt daraus die
    Innen-/Aussendurchmesser der Muffe. Mit ``pitch_override > 0`` laesst sich
    die Rod-Standardsteigung manuell uebersteuern (z.B. M10 x 1.0 statt 1.5).
    """
    validated = _validate_parameters(
        length, wall_thickness, outer_add, clearance, starts, handedness, pitch_override
    )
    length = validated["length"]
    wall_thickness = validated["wall_thickness"]
    outer_add = validated["outer_add"]
    clearance = validated["clearance"]
    starts = validated["starts"]
    pitch_override = validated["pitch_override"]

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

    if pitch_override > 0:
        thread_data["pitch_mm"] = pitch_override

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
