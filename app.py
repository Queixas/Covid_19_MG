import streamlit as st
import pandas as pd
import numpy as np
import time
from geopy.geocoders import Nominatim
import plotly.express as px

# Configuração da página
st.set_page_config(layout="wide", page_title="Relação Covid/Vacinação em Minas Gerais", page_icon=":mask:")
# Lendo o conteúdo do arquivo CSS
with open("styles.css", "r", encoding="utf-8") as f:
    css = f.read()

# Inserindo o CSS usando st.markdown
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Função para carregar e preparar os dados
@st.cache_data(show_spinner=False)
def carregar_dados(caminhos_arquivos):
    df_list = [pd.read_csv(caminho, sep=";") for caminho in caminhos_arquivos]
    df = pd.concat(df_list, ignore_index=True)
    colunas_para_remover = [
        'regiao', 'coduf', 'codmun', 'codRegiaoSaude', 'nomeRegiaoSaude',
        'semanaEpi', 'populacaoTCU2019', 'emAcompanhamentoNovos',
        'interior/metropolitana', 'casosAcumulado','obitosAcumulado'
    ]
    df.drop(columns=colunas_para_remover, inplace=True)
    df['data'] = pd.to_datetime(df['data'])
    df['mes'] = df['data'].dt.to_period('M')
    df_mg = df[df['estado'] == "MG"].copy()
    df_mg['municipio'] = df_mg['municipio'].fillna("Todos - MG")
    df_mg['Recuperadosnovos'] = df_mg['Recuperadosnovos'].fillna(0)
    df_mg.drop(columns=['estado'], inplace=True) #depois de realizar o filtro, removida a coluna que repete "MG"
    return df_mg

# Carregar os dados
caminhos_arquivos = [
    'painelcovid (1).csv', 'painelcovid (2).csv', 'painelcovid (3).csv',
    'painelcovid (4).csv', 'painelcovid (5).csv', 'painelcovid (6).csv',
    'painelcovid (7).csv', 'painelcovid (8).csv', 'painelcovid (9).csv'
]
df_mg = carregar_dados(caminhos_arquivos)
# Carregar os dados
df_mg = carregar_dados([
    f'painelcovid ({i}).csv' for i in range(1, 10)
])

# Adicionar seletores na barra lateral
st.sidebar.header("Filtros🔍")

# Seleção de intervalo de datas
st.sidebar.text(f"Base de dados abrange de \n01/01/2020 a 30/04/2024")

# Seleção de mês e ano de início
mes_inicio = st.sidebar.selectbox("Mês de Início📅", range(1, 13), format_func=lambda x: f"{x:02d}")
ano_inicio = st.sidebar.selectbox("Ano de Início📅", range(2020, 2025))
data_inicio = pd.to_datetime(f"{ano_inicio}-{mes_inicio:02d}-01")

# Seleção de municípios
st.sidebar.subheader("Municípios")
municipios = df_mg['municipio'].unique()
municipios_selecionados = st.sidebar.multiselect("Municípios📌", municipios, placeholder="Digite ou selecione.")

# Função para aplicar o filtro
def aplicar_filtro(df, data_inicio, data_fim, municipios_selecionados):
    df_filtrado = df[(df['data'] >= data_inicio) & (df['data'] <= data_fim)]
    if municipios_selecionados:
        df_filtrado = df_filtrado[df_filtrado['municipio'].isin(municipios_selecionados)]
    return df_filtrado
# Seleção de mês e ano de fim
mes_fim = st.sidebar.selectbox("Mês de Fim📅", range(1, 13), index=3, format_func=lambda x: f"{x:02d}")
ano_fim = st.sidebar.selectbox("Ano de Fim📅", range(2020, 2025), index=4)
data_fim = pd.to_datetime(f"{ano_fim}-{mes_fim:02d}-01") + pd.offsets.MonthEnd()


# Aplicar o filtro
df_mg_filtrado = aplicar_filtro(df_mg, data_inicio, data_fim, municipios_selecionados)

