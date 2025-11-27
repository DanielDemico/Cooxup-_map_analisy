import pandas as pd

try:
    df = pd.read_excel('./datas/hectares-mg.xlsx', header=0)
    
    # Check for duplicates
    duplicates = df[df.duplicated(subset=['Municipio', 'Categoria Hectares'], keep=False)]
    
    with open('debug_duplicates.txt', 'w', encoding='utf-8') as f:
        if not duplicates.empty:
            f.write("Found duplicates:\n")
            f.write(duplicates.sort_values(by=['Municipio', 'Categoria Hectares']).to_string())
        else:
            f.write("No duplicates found.")
        
except Exception as e:
    with open('debug_duplicates.txt', 'w', encoding='utf-8') as f:
        f.write(str(e))
