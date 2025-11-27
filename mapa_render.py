from flask import Flask, send_file, render_template, request
import os
import dados
import json
from unidecode import unidecode
from io import BytesIO
import pandas as pd

app = Flask(__name__)

def replace_states_values(x):
    if type(x) is str and x is not None:
        return x.replace('(SP)', '').replace('(MG)', '').strip()
    return x

@app.route('/')
def dashboard():
    # Get data type from query parameter, default to 'producao'
    data_type = request.args.get('data_type', 'producao')
    
    # Fetch data based on selection
    if data_type == 'area_colhida':
        df = dados.area_colhida()
        title_suffix = ' - Área Colhida'
    elif data_type == 'hectares':
        df = dados.hectares()
        title_suffix = ' - Por Hectares'
    else:
        df = dados.area_plantada()
        title_suffix = ' - Produção'

    df['MUNICIPIO'] = df['MUNICIPIO'].apply(replace_states_values)

    # Carregar lista de municípios filtrados
    if os.path.exists('municipios_filtrados.json'):
        with open('municipios_filtrados.json', 'r', encoding='utf-8') as f:
            valid_municipios = json.load(f)

        # Filtrar dados apenas para municípios presentes na lista
        valid_municipios_upper = {str(m).upper() for m in valid_municipios}
        
        # Normalizar nomes dos municípios no DataFrame para comparação
        df['MUNICIPIO_NORM'] = df['MUNICIPIO'].apply(lambda x: unidecode(str(x)).upper())
        
        # Filtrar DataFrame
        df = df[df['MUNICIPIO_NORM'].isin([unidecode(m).upper() for m in valid_municipios_upper])]
        
        # Remover coluna auxiliar
        df = df.drop(columns=['MUNICIPIO_NORM'])

    # Substituir valores NaN por 0
    df = df.fillna(0)

    # Converter DataFrame para lista de dicionários
    data = df.to_dict(orient='records')
    columns = df.columns.tolist()

    # Carregar dados de cooperados
    try:
        df_cooperados = dados.cooperados()
        cooperados_data = df_cooperados.to_dict(orient='records')
    except Exception as e:
        print(f"Erro ao carregar cooperados: {e}")
        cooperados_data = []

    return render_template('index.html', data=data, columns=columns, current_data_type=data_type, title_suffix=title_suffix, cooperados_data=cooperados_data)

@app.route('/map')
def serve_map():
    # Verifica se o mapa existe antes de tentar servir
    if not os.path.exists('mapa_raio.html'):
        return "O mapa ainda não foi gerado. Execute o script 'gerar_mapa.py' primeiro.", 404
    
    return send_file('mapa_raio.html')

