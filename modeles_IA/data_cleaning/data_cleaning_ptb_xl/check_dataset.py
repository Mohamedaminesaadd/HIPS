from pathlib import Path

path =r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3"
PTBXL_DIR = Path(path)


required_items = [
    "ptbxl_database.csv",
    "scp_statements.csv",
    "records100",
    "records500",
]


print("=" * 50)
print("PTB-XL DATASET CHECK")
print("=" * 50)


for item in required_items:

    path = PTBXL_DIR / item

    if path.exists():
        print(f"[OK]      {path}")
    else:
        print(f"[MISSING] {path}")


print("=" * 50)