# Agrupar os dados por mês
df_mg_filtrado_mes = df_mg_filtrado.groupby(['municipio', 'mes']).agg({
    'casosNovos': 'sum',
    'obitosNovos': 'sum',
    'Recuperadosnovos': 'sum'
}).reset_index()


# Adicionando o conteúdo ao topo da página
#st.title(":mask: Covid-19 em Minas Gerais")

st.markdown('<p class="title">Covid-19 em Minas Gerais </p>', unsafe_allow_html=True)
st.markdown('<style>.title{margin-top:-70px}</style>', unsafe_allow_html=True)


# Função para obter coordenadas de municípios
@st.cache_data(show_spinner=False)
def obter_coordenadas(municipios):
    geolocator = Nominatim(user_agent="covid_mg_app")
    coordenadas = {}
    for municipio in municipios:
        try:
            location = geolocator.geocode(f"{municipio}, Minas Gerais, Brazil", timeout=10)
            if location:
                coordenadas[municipio] = (location.latitude, location.longitude)
            else:
                coordenadas[municipio] = (np.nan, np.nan)
        except Exception as e:
            st.write(f"Erro ao obter coordenadas para {municipio}: {e}")
            coordenadas[municipio] = (np.nan, np.nan)
    return coordenadas



# Agrupar os dados por mês
df_mg_filtrado_mes = df_mg_filtrado.groupby(['municipio', 'mes']).agg({
    'casosNovos': 'sum',
    'obitosNovos': 'sum',
    'Recuperadosnovos': 'sum'
}).reset_index()

st.sidebar.markdown("[Fonte: Ministério da Saúde](https://covid.saude.gov.br/)")
st.sidebar.text("Raul Antônio Horta Campos")
st.sidebar.text("PDITA: 307")
if st.sidebar.button("Linkedin"):
    st.sidebar.markdown("[Raul Campos](https://www.linkedin.com/in/raulcampos4/)")

# Exibir o resumo dos dados filtrados em três colunas
if not df_mg_filtrado_mes.empty:
    resumo = {
        'Total de Casos Novos': [df_mg_filtrado_mes['casosNovos'].sum()],
        'Total de Óbitos': [df_mg_filtrado_mes['obitosNovos'].sum()],
        'Total de Recuperados Novos': [df_mg_filtrado_mes['Recuperadosnovos'].sum()]
    }
    resumo_df = pd.DataFrame(resumo)

#Gráficos de linha 
# Filtrar apenas os municípios selecionados
# Criar DataFrame com óbitos novos por município e mês
df_obitos_novos = df_mg_filtrado.groupby(['municipio', 'mes'])['obitosNovos'].sum().reset_index()

# Filtrar apenas os municípios selecionados
df_obitos_novos_filtrado = df_obitos_novos[df_obitos_novos['municipio'].isin(municipios_selecionados)]

# Convertendo o período para string antes de plotar o gráfico de linha
df_obitos_novos_filtrado['mes'] = df_obitos_novos_filtrado['mes'].astype(str)

# Criar o gráfico de linha
fig_linha = px.line(df_obitos_novos_filtrado, x='mes', y='obitosNovos', color='municipio')

# Adicionar título e rótulos aos eixos
fig_linha.update_layout(xaxis_title='Mês', yaxis_title='Óbitos Novos')
#------------------------------------------
#Gráfico de linha - Média
        #Aplicar o filtro aos dados antes de calcular o crescimento
df_mg_filtrado_crescimento = aplicar_filtro(df_mg, data_inicio, data_fim, municipios_selecionados)

# Converter a coluna 'data' para o formato de data
df_mg_filtrado_crescimento['data'] = pd.to_datetime(df_mg_filtrado_crescimento['data'])

# Extrair o mês e o ano de cada data e converter para string
df_mg_filtrado_crescimento['ano_mes'] = df_mg_filtrado_crescimento['data'].dt.to_period('M').astype(str)

