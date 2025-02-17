import streamlit as st
import pandas as pd
import plotly.express as px
import uuid

# Função para carregar e processar os dados, com cache
@st.cache_data
def load_data_from_github():
    # URLs dos arquivos no formato raw
    url_base = "https://github.com/kauanpscode/basescorandini/raw/refs/heads/main/base_3meses.xlsx"
    url_fcr = "https://github.com/kauanpscode/basescorandini/raw/refs/heads/main/fcr.xlsx"

    # Carregar o arquivo Excel
    df = pd.read_excel(url_base, engine='openpyxl')
    df_fcr = pd.read_excel(url_fcr, engine='openpyxl')
    return df, df_fcr

def load_data():
    df, df_fcr = load_data_from_github()

    # Processamento dos dados
    df_fcr['temacategoriaassunto'] = df_fcr['temacategoriaassunto'].fillna('').str.lower()
    df_fcr = df_fcr.drop_duplicates(subset=['temacategoriaassunto'])

    df['topic'] = df['topic'].fillna('').astype(str)
    df['category'] = df['category'].fillna('').astype(str)
    df['subject'] = df['subject'].fillna('').astype(str)
    df['channel_order_code'] = df['channel_order_code'].fillna('').astype(str)
    df['branded_store_slug'] = df['branded_store_slug'].fillna('').astype(str)
    df['reason'] = df['reason'].fillna('').astype(str)

    df['temacategoriaassunto'] = df['topic'].str.lower() + df['category'].str.lower() + df['subject'].str.lower()

    df = pd.merge(df, df_fcr, on='temacategoriaassunto', how='left')
    df['interacoes'] = df['interacoes'].fillna(1)

    df['interacao_buyer'] = df['outcome'].apply(lambda x: 1 if x == "Interação com o buyer" else 0)

    df['diferenca_data'] = (df['service_date'] - df['due_date']).dt.days
    df['sla'] = df['diferenca_data'].apply(lambda x: 1 if x < 0 else 0)
    df['data'] = df['service_date'].dt.date

    df['filtro_fcr'] = df.apply(
        lambda row: 1 if row['subtype'] in ['Mensageria', 'Reclamação', 'Mediação'] and row['outcome'] == 'Interação com o buyer' else 0,
        axis=1
    )

    mapping = {
        'carrefourIndisponível': 'carrefour',
        'vtex_bancointerIndisponível': 'vtex_bancointer',
        'amazonIndisponível': 'amazon',
        'magazineluizaIndisponível': 'magazineluiza',
        'cnovaIndisponível': 'cnova',
        'madeiramadeiraIndisponível': 'madeiramadeiramsg',
        'b2wIndisponível': 'b2w',
        'amazonReclamação': 'amazon',
        'b2wReclamação': 'b2w',
        'carrefourReclamação': 'carrefour',
        'madeiramadeiraMensageria': 'madeiramadeiramsg',
        'madeiramadeiraReclamação': 'madeiramadeirasac',
        'magazineluizaReclamação': 'magazineluiza',
        'vtex_bancointerReclamação': 'vtex_bancointer',
        'cnovaReclamação': 'cnova',
        'magazineluizaAcompanhamento': 'magazineluiza',
        'mercadolivreMensageria': 'mercadolivremsg',
        'mercadolivreReclamação': 'mercadolivrerec',
        'mercadolivreMediação': 'mercadolivremed',
        'mercadolivreAcompanhamento': 'mercadolivremsg',
        'carrefourAcompanhamento': 'carrefour',
        'cnovaAcompanhamento': 'cnova',
        'mercadolivreAcompannhamento': 'mercadolivremsg',
        'cnovaDemandas Extras': 'cnova',
        'b2wAcompanhamento': 'b2w',
        'madeiramadeiraAcompanhamento': 'madeiramadeiramsg',
        'amazonAcompanhamento': 'amazon',
        "amazonDemandas Extras": "amazon",
        "carrefourDemandas Extras":"carrefour",
        "mercadolivreDemandas Extras":"mercadolivremsg",
        "vtex_bancointerDemandas Extras":"vtex_bancointer"    
    }

    df['channel_subtype'] = df['channel_slug'].fillna('') + df['subtype'].fillna('')
    df['canal_tratado'] = df['channel_subtype'].map(mapping)

    df['temacategoriaassunto_PPL'] = df['temacategoriaassunto'].fillna('') + df['channel_order_code'] + df['branded_store_slug'] + df['reason'] + df['canal_tratado']

    df.loc[df['filtro_fcr'] != 1, 'temacategoriaassunto_PPL'] = ''

    df['contagem_progressiva'] = df.groupby('temacategoriaassunto_PPL').cumcount() + 1

    df['calculo_fcr'] = df.apply(
        lambda row: '' if row['filtro_fcr'] == 0 else ('Não' if row['contagem_progressiva'] > row['interacoes'] else 'Sim'),
        axis=1
    )

    # Garantir que service_date esteja no formato datetime
    df['service_date'] = pd.to_datetime(df['service_date'], errors='coerce')

    # Criar uma nova coluna para o mês de service_date
    df['mes_service_date'] = df['service_date'].dt.to_period('M')

    return df

