# Uni-threaded-sleeve

Parametric threaded sleeve / coupling nut generator for Blender 4.0+.

**Requires:** [Uni-threaded-rod](https://github.com/Chance-Konstruktion/Uni-threaded-rod) — the Rod engine provides thread data and geometry.

---

## Features
- All thread standards from the Rod database (Metric ISO, Trapezoidal, Pipe, UNC, NPT, …)
- Presets: Standard sleeve, Repair sleeve (+0.3 mm clearance), Pipe sleeve, Heavy Duty, Flange, Trapezoidal
- Outer shape: round or hexagonal
- Optional flange
- Adjustable clearance for repair sleeves
- Multi-start threads (1–4), right- or left-handed
- Fully integrated with the Uni-threaded-rod engine

## Installation
1. Install and enable [Uni-threaded-rod](https://github.com/Chance-Konstruktion/Uni-threaded-rod)
2. Install and enable this add-on
3. Open the 3D viewport sidebar (`N`) → tab **Uni-threaded-sleeve**

## Quick start
1. Pick a **preset** (or leave it for manual control)
2. Select **thread standard** and **diameter**
3. Adjust length, wall thickness, clearance as needed
4. Click **Sleeve erstellen**

## Parameters
| Parameter      | Range          | Default |
|----------------|----------------|---------|
| Length         | 5–500 mm       | 40 mm   |
| Wall thickness | ≥ 1 mm         | 3.5 mm  |
| Extra outer    | ≥ 0 mm         | 0 mm    |
| Clearance      | 0–1 mm         | 0 mm    |
| Starts         | 1–4            | 1       |
| Handedness     | Right / Left   | Right   |

## Presets
| Preset            | Wall | Extra outer | Clearance | Flange |
|-------------------|------|-------------|-----------|--------|
| Standard Muffe    | 3.5  | 7.0         | –         | –      |
| Reparatur-Sleeve  | 4.0  | 8.0         | 0.3       | –      |
| Rohrmuffe         | 4.5  | 10.0        | –         | –      |
| Heavy Duty        | 5.5  | 12.0        | –         | –      |
| Mit Flansch       | 4.0  | 8.0         | –         | ✓      |
| Trapezgewinde     | 5.0  | 10.0        | –         | –      |

## Version
1.4.0 — Blender 4.0+

## License
[GNU General Public License v3.0](LICENSE)

---

# Deutsch

Parametrischer Gewindemuffen-Generator für Blender 4.0+.

**Benötigt:** [Uni-threaded-rod](https://github.com/Chance-Konstruktion/Uni-threaded-rod) — die Rod-Engine liefert Gewindedaten und Geometrie.

## Features
- Alle Gewindetypen aus der Rod-Datenbank (Metrisch ISO, Trapez, Rohr, UNC, NPT, …)
- Presets: Standard-Muffe, Reparatur-Sleeve (+0.3 mm Spiel), Rohrmuffe, Heavy Duty, Flansch, Trapez
- Außenform rund oder sechskant
- Optionaler Flansch
- Einstellbares Spiel (Clearance) für Reparatur-Sleeves
- Mehrgängig (1–4), Rechts- oder Linksgewinde
- Voll integriert mit der Uni-threaded-rod Engine

## Installation
1. [Uni-threaded-rod](https://github.com/Chance-Konstruktion/Uni-threaded-rod) installieren und aktivieren
2. Dieses Add-on installieren und aktivieren
3. Im 3D-Viewport Sidebar (`N`) öffnen → Tab **Uni-threaded-sleeve**

## Schnellstart
1. **Preset** wählen (oder leer lassen für manuelle Steuerung)
2. **Gewindetyp** und **Durchmesser** auswählen
3. Länge, Wandstärke, Spiel anpassen
4. Auf **Sleeve erstellen** klicken

## Parameter
| Parameter   | Bereich        | Standard |
|-------------|----------------|----------|
| Länge       | 5–500 mm       | 40 mm    |
| Wandstärke  | ≥ 1 mm         | 3.5 mm   |
| Extra Außen | ≥ 0 mm         | 0 mm     |
| Spiel       | 0–1 mm         | 0 mm     |
| Gängig      | 1–4            | 1        |
| Richtung    | Rechts / Links | Rechts   |

## Lizenz
[GNU General Public License v3.0](LICENSE)