# Agrupar os dados por mês e calcular a média dos valores de óbitos novos e casos novos
df_crescimento_mes = df_mg_filtrado_crescimento.groupby('ano_mes').agg({
            'obitosNovos': 'mean',
            'casosNovos': 'mean'
        }).reset_index()

        # Renomear a coluna 'ano_mes' para 'data' para ser compatível com o gráfico
df_crescimento_mes = df_crescimento_mes.rename(columns={'ano_mes': 'data'})

        # Criar o gráfico de linhas para o crescimento de óbitos novos
fig_obitos_novos = px.line(df_crescimento_mes, x='data', y='obitosNovos',
                                labels={'obitosNovos': 'Óbitos Novos Médios', 'data': 'Data'})
fig_obitos_novos.update_layout(yaxis_title='Quantidade Média de Óbitos Novos')

        # Criar o gráfico de linhas para o crescimento de casos novos
fig_casos_novos = px.line(df_crescimento_mes, x='data', y='casosNovos',
                                labels={'casosNovos': 'Casos Novos Médios', 'data': 'Data'})
fig_casos_novos.update_layout(yaxis_title='Quantidade Média de Casos Novos')
#-------
col1, col2, col3 = st.columns(3)

with col1:
# Exibir o total de casos novos sem casas decimais
        cartao1 = resumo_df[['Total de Casos Novos']].to_string(index=False, formatters=[lambda x: f"{x:,.0f}".replace(',', '.')])
        with st.container():
            st.subheader(cartao1)
            # Adicionar expander com inform ações para o     usuário
            with st.expander("Mais detalhes"):
                st.write("Esta tabela mostra o total de casos novos registrados no filtro selecionado.")
#--------------------
         # Exibir o mapa com casos novos por município
        # Agrupar os dados por município e calcular o total de casos novos
        agrupado_municipios = df_mg_filtrado.groupby('municipio')['casosNovos'].sum().reset_index()

        # Obter coordenadas dos municípios
        coordenadas_municipios = obter_coordenadas(agrupado_municipios['municipio'])
        agrupado_municipios['latitude'] = agrupado_municipios['municipio'].map(lambda x: coordenadas_municipios.get(x, (np.nan, np.nan))[0])
        agrupado_municipios['longitude'] = agrupado_municipios['municipio'].map(lambda x: coordenadas_municipios.get(x, (np.nan, np.nan))[1])
        # Criação do mapa
        fig = px.scatter_mapbox(
            agrupado_municipios.dropna(),
            lat="latitude",
            lon="longitude",
            size="casosNovos",
            hover_name="municipio",
            hover_data={"latitude": False, "longitude": False, "casosNovos": True},
            color="casosNovos",
            size_max=50,
            zoom=5,
            mapbox_style="carto-positron",
        )

        # Personalizando as cores dos marcadores e dos textos para aumentar o contraste
        fig.update_traces(
            marker=dict(color='green', opacity=0.7),
            selector=dict(type='scattermapbox'),
            hovertemplate="<b>%{hovertext}</b><br>Casos Novos: %{marker.size:,}<extra></extra>"
        )

        fig.update_layout(font=dict(color='white'))

        if municipios_selecionados:
            agrupado_municipios_filtrado = df_mg_filtrado.groupby('municipio')['casosNovos'].sum().reset_index()
            agrupado_municipios_filtrado['latitude'] = agrupado_municipios_filtrado['municipio'].map(lambda x: coordenadas_municipios.get(x, (np.nan, np.nan))[0])
            agrupado_municipios_filtrado['longitude'] = agrupado_municipios_filtrado['municipio'].map(lambda x: coordenadas_municipios.get(x, (np.nan, np.nan))[1])
            if not agrupado_municipios_filtrado[['latitude', 'longitude']].dropna().empty:
                avg_lat = agrupado_municipios_filtrado['latitude'].mean()
                avg_lon = agrupado_municipios_filtrado['longitude'].mean()
                fig.update_layout(mapbox_center={"lat": avg_lat, "lon": avg_lon}, mapbox_zoom=4)

        # Aplicar CSS inline para ajustar a largura do mapa
        st.write("<style>div.stPlotlyChart { width: 250px !important; }</style>", unsafe_allow_html=True)
        st.subheader("Mapa de Casos por Município🗺️")
        # Exibir detalhes do gráfico em um expander
        with st.expander("Mais detalhes"):
            st.write("Este mapa mostra a distribuição geográfica dos casos novos por município em Minas Gerais.")
            st.write("Cada ponto no mapa representa um município, sendo o tamanho do ponto proporcional ao número de casos novos.")
            st.write("Passe o mouse sobre os pontos para ver mais detalhes sobre cada município.")
        # Exibir o gráfico do mapa
        st.plotly_chart(fig)
