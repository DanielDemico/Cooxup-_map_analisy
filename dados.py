import pandas as pd

def area_plantada():
    # Read excel with header at row 3 (0-indexed)
    area_plantada = pd.read_excel('./datas/produção2.xlsx', header=4)
    
    # Rename the first column to MUNICIPIO
    area_plantada.rename(columns={area_plantada.columns[0]: 'MUNICIPIO'}, inplace=True)
    
    # Drop the first 2 rows (empty row and 'Brasil' row) to keep only municipality data
    # Row 4 is empty, Row 5 is Brasil. header=3 means Row 3 is header.
    # So index 0 is Row 4, index 1 is Row 5.
    area_plantada = area_plantada.drop([0, 1])

    return area_plantada

def area_colhida():
    area_colhida = pd.read_excel('./datas/Area_colhida.xlsx', header=4)
    area_colhida.rename(columns={area_colhida.columns[0]: 'MUNICIPIO'}, inplace=True)
    area_colhida = area_colhida.drop([0, 1])
    return area_colhida
    
def hectares():
    # Read excel with header at row 0
    hectares = pd.read_excel('./datas/hectares-mg.xlsx', header=0)
    
    # Replace '-' with 0 and convert to numeric BEFORE pivoting
    hectares['Quantidade de Propriedades'] = hectares['Quantidade de Propriedades'].replace('-', 0)
    hectares['Quantidade de Propriedades'] = pd.to_numeric(hectares['Quantidade de Propriedades'])
    
    # Pivot the table to make categories into columns, aggregating duplicates
    hectares_pivot = hectares.pivot_table(index='Municipio', columns='Categoria Hectares', values='Quantidade de Propriedades', aggfunc='sum')
    
    # Reset index to make Municipio a column again
    hectares_pivot.reset_index(inplace=True)
    
    # Rename Municipio to MUNICIPIO to match other dataframes
    hectares_pivot.rename(columns={'Municipio': 'MUNICIPIO'}, inplace=True)
    
    return hectares_pivot

def cooperados():
    # Read excel
    df = pd.read_excel('cooxupé.xlsx')
    
    # Select specific columns
    df = df[['CIDADE', 'COOPERADOS']]
    
    return df

if __name__ == "__main__":
    df = area_plantada()
    print(df.columns)
    print(df.head())

    df = area_colhida()
    print(df.columns)
    print(df.head())
