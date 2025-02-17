import streamlit as st
import pandas as pd
import plotly.express as px

# Função para carregar e processar os dados, com cache
@st.cache_data
def load_data_from_github():
    url_base = "https://github.com/kauanpscode/basescorandini/raw/refs/heads/main/base_3meses.xlsx"
    url_fcr = "https://github.com/kauanpscode/basescorandini/raw/refs/heads/main/fcr.xlsx"
    df = pd.read_excel(url_base, engine='openpyxl')
    df_fcr = pd.read_excel(url_fcr, engine='openpyxl')
    return df, df_fcr

def load_data():
    df, df_fcr = load_data_from_github()
    df_fcr['temacategoriaassunto'] = df_fcr['temacategoriaassunto'].fillna('').str.lower()
    df_fcr = df_fcr.drop_duplicates(subset=['temacategoriaassunto'])
    df['topic'] = df['topic'].fillna('').astype(str)
    df['category'] = df['category'].fillna('').astype(str)
    df['subject'] = df['subject'].fillna('').astype(str)
    df['service_date'] = pd.to_datetime(df['service_date'], errors='coerce')
    df['data'] = df['service_date'].dt.date
    df['calculo_fcr'] = df['calculo_fcr'].fillna('')  # Garante que não haja valores NaN
    return df

# Carregar os dados
df = load_data()

def plot_table_chart(title, data, column, key):
    st.subheader(title)
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(data, use_container_width=True)
    with col2:
        fig = px.pie(df_filtrado, names=column, title=title)
        st.plotly_chart(fig, use_container_width=True, key=key)

st.title("Análise de Temas, Categorias e Assuntos")
meses_disponiveis = sorted(df['service_date'].dropna().dt.to_period('M').unique())
mes_filtro = st.sidebar.selectbox("Selecione o mês", options=meses_disponiveis, format_func=lambda x: str(x))
df_filtrado = df[df['service_date'].dt.to_period('M') == mes_filtro]

# Gráfico de Interações por Dia
st.subheader("Interações por Dia")
df_temporal = df_filtrado.groupby('data').size().reset_index(name='Contagem')
fig_line = px.line(df_temporal, x='data', y='Contagem', text='Contagem', title="Número de Interações por Dia")
fig_line.update_traces(textposition='top center')
st.plotly_chart(fig_line, use_container_width=True, key="interacoes_dia")

# Análise de FCR
if 'calculo_fcr' in df.columns:
    st.title("Análise de FCR - Fora do FCR")
    df_nao_fcr = df_filtrado[df_filtrado['calculo_fcr'] == 'Não']
    plot_table_chart("Tema", df_nao_fcr['topic'].value_counts().reset_index().rename(columns={'index': 'Tema', 'topic': 'Contagem'}), 'topic', key="tema_fcr")
    plot_table_chart("Categoria", df_nao_fcr['category'].value_counts().reset_index().rename(columns={'index': 'Categoria', 'category': 'Contagem'}), 'category', key="categoria_fcr")
    plot_table_chart("Assunto", df_nao_fcr['subject'].value_counts().reset_index().rename(columns={'index': 'Assunto', 'subject': 'Contagem'}), 'subject', key="assunto_fcr")
    
    st.subheader("Quantidade geral - Fora do FCR")
    df_fcr_counts = df_filtrado[df_filtrado['calculo_fcr'] != '']['calculo_fcr'].value_counts().reset_index()
    df_fcr_counts.columns = ['FCR Status', 'Contagem']
    fig_bar = px.bar(df_fcr_counts, x='FCR Status', y='Contagem', text='Contagem', title="Contagem de FCR")
    st.plotly_chart(fig_bar, use_container_width=True, key="fcr_status")
else:
    st.error("Erro: A coluna 'calculo_fcr' não foi encontrada no DataFrame!")