#---------------------------------------------------------------------------------
        # Criar DataFrame com Casos novos por município e mês
        df_casos_novos = df_mg_filtrado.groupby(['municipio', 'mes'])['casosNovos'].sum().reset_index()

        # Convertendo o período para string antes de plotar o gráfico de linha
        df_casos_novos['mes'] = df_casos_novos['mes'].astype(str)

        # Criar o gráfico de linha
        fig_linha = px.line(df_casos_novos, x='mes', y='casosNovos', color='municipio', 
                            title='Casos Novos por Município ao Longo do Tempo')

        # Adicionar título e rótulos aos eixos
        fig_linha.update_layout(xaxis_title='Mês', yaxis_title='Casos Novos')

        # Exibir o gráfico de linha
        st.subheader('Casos Novos por Município ao Longo do Tempo')

        # Adicionar expander com informações para o usuário
        with st.expander("Informações sobre o Gráfico de Casos Novos por Município"):
            st.write("Este gráfico mostra a evolução do número de casos novos por município ao longo do tempo em Minas Gerais.")
            st.write("Cada linha representa um município e mostra como o número de casos novos tem variado ao longo dos meses.")
            st.write("Você pode analisar as tendências de casos novos em diferentes municípios e comparar seu comportamento ao longo do tempo.")
            st.write("Use a legenda interativa para destacar ou ocultar os dados de municípios específicos.")
        st.plotly_chart(fig_linha)
#-------------------------------------------------------------------------------  
        # Exibir o gráfico de linha
        st.subheader('Crescimento Médio de Casos ao Longo do Tempo📈')
        # Adicionar expander com informações para o usuário
        with st.expander("Mais detalhes"):
            st.write("Este gráfico mostra o crescimento médio dos casos novos ao longo do tempo em Minas Gerais.")
            st.write("Você pode observar como o número médio de casos novos tem variado ao longo dos meses conforme filtro selecionado.")
            st.write("Use esse gráfico para avaliar regiões ou conjunto de cidades.")
        st.plotly_chart(fig_casos_novos)
