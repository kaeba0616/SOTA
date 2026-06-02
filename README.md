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

## Recognition (optional, needs ML deps)
Recognize the items you own straight from a screenshot instead of typing keys.
Install the ML libraries, build the canonical training set, and train the
classifier once:
```
pip install tensorflow opencv-python scikit-learn
python3 -c "from sota.recognize.dataset import build_canonical_dataset as b; import pathlib; b(pathlib.Path('.'), pathlib.Path('build/dataset'))"
python3 -c "from sota.recognize.train import train_model as t; t('build/dataset','CNN/sephiria_item_model.keras','CNN/classes.pickle')"
```
Then optimize from a screenshot:
```
python3 -m sota.cli --screenshot inventory.png --combo yinggalbul --slots 34 --out build.png
```
Low-confidence detections are listed and excluded; review them and re-add via
`--tablets/--artifacts` if needed. Without a trained model (or the ML deps), the
keys-based usage above works unchanged.

## Pipeline
data (`sota/data`) -> evaluation engine (`sota/evaluate`) -> GA solver (`sota/solve`) -> render/CLI (`sota/render`, `sota/cli.py`).
Recognition (`sota/recognize`) turns a screenshot into the item pool the solver consumes.
See `docs/superpowers/` for specs and plans, `docs/CALIBRATION.md` for known approximations.
