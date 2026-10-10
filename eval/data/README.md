# RDD2022 India Dataset Directory

This directory is reserved for RDD2022 (Road Damage Dataset 2022) Indian road imagery and Pascal-VOC annotations.

## Instructions
Place the dataset files under `eval/data/rdd2022_india/`:
- `images/`: JPEG image files (e.g., `India_000001.jpg`, ...)
- `annotations/xmls/`: Pascal-VOC XML files containing bounding boxes (`D00`, `D10`, `D20`, `D40`).
  - `D40` indicates pothole damage.
  - `D00`, `D10`, `D20` indicate longitudinal, lateral, and alligator cracks.

## Dataset Reference & License
- **Dataset:** Road Damage Dataset 2022 (RDD2022) / Global Road Damage Detection Challenge (GRDDC 2022)
- **Source:** Arya, D. et al., "Global Road Damage Detection: State-of-the-Art Solutions"
- **License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
- **Attribution:** Included in `CREDITS.md`.

## Execution
Run:
```bash
python eval/rdd2022_eval.py
```
If the directory is empty or missing, the evaluation exits safely with exit code 0 and instructions.