#------------------------------------------------------------------------------------------------------------------------------
with col2:
        with st.container():
        # Exibir o total de óbitos sem casas decimais  
            cartao2 = resumo_df[['Total de Óbitos']].to_string(index=False, formatters=[lambda x: f"{x:,.0f}".replace(',', '.')])
            st.subheader(cartao2)
            # Adicionar expander com informações para o usuário
            with st.expander("Mais detalhes"):
                st.write("Este número mostra o total de óbitos registrados no filtro selecionado.")

        # Exibir o mapa com óbitos novos por município
        # Configurar CSS inline para ajustar a largura do mapa
        st.write("<style>div.stPlotlyChart { width: 250px !important; }</style>", unsafe_allow_html=True)

        # Exibir o mapa com óbitos novos por município
        st.subheader("Mapa de Óbitos por Município🗺️")
        with st.expander("Mais detalhes"):
            st.write("Este mapa mostra a distribuição geográfica dos óbitos novos por município em Minas Gerais.")
            st.write("Cada ponto no mapa representa um município, sendo o tamanho do ponto proporcional ao número de óbitos novos.")
            st.write("Passe o mouse sobre os pontos para ver mais detalhes sobre cada município.")

        # Agrupar os dados por município e calcular o total de óbitos novos
        agrupado_municipios_obitos = df_mg_filtrado.groupby('municipio')['obitosNovos'].sum().reset_index()

        # Obter coordenadas dos municípios
        coordenadas_municipios_obitos = obter_coordenadas(agrupado_municipios_obitos['municipio'])
        agrupado_municipios_obitos['latitude'] = agrupado_municipios_obitos['municipio'].map(lambda x: coordenadas_municipios_obitos.get(x, (np.nan, np.nan))[0])
        agrupado_municipios_obitos['longitude'] = agrupado_municipios_obitos['municipio'].map(lambda x: coordenadas_municipios_obitos.get(x, (np.nan, np.nan))[1])

        # Criar o mapa de óbitos novos por município
        fig_obitos = px.scatter_mapbox(
            agrupado_municipios_obitos.dropna(),
            lat="latitude",
            lon="longitude",
            size="obitosNovos",
            hover_name="municipio",
            hover_data={"latitude": False, "longitude": False, "obitosNovos": True},
            color="obitosNovos",
            size_max=30,
            zoom=5,
            mapbox_style="carto-positron",
        )

        fig_obitos.update_traces(marker=dict(color='red', opacity=0.7), selector=dict(type='scattermapbox'),
                                hovertemplate="<b>%{hovertext}</b><br>Óbitos Novos: %{marker.size:,}<extra></extra>")
        fig_obitos.update_layout(font=dict(color='white'))

        # Ajustar o zoom do mapa de acordo com os filtros aplicados
        if municipios_selecionados:
            agrupado_municipios_obitos_filtrado = df_mg_filtrado.groupby('municipio')['obitosNovos'].sum().reset_index()
            agrupado_municipios_obitos_filtrado['latitude'] = agrupado_municipios_obitos_filtrado['municipio'].map(lambda x: coordenadas_municipios_obitos.get(x, (np.nan, np.nan))[0])
            agrupado_municipios_obitos_filtrado['longitude'] = agrupado_municipios_obitos_filtrado['municipio'].map(lambda x: coordenadas_municipios_obitos.get(x, (np.nan, np.nan))[1])
            if not agrupado_municipios_obitos_filtrado[['latitude', 'longitude']].dropna().empty:
                avg_lat_obitos = agrupado_municipios_obitos_filtrado['latitude'].mean()
                avg_lon_obitos = agrupado_municipios_obitos_filtrado['longitude'].mean()
                fig_obitos.update_layout(mapbox_center={"lat": avg_lat_obitos, "lon": avg_lon_obitos}, mapbox_zoom=7)

        # Exibir o gráfico do mapa de óbitos novos por município
        st.plotly_chart(fig_obitos)
#---------------------------------------------------------------------------
        # Exibir o gráfico de linha
        st.subheader('Óbitos Novos por Município ao Longo do Tempo📈')
        # Adicionar expander com informações para o usuário
        with st.expander("Mais detalhes"):
            st.write("Este gráfico mostra a evolução do número de óbitos novos por município ao longo do tempo em Minas Gerais.")
            st.write("Cada linha representa um município e mostra como o número de óbitos novos tem variado ao longo dos meses.")
            st.write("Você pode analisar as tendências de óbitos novos em diferentes municípios e comparar seu comportamento ao longo do tempo.")
            st.write("Use a legenda interativa para destacar ou ocultar os dados de municípios específicos.")
        st.plotly_chart(fig_linha)
#-----------------------------------------------------------------------------
        # Exibir o gráfico de linha
        st.subheader('Crescimento Médio de Óbitos ao Longo do Tempo📈')
        # Adicionar expander com informações para o usuário
        with st.expander("Mais detalhes"):
            st.write("Este gráfico mostra o crescimento médio dos óbitos novos ao longo do tempo em Minas Gerais.")
            st.write("Você pode observar como o número médio de óbitos novos tem variado ao longo dos meses conforme filtro selecionado.")
            st.write("Use esse gráfico para identificar tendências gerais no crescimento do número de óbitos em regiões ou conjunto de cidades.")
        st.plotly_chart(fig_obitos_novos)
