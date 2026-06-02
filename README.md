# SOTA (Sephiria Optimal Tablet Arranger)
세피리아 석판 최적화 배치 자동 계산기

## Usage
```
python3 -m sota.cli --list-combos
python3 -m sota.cli --combo yinggalbul \
    --tablets peace,honor,courage \
    --artifacts fire_bolt,ohia_lehua,ignition,magma_bead \
    --slots 34 --seed 1 --out build.png
```
Outputs a build summary (score = combo stages x1000 + target level sum) and an
arranged-grid PNG. Item keys are the English keys in `sota/data/{tablets,artifacts}.json`.

## Pipeline
data (`sota/data`) -> evaluation engine (`sota/evaluate`) -> GA solver (`sota/solve`) -> render/CLI (`sota/render`, `sota/cli.py`).
See `docs/superpowers/` for specs and plans, `docs/CALIBRATION.md` for known approximations.
