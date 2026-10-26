"""Sleeve High-Level API. Delegiert Gewindenormen an Uni-threaded-rod."""
import math

from .presets import PRESETS
from .rod_link import require_rod_compatibility


def _finite_float(name, value):
    """Convert a public numeric parameter and reject NaN/infinity explicitly."""
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} muss eine endliche Zahl sein.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} muss eine endliche Zahl sein.")
    return number


def _validate_sleeve_parameters(
    length, wall_thickness, outer_add, clearance, starts, handedness, pitch_override
):
    """Validate API inputs independently of Blender UI property limits."""
    length_mm = _finite_float("Länge", length)
    wall_mm = _finite_float("Wandstärke", wall_thickness)
    outer_add_mm = _finite_float("Extra Außen", outer_add)
    clearance_mm = _finite_float("Spiel", clearance)
    pitch_override_mm = _finite_float("Pitch override", pitch_override)

    if length_mm <= 0.0:
        raise ValueError("Länge muss > 0 mm sein.")
    if wall_mm < 1.0:
        raise ValueError("Wandstärke muss mindestens 1 mm betragen.")
    if outer_add_mm < 0.0:
        raise ValueError("Extra Außen muss >= 0 mm sein.")
    if not 0.0 <= clearance_mm <= 1.0:
        raise ValueError("Spiel muss zwischen 0 und 1 mm liegen.")
    if pitch_override_mm < 0.0:
        raise ValueError("Pitch override muss >= 0 mm sein (0 = Rod-Standard).")

    if isinstance(starts, bool):
        raise ValueError("Gängigkeit muss eine ganze Zahl von 1 bis 4 sein.")
    starts_number = _finite_float("Gängigkeit", starts)
    if not starts_number.is_integer() or not 1 <= starts_number <= 4:
        raise ValueError("Gängigkeit muss eine ganze Zahl von 1 bis 4 sein.")

    handedness_key = str(handedness).strip().upper()
    if handedness_key not in {"RIGHT", "LEFT"}:
        raise ValueError("Drehrichtung muss RIGHT oder LEFT sein.")

    return {
        "length_mm": length_mm,
        "wall_thickness_mm": wall_mm,
        "outer_add_mm": outer_add_mm,
        "clearance_mm": clearance_mm,
        "starts": int(starts_number),
        "handedness": handedness_key,
        "pitch_override_mm": pitch_override_mm,
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
    """Berechne verlässliche Geometrie- und Mechanikdaten für eine Gewindemuffe.

    Rod ist die einzige Quelle für Normdaten und Profilformeln. Ein positiver
    Pitch-Override ersetzt nicht nur die Steigung, sondern löst die Profil-
    und Mechanikberechnung mit genau dieser Steigung erneut aus. Ein Wert von
    0 nutzt die Standardsteigung aus der Rod-Datenbank.
    """
    params = _validate_sleeve_parameters(
        length, wall_thickness, outer_add, clearance, starts, handedness, pitch_override
    )
    spec_token = str(spec).strip()
    standard_key = str(standard).strip()
    if not spec_token:
        raise ValueError("Gewindegröße darf nicht leer sein.")
    if not standard_key:
        raise ValueError("Gewindestandard darf nicht leer sein.")

    preset_key = str(preset).strip() if preset is not None else None
    if preset_key is None or preset_key in {"", "NONE"}:
        preset_key = None
    elif preset_key not in PRESETS:
        raise ValueError(f"Unbekanntes Sleeve-Preset: {preset_key}")

    rod = require_rod_compatibility()
    thread_data = rod["api"].thread(
        spec=spec_token,
        fit=fit,
        material=material,
        length=params["length_mm"],
        standard=standard_key,
        internal=True,
        starts=params["starts"],
    )

    diameter = _finite_float("Nenndurchmesser", thread_data.get("diameter_mm"))
    default_pitch = _finite_float("Rod-Steigung", thread_data.get("pitch_mm"))
    if diameter <= 0.0:
        raise ValueError("Nenndurchmesser muss > 0 mm sein.")
    if default_pitch <= 0.0:
        raise ValueError("Rod-Steigung muss > 0 mm sein.")

    pitch = params["pitch_override_mm"] if params["pitch_override_mm"] > 0.0 else default_pitch
    thread_data["diameter_mm"] = diameter
    thread_data["pitch_mm"] = pitch
    thread_data["length_mm"] = params["length_mm"]

    if params["pitch_override_mm"] > 0.0:
        # The Rod API's original profile/mechanics describe its table pitch.
        # Regenerate both with the effective pitch rather than returning mixed
        # metadata that contradicts the cutter created by sleeve_builder.
        tolerance_class = thread_data.get("tolerance_class")
        property_class = thread_data.get("property_class")
        if tolerance_class is None or property_class is None:
            raise ImportError(
                "Die installierte Uni-threaded-rod-Version liefert keine "
                "Toleranz-/Werkstoffmetadaten für Pitch override. Bitte Rod aktualisieren."
            )

        profile, ratio_warnings = rod["geometry_engine"].generate_profile(
            standard_key,
            diameter,
            pitch,
            tolerance_class=tolerance_class,
            internal=True,
            clearance=0.0,
            return_warnings=True,
        )
        thread_data["profile_points"] = profile
        thread_data["ratio_warnings"] = ratio_warnings

        mechanics_api = rod["mechanical_validation"]
        allowables = mechanics_api.allowables_from_property_class(property_class)
        thread_data["mechanics"] = mechanics_api.validate_combined_load_case(
            axial_force_n=0.0,
            transverse_force_n=0.0,
            torsion_moment_nmm=0.0,
            diameter=diameter,
            pitch=pitch,
            engagement_length=min(
                params["length_mm"], max(diameter, pitch * 2.0)
            ),
            allowable_tensile_mpa=allowables["allowable_tensile_mpa"],
            allowable_shear_mpa=allowables["allowable_shear_mpa"],
            standard_key=standard_key,
        )

    outer_diameter = diameter + 2.0 * params["wall_thickness_mm"] + params["outer_add_mm"]
    if not math.isfinite(outer_diameter) or outer_diameter <= diameter:
        raise ValueError("Berechneter Außendurchmesser ist ungültig.")

    return {
        **thread_data,
        "standard": standard_key,
        "spec": spec_token,
        "outer_diameter": outer_diameter,
        "wall_thickness": params["wall_thickness_mm"],
        "outer_add": params["outer_add_mm"],
        "clearance": params["clearance_mm"],
        "preset": preset_key,
        "starts": params["starts"],
        "handedness": params["handedness"],
        "pitch_override_mm": params["pitch_override_mm"],
    }


def sleeve(spec="M10", length=40.0, wall_thickness=3.5, **kwargs):
    """Convenience alias for create_sleeve_data."""
    return create_sleeve_data(spec=spec, length=length, wall_thickness=wall_thickness, **kwargs)
