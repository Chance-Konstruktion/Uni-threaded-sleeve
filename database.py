from Uni_threaded_rod.database import STANDARDS as ROD_STANDARDS, get_diameter_items_for_standard as rod_get_diameters

# Erweiterte Datenbank für Sleeves
STANDARDS = ROD_STANDARDS

get_diameter_items_for_standard = rod_get_diameters

PRESETS = {
    "STANDARD_MUFFE": {"name": "Standard Muffe", "outer_add": 7, "wall": 3.5},
    "REPARATUR": {"name": "Reparatur-Sleeve (+0.3mm)", "outer_add": 8, "wall": 4.0, "clearance": 0.3},
    "ROHR_MUFFE": {"name": "Rohrmuffe", "outer_add": 10, "wall": 4.5},
    "HEAVY_DUTY": {"name": "Heavy Duty", "outer_add": 12, "wall": 5.5},
    "FLANSCH": {"name": "Mit Flansch", "outer_add": 8, "wall": 4.0, "flange": True},
    "TRAPEZ": {"name": "Trapezgewinde Sleeve", "outer_add": 10, "wall": 5.0},
}

def get_preset_items():
    return [(k, v["name"], "") for k, v in PRESETS.items()]