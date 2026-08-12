from pathlib import Path

import pandas as pd


# --------------------------------------------------
# Configuration
# --------------------------------------------------
path =r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3"
PTBXL_DIR = Path(path)


SCP_PATH = PTBXL_DIR / "scp_statements.csv"


# --------------------------------------------------
# 1. Load SCP statements
# --------------------------------------------------

scp = pd.read_csv(
    SCP_PATH,
    index_col=0
)


# --------------------------------------------------
# 2. Basic information
# --------------------------------------------------

print("=" * 70)
print("SCP STATEMENTS")
print("=" * 70)

print("\nShape:")
print(scp.shape)


# --------------------------------------------------
# 3. Columns
# --------------------------------------------------

print("\nColumns:")

for column in scp.columns:
    print(f" - {column}")


# --------------------------------------------------
# 4. First rows
# --------------------------------------------------

print("\nFirst 10 rows:")

print(scp.head(10))