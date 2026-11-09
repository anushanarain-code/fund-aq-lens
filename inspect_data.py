import pandas as pd

file_path = r"C:\Users\divya\aq-prototype\data\aim_companies.csv"

df = pd.read_csv(file_path)

print("DATASET SIZE:", df.shape)

print("\nCATEGORY COUNTS:")
print(df["Category"].value_counts(dropna=False))

print("\nDUPLICATE ISINs:")
print(df["ISIN Code"].duplicated(keep=False).sum())

print("\nMISSING ISINs:")
print(df["ISIN Code"].isna().sum())