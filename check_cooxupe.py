import pandas as pd

try:
    df = pd.read_excel('cooxupé.xlsx')
    print("Columns:", df.columns.tolist())
    print("First 5 rows:")
    print(df.head())
    print("\nUnique cities count:", df['CIDADE'].nunique())
    print("Total rows:", len(df))
    
    if 'CIDADE' in df.columns:
        dup_cities = df[df.duplicated('CIDADE', keep=False)]
        if not dup_cities.empty:
            print("\nDuplicate cities found:")
            print(dup_cities.head())
except Exception as e:
    print(e)