#--------------------------------------------------------------------------------
with col3:
        with st.container():
            # Exibir o total de recuperados novos sem casas decimais
            # Gerar o texto com a formatação desejada e adicionar uma quebra de linha
            cartao3 = resumo_df[['Total de Recuperados Novos']].to_string(index=False, formatters=[lambda x: f"{x:,.0f}".replace(',', '.')])
            st.subheader(cartao3)
            # Adicionar expander com informações para o usuário
            with st.expander("Mais detalhes"):
                st.write("Valor zerado na base de dados municipais.")
                st.write("A base de dados apresenta estas informações como Estaduais.")
                st.write("Como autor, julgo importante informar a ausência destes dados.")
        
#----------------------------------------------------------------------------------------------------
        # Calcular a porcentagem de óbitos novos em relação aos casos novos para cada município
        df_medias_por_cidade = df_mg_filtrado_mes.groupby('municipio').agg({
            'obitosNovos': 'mean',
            'casosNovos': 'mean'
        }).reset_index()

        # Calcular a porcentagem de óbitos novos entre os casos novos para cada município
        df_medias_por_cidade['Porcentagem de Óbitos Entre Casos'] = (df_medias_por_cidade['obitosNovos'] / df_medias_por_cidade['casosNovos'])

        # Criar o gráfico de barras empilhadas
        fig_barras_empilhadas = px.bar(df_medias_por_cidade, x='municipio', y='Porcentagem de Óbitos Entre Casos', 
                                        color='municipio',labels={'Porcentagem de Óbitos Entre Casos': '% de Óbitos Entre Casos Novos'})

        # Adicionar título e rótulos aos eixos
        fig_barras_empilhadas.update_layout(xaxis_title='Município', yaxis_title='% de Óbitos Entre Casos Novos')

        # Formatar o número exposto no eixo y para mostrar a porcentagem
        fig_barras_empilhadas.update_yaxes(tickformat=".2%")

    # Exibir o gráfico de barras empilhadas
        st.subheader('% de Óbitos Entre Casos Novos📊')
        with st.expander("Mais detalhes"):
            st.write("Este gráfico de barras empilhadas mostra a % de óbitos em relação aos casos novos ao longo do tempo.")
            st.write("Ele oferece insights sobre a letalidade da COVID-19 em diferentes períodos.")
            st.write("Analise as variações ao longo do tempo para entender melhor o impacto da pandemia em Minas Gerais.")
        st.plotly_chart(fig_barras_empilhadas)
        # Adicionar expander com dicas importantes sobre o site
        with st.expander("Dicas Importantes sobre o Site"):
            st.write("1. Utilize os filtros na barra lateral para refinar a visualização dos dados de acordo com suas necessidades.")
            st.write("2. Passe o mouse sobre os elementos gráficos para obter mais informações detalhadas.")
            st.write("3. Explore as diferentes seções do site para visualizar diferentes aspectos dos dados relacionados à COVID-19 em Minas Gerais.")
            st.write("4. Caso tenha alguma dúvida ou sugestão, não hesite em entrar em contato através do Linkedin ou Github.")
            st.info("""
            - **Visualização Simultânea:** Para melhor visualização de várias cidades simultaneamente, clique nas setas no canto superior direito do gráfico/tabela.
            - **Comparação de Dados:** Ao comparar dados de cidades de pequeno e grande porte, os números absolutos podem gerar diferenças gritantes. Considere isso ao selecionar as comparações.
            - **Valores Zerados:** Médias e porcentagens podem ser zeradas dependendo dos valores avaliados.
    """)

#-------------Fim das Colunas
# Alterar os nomes das colunas
df_mg_filtrado_mes = df_mg_filtrado_mes.rename(columns={
    'municipio': 'Município',
    'mes':'Mês',
    'casosNovos': 'Casos Novos',
    'obitosNovos': 'Óbitos Novos',
    'Recuperadosnovos': 'Recuperados Novos'
})

# Exibir a tabela de dados filtrados com títulos mais amigáveis
st.write(df_mg_filtrado_mes)