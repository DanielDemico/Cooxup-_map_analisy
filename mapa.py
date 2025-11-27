import pandas as pd
import folium
from folium.features import CustomIcon
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import json
from shapely.geometry import shape, Point, mapping
from shapely.ops import unary_union
import os

def gerar_mapa():
    df = pd.read_excel('cooxupé.xlsx')
    
    geolocator = Nominatim(user_agent="projeto_cooxupe_analise_v2", timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)

    def get_location(cep):
        try:
            cep_clean = str(cep).replace('.', '').replace('-', '')
            print(f"Buscando: {cep_clean}...")
            loc = geocode(f"{cep_clean}, Brazil")
            if loc:
                return loc.latitude, loc.longitude
            else:
                print(f" -> Não encontrado: {cep}")
                return None
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            print(f" -> Erro de conexão no CEP {cep}: {e}")
            return None
        except Exception as e:
            print(f" -> Erro genérico: {e}")
            return None

    df['Estado_Cidade'] = df['CIDADE'] + ', ' + df['ESTADO']
    df['coordenadas'] = df['Estado_Cidade'].apply(get_location)

 
    df_validos = df.dropna(subset=['coordenadas'])
    
    if df_validos.empty:
      
        return


    start_lat = df_validos.iloc[0]['coordenadas'][0]
    start_lon = df_validos.iloc[0]['coordenadas'][1]
    m = folium.Map(location=[start_lat, start_lon], zoom_start=8)

    # --- Lógica de Interseção ---
    print("Calculando interseções...")
    
    # Pre-calculate nucleus buffers with their info
    # Pre-calculate nucleus buffers with their info
    nuclei_buffers = []
    simple_buffers = [] # For unary_union
    
    for _, row in df_validos.iterrows():
        lat, lon = row['coordenadas']
        # 0.18 degrees is approximately 20km
        b = Point(lon, lat).buffer(0.16)
        simple_buffers.append(b)
        
        # Get ORG and ORG RESP info (combined column)
        info = str(row.get('ORG e ORG RESP', '')).strip()
        
        nuclei_buffers.append((b, info))

    area_cobertura = unary_union(simple_buffers)
    municipios_filtrados = []
    municipios_detalhes = {} # Name -> "Info1; Info2"
    
    arquivos_geojson = ['municipios_mg.json', 'municipios_sp.json']

    for arquivo in arquivos_geojson:
        if not os.path.exists(arquivo):
            print(f"Aviso: Arquivo {arquivo} não encontrado.")
            continue
            
        with open(arquivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for feature in data['features']:
            geom = shape(feature['geometry'])
            
            if area_cobertura.intersects(geom):
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': 'green',
                        'color': 'green',
                        'weight': 1,
                        'fillOpacity': 0.4
                    },
                    tooltip=feature['properties'].get('name', 'Municipio')
                ).add_to(m)
                
                nome_municipio = feature['properties'].get('name')
                if nome_municipio:
                    municipios_filtrados.append(nome_municipio)
                    
                    # Identify specific nuclei intersecting this municipality
                    intersecting_infos = []
                    for b, info in nuclei_buffers:
                        if b.intersects(geom):
                            if info: # Only add if info is not empty
                                intersecting_infos.append(info)
                    
                    if intersecting_infos:
                        # Deduplicate and join
                        municipios_detalhes[nome_municipio] = "; ".join(sorted(list(set(intersecting_infos))))

    for _, row in df_validos.iterrows():
        lat, lon = row['coordenadas']

        icon_image = CustomIcon(
            icon_image='./map_icon.png',
            icon_size=(30, 30),
            icon_anchor=(15, 15)
        )
        folium.Marker(
            location=[lat, lon],
            popup=f"CIDADE: {row['CIDADE']}\n COOPERADOS: {row['COOPERADOS']}",
            icon=icon_image
        ).add_to(m)

    
        folium.Circle(
            location=[lat, lon],
            radius=20000,
            color="green",
            fill=False, # Só borda
            weight=1
        ).add_to(m)

    # Inject Custom JS for Interaction
    custom_js = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Wait for map to initialize
        setTimeout(function() {
            var map = null;
            // Find the map object in global scope (Folium usually names it 'map_randomid')
            for (var key in window) {
                if (key.startsWith('map_')) {
                    map = window[key];
                    break;
                }
            }
            
            if (!map) return;

            // Store original styles
            var originalStyles = {};

            // Iterate over layers to find GeoJSONs
            map.eachLayer(function(layer) {
                if (layer.feature && layer.feature.properties && layer.feature.properties.name) {
                    var name = layer.feature.properties.name;
                    
                    // Add Click Listener
                    layer.on('click', function(e) {
                        window.parent.postMessage({
                            type: 'municipioClick',
                            name: name
                        }, '*');
                    });
                    
                    // Store reference for external access
                    layer._municipioName = name;
                }
            });

            // Listen for messages from parent
            window.addEventListener('message', function(event) {
                var data = event.data;
                
                if (data.type === 'municipioHover') {
                    var targetName = data.name.toUpperCase();
                    map.eachLayer(function(layer) {
                        if (layer._municipioName && layer._municipioName.toUpperCase() === targetName) {
                            // Save original style if not saved
                            if (!originalStyles[layer._leaflet_id]) {
                                originalStyles[layer._leaflet_id] = {
                                    fillColor: layer.options.fillColor,
                                    fillOpacity: layer.options.fillOpacity
                                };
                            }
                            
                            // Highlight
                            layer.setStyle({
                                fillColor: 'yellow',
                                fillOpacity: 0.7
                            });
                        }
                    });
                } else if (data.type === 'municipioLeave') {
                    var targetName = data.name.toUpperCase();
                    map.eachLayer(function(layer) {
                        if (layer._municipioName && layer._municipioName.toUpperCase() === targetName) {
                            // Restore style
                            var style = originalStyles[layer._leaflet_id];
                            if (style) {
                                layer.setStyle(style);
                            }
                        }
                    });
                }
            });
        }, 1000); // Delay to ensure map load
    });
    </script>
    """
    
    m.get_root().html.add_child(folium.Element(custom_js))

    m.save("mapa_raio.html")
    
    # Salvar lista de municipios filtrados
    with open('municipios_filtrados.json', 'w', encoding='utf-8') as f:
        json.dump(municipios_filtrados, f, ensure_ascii=False, indent=2)
        
    # Salvar detalhes dos municipios (nucleos que atingem)
    with open('municipios_detalhes.json', 'w', encoding='utf-8') as f:
        json.dump(municipios_detalhes, f, ensure_ascii=False, indent=2)
        
    print(f"Sucesso. Mapa gerado. {len(municipios_filtrados)} municípios interceptados.")
    return 

if __name__ == "__main__":
    gerar_mapa()
