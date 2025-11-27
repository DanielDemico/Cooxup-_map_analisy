import dados
import pandas as pd

try:
    print("Testing dados.hectares()...")
    df = dados.hectares()
    print("Success!")
    print("Columns:", df.columns.tolist())
    print("Shape:", df.shape)
    print("First 5 rows:")
    print(df.head().to_string())
except Exception as e:
    print("Error:")
    print(e)