@app.route('/download_data')
def download_data():
    data_type = request.args.get('data_type', 'producao')
    
    df_prod = dados.area_plantada()
    df_hectares = dados.hectares()
    df_area_colhida = dados.area_colhida()

    df = pd.merge(df_prod, df_area_colhida, on='MUNICIPIO', suffixes=(' produção (t)', ' área colhida (ha)'))
    df = pd.merge(df, df_hectares, on='MUNICIPIO')
    
    df['MUNICIPIO'] = df['MUNICIPIO'].apply(replace_states_values)

    # Filter logic for download (same as dashboard)
    if os.path.exists('municipios_filtrados.json'):
        try:
            with open('municipios_filtrados.json', 'r', encoding='utf-8') as f:
                valid_municipios = json.load(f)
            
            valid_municipios_upper = [str(m).upper() for m in valid_municipios]
            df = df[df['MUNICIPIO'].astype(str).str.upper().isin(valid_municipios_upper)]
        except Exception as e:
            print(f"Erro ao filtrar municipios para download: {e}")

    # Filter columns
    # 1. Produção/Área Colhida Filters
    
    # Identify all potential production/area columns in the dataframe
    # df_prod.columns contains crop names + MUNICIPIO.
    all_prod_cols = [c for c in df_prod.columns if c != 'MUNICIPIO']
    all_hectares_cols = [c for c in df_hectares.columns if c != 'MUNICIPIO']

    # Determine selected production columns
    if 'columns_producao' in request.args:
        selected_prod = request.args.getlist('columns_producao')
    else:
        # If not present in args, assume ALL (e.g. user never opened that tab or cleared storage)
        selected_prod = all_prod_cols

    # Determine selected hectares columns
    if 'columns_hectares' in request.args:
        selected_hectares = request.args.getlist('columns_hectares')
    else:
        selected_hectares = all_hectares_cols

    # Build the final list of columns to keep in the merged dataframe
    cols_to_keep = ['MUNICIPIO']
    
    # 1. Add Production/Area columns based on selection
    for col in selected_prod:
        # Check for suffixed versions first (priority)
        suffixed_prod = f"{col} produção (t)"
        suffixed_area = f"{col} área colhida (ha)"
        
        if suffixed_prod in df.columns:
            cols_to_keep.append(suffixed_prod)
        if suffixed_area in df.columns:
            cols_to_keep.append(suffixed_area)
        
        # Calculate Yield (Produção por hectare)
        if suffixed_prod in df.columns and suffixed_area in df.columns:
            yield_col = f"Produção por hectare - {col}"
            # Ensure numeric values for calculation
            s_prod = pd.to_numeric(df[suffixed_prod], errors='coerce').fillna(0)
            s_area = pd.to_numeric(df[suffixed_area], errors='coerce').fillna(0)
            
            # Calculate yield, handling division by zero (replace inf with 0)
            df[yield_col] = s_prod / s_area
            df[yield_col] = df[yield_col].replace([float('inf'), -float('inf')], 0).fillna(0)
            
            cols_to_keep.append(yield_col)
            
        # Also check for original name (if it didn't get suffixed, e.g. unique to one df)
        if col in df.columns:
            cols_to_keep.append(col)

    # 2. Add Hectares columns based on selection
    hectares_cols_found = []
    for col in selected_hectares:
        if col in df.columns:
            cols_to_keep.append(col)
            hectares_cols_found.append(col)
            
    # Add Sum of Properties for selected categories
    if hectares_cols_found:
        total_props_col = "Total de Propriedades"
        # Ensure numeric values
        df[hectares_cols_found] = df[hectares_cols_found].apply(pd.to_numeric, errors='coerce').fillna(0)
        df[total_props_col] = df[hectares_cols_found].sum(axis=1)
        cols_to_keep.append(total_props_col)

    # Remove duplicates just in case
    cols_to_keep = list(dict.fromkeys(cols_to_keep))
    
    # Filter dataframe
    df = df[cols_to_keep]

    output = BytesIO()
   
    df_visual = df.copy()
    df_visual.replace('-', pd.NA, inplace=True)
    df_visual.replace('...', pd.NA, inplace=True)

    df_visual.dropna(axis=1, how='all', inplace=True)

    # Create Summary DataFrame (Yield and Total Properties)
    summary_cols = ['MUNICIPIO']
    for col in df.columns:
        if "Produção por hectare" in col or col == "Total de Propriedades":
            summary_cols.append(col)
    
    df_produtividade = df[summary_cols].copy()
    
    # Add Nuclei Info
    if os.path.exists('municipios_detalhes.json'):
        try:
            with open('municipios_detalhes.json', 'r', encoding='utf-8') as f:
                municipios_detalhes = json.load(f)
            
            # Normalize keys for matching (uppercase)
            detalhes_upper = {unidecode(k).upper(): v for k, v in municipios_detalhes.items()}
            
            def get_nuclei_info(municipio):
                norm_name = unidecode(str(municipio)).upper()
                return detalhes_upper.get(norm_name, '')
                
            df_produtividade['Núcleos Cooxupé'] = df_produtividade['MUNICIPIO'].apply(get_nuclei_info)
        except Exception as e:
            print(f"Erro ao carregar detalhes dos municipios: {e}")

    df_produtividade.replace('-', pd.NA, inplace=True)
    df_produtividade.replace('...', pd.NA, inplace=True)
    df_produtividade.dropna(axis=1, how='all', inplace=True)

    # Sort by numeric columns (descending)
    sort_cols = [c for c in df_produtividade.columns if c != 'MUNICIPIO' and c != 'Núcleos Cooxupé']
    if sort_cols:
        df_produtividade.sort_values(by=sort_cols, ascending=False, inplace=True)

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
       df.to_excel(writer, index=False, sheet_name='Dados Brutos')
       df_visual.to_excel(writer, index=False,sheet_name='Dados Limpos')
       df_produtividade.to_excel(writer, index=False, sheet_name='Resumo Produtividade')
       
       workbook = writer.book
       
       # Format 'Dados Limpos'
       worksheet_limpos = writer.sheets['Dados Limpos']
       if not df_visual.empty:
           worksheet_limpos.set_column(0, len(df_visual.columns) - 1, 25)
           
       # Format 'Resumo Produtividade'
       worksheet_resumo = writer.sheets['Resumo Produtividade']
       if not df_produtividade.empty:
           worksheet_resumo.set_column(0, len(df_produtividade.columns) - 1, 25)

    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='dados_cooxupé.xlsx'
    )

if __name__ == "__main__":
    print("Servidor rodando em http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)