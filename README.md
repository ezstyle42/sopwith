# Sopwith (cross-platform reimplementation)

A modern, cross-platform reimplementation of **Sopwith** (BMB Compuscience
Canada Ltd., 1984; network edition v7.F15 by David L. Clark), reconstructed
from the decompiled 16-bit DOS binary `sw.exe`.

The original ran on DOS using BIOS text-mode video (`int 0x10`), the PC
joystick port `0x201`, and a communications file (`c:sopwith?.dta` /
`c:semaphor`) for multiplayer. This port replaces those with SDL2 via
pygame, so it runs on Windows, macOS and Linux.

## Requirements

- Python 3.9+
- pygame 2.x (`pip install -r requirements.txt`)

## Run

```sh
python sopwith.py        # title screen, then press S
python sopwith.py -n     # novice single player (starts immediately-ish)
python sopwith.py -q     # sound off flag (accepted for CLI compatibility)
python sopwith.py --seed 42   # fixed world layout
```

## Controls

| Key | Action |
| --- | --- |
| Arrow keys / WASD | Fly (throttle burns fuel) |
| SPACE | Drop bomb |
| ESC | Quit / back to title |
| ENTER | Continue after "all targets destroyed" / game over |

## Objective

Fly right over the enemy lines and bomb the bridges, tanks, hangars and
fuel depots. Land gently at your own base (left side) to refuel and
rearm. You have 3 planes. Crashing (hitting ground away from base, or
colliding with a target) costs a life.

## Original command-line options honored

`-n` novice, `-s` single player, `-c` vs computer, `-q` quiet — parsed for
compatibility with `sw.exe`; `-m`/`-a` network play is replaced by local
single player in this port.

## Files

- `sopwith.py` — the whole game (engine, world, rendering, input)
- `requirements.txt` — pygame
- `test_headless.py` — smoke test that runs the game loop headlessly