# Carregar os dados
df = load_data()

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

# Filtro dinâmico: permite selecionar o mês disponível na barra lateral
meses_disponiveis = sorted(df['mes_service_date'].dropna().unique())
mes_filtro = st.sidebar.selectbox("Selecione o mês", options=meses_disponiveis, format_func=lambda x: str(x), key="mes_filtro")
df_filtrado = df[df['mes_service_date'] == mes_filtro]

def plot_table_chart(title, data, column):
    st.subheader(title)
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(data, use_container_width=True)
    with col2:
        fig = px.pie(df_filtrado, names=column, title=f'')
        st.plotly_chart(fig, use_container_width=True , key=uuid.uuid4())

st.title("Análise de Temas, Categorias e Assuntos")

# Relatórios existentes
plot_table_chart("Tema", df_filtrado['topic'].value_counts().reset_index().rename(columns={'index': 'Tema', 'topic': 'Contagem'}), 'topic')
plot_table_chart("Categoria", df_filtrado['category'].value_counts().reset_index().rename(columns={'index': 'Categoria', 'category': 'Contagem'}), 'category')
plot_table_chart("Assunto", df_filtrado['subject'].value_counts().reset_index().rename(columns={'index': 'Assunto', 'subject': 'Contagem'}), 'subject')

# Gráfico de Série Temporal: evolução das interações por dia
st.subheader("Interações por Dia")
df_temporal = df_filtrado.groupby('data').size().reset_index(name='Contagem')
fig_line = px.line(df_temporal, x='data', y='Contagem', text='Contagem',title="Número de Interações por Dia")
fig_line.update_traces(textposition='top center')  # Posiciona os rótulos acima das barras
st.plotly_chart(fig_line, use_container_width=True, key=uuid.uuid4())

# Análise de FCR: gráfico de barras resumindo os resultados
if 'calculo_fcr' in df.columns:
    st.title("Análise de FCR - Fora do FCR")
    df_nao_fcr = df_filtrado[df_filtrado['calculo_fcr'] == 'Não']
    plot_table_chart("Tema", df_nao_fcr['topic'].value_counts().reset_index().rename(columns={'index': 'Tema', 'topic': 'Contagem'}), 'topic')
    plot_table_chart("Categoria", df_nao_fcr['category'].value_counts().reset_index().rename(columns={'index': 'Categoria', 'category': 'Contagem'}), 'category')
    plot_table_chart("Assunto", df_nao_fcr['subject'].value_counts().reset_index().rename(columns={'index': 'Assunto', 'subject': 'Contagem'}), 'subject')
    
    st.subheader("Quantidade geral - Fora do FCR")
    df_fcr_counts = df_filtrado[df_filtrado['calculo_fcr'] != '']['calculo_fcr'].value_counts().reset_index()
    df_fcr_counts.columns = ['FCR Status', 'Contagem']
    fig_bar = px.bar(df_fcr_counts, x='FCR Status', y='Contagem', text='Contagem', title="Contagem de FCR")

    st.plotly_chart(fig_bar, use_container_width=True, key=uuid.uuid4())
else:
    st.error("Erro: A coluna 'calculo_fcr' não foi encontrada no DataFrame!")
