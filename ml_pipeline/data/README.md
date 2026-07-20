# ML Pipeline Data Directory

Place NSL-KDD dataset files here:

## Download
1. Visit: https://www.unb.ca/cic/datasets/nsl.html
2. Download: **NSL-KDD dataset (KDDTrain+.txt / KDDTest+.txt)**
3. Convert to CSV and rename:
   - `NSL-KDD-Train.csv`  ← KDDTrain+.txt
   - `NSL-KDD-Test.csv`   ← KDDTest+.txt

## Column Format
NSL-KDD has 43 columns (41 features + label + difficulty_level).
No header row — the training script adds column names automatically.

## File Size Reference
- KDDTrain+ : ~125,973 records (~18 MB)
- KDDTest+  : ~22,544  records (~3.2 MB)
