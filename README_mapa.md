# Mapa das Cooperativas

Este projeto cria um mapa interativo das cooperativas usando dados do arquivo `cooperativas.json`.

## Funcionalidades

- **Marcadores**: Cada cooperativa é representada por um marcador no mapa com seu nome
- **Informações detalhadas**: Clique nos marcadores para ver informações completas (nome, município, estado, endereço, CEP, raio)
- **Círculos de raio**: Cada cooperativa tem um círculo azul representando seu raio de atuação em quilômetros
- **Raio padrão**: Quando o raio é "None" no JSON, é usado automaticamente 100km como padrão

## Como usar

### Mapa básico (3 cooperativas)
```bash
python mapa_cooperativas.py
# ou
python mapa_cooperativas.py cooperativas.json
```

### Mapa completo (49 cooperativas)
```bash
python mapa_cooperativas.py cooperativas_completo.json
```

### Abrir automaticamente no navegador
```bash
python abrir_mapa.py
```

### URLs disponíveis no servidor Flask:
- `http://127.0.0.1:5000/` - Mapa básico (3 cooperativas)
- `http://127.0.0.1:5000/completo` - Mapa completo (49 cooperativas)
- `http://127.0.0.1:5000/heatmap` - Mapa heatmap (24 cooperativas)
- `http://127.0.0.1:5000/heatmap-completo` - Mapa heatmap completo (48 cooperativas)

### Arquivos gerados
- `mapa_cooperativas.html` - Mapa das 3 cooperativas básicas
- `mapa_cooperativas_completo.html` - Mapa das 49 cooperativas completas
- `heatmap_cooperativas.html` - **NOVO:** Mapa coroplético (heatmap) dos municípios com cooperativas

## Mapa Heatmap (Coroplético)

O heatmap mostra a distribuição das cooperativas por município usando polígonos dos municípios brasileiros:

### Características:
- **Polígonos coloridos**: Cada município é colorido baseado no número de cooperativas
- **Escala de cores**: De amarelo (poucas cooperativas) para vermelho (muitas cooperativas)
- **Dados geoespaciais**: Usa polígonos oficiais dos municípios de MG e SP
- **Marcadores**: Pontos vermelhos nos centroides dos municípios com cooperativas

### Como usar:
```bash
# Gerar heatmap
python mapa_heatmap_cooperativas.py cooperativas.json

# Ou com dados completos
python mapa_heatmap_cooperativas.py cooperativas_completo.json
```

3. Navegue pelo mapa - você pode:
   - Zoom in/out
   - Clicar nos marcadores para ver detalhes
   - Ver os círculos azuis representando os raios

## Estrutura dos dados

O arquivo `cooperativas.json` deve ter a seguinte estrutura:

```json
[
    {
        "nome": "Nome da Cooperativa",
        "municipio": "Nome do Município",
        "Estado": "UF",
        "endereço": "Endereço completo",
        "raio": "valor em km ou 'None'",
        "CEP": "XXXXX-XXX"
    }
]
```

## Dependências

- folium: Para criação de mapas interativos
- geopy: Para geocodificação dos CEPs
- pandas: Para manipulação de dados
- requests: Para chamadas HTTP (usado pelo geopy)

## Instalação das dependências

```bash
pip install folium geopy pandas
```

## Resultado

O script gera um arquivo `mapa_cooperativas.html` que pode ser aberto em qualquer navegador moderno. O mapa mostra todas as cooperativas plotadas com seus respectivos raios de atuação.
