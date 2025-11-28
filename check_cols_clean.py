import pandas as pd
df = pd.read_excel('cooxupé.xlsx')
for col in df.columns:
    print(f"'{col}'")
