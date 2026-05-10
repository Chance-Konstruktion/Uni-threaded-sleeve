PRESETS = {
    "STANDARD_MUFFE": {"name": "Standard Muffe", "outer_add": 7.0, "wall": 3.5},
    "REPARATUR":      {"name": "Reparatur-Sleeve (+0.3mm)", "outer_add": 8.0, "wall": 4.0, "clearance": 0.3},
    "ROHR_MUFFE":     {"name": "Rohrmuffe", "outer_add": 10.0, "wall": 4.5},
    "HEAVY_DUTY":     {"name": "Heavy Duty", "outer_add": 12.0, "wall": 5.5},
    "FLANSCH":        {"name": "Mit Flansch", "outer_add": 8.0, "wall": 4.0, "flange": True},
    "TRAPEZ":         {"name": "Trapezgewinde Sleeve", "outer_add": 10.0, "wall": 5.0, "standard": "TRAPEZOIDAL"},
}


def get_preset_items():
    return [(k, v["name"], "") for k, v in PRESETS.items()]
