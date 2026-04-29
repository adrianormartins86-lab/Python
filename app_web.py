import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz
import os

# --- CONFIGURAÇÃO VISUAL E DO ÍCONE ---
# Substitua os valores abaixo pelo seu usuário e nome do repositório para o link da imagem funcionar
USER_GITHUB = "adrianormartins86-lab"
REPO_GITHUB = "Python"
NOME_IMAGEM = "passaro_logo.png"

# Link direto para a imagem no GitHub
URL_ICONE = f"https://raw.githubusercontent.com/{USER_GITHUB}/{REPO_GITHUB}/main/{NOME_IMAGEM}"

st.set_page_config(
    page_title="Check-in Promotores", 
    layout="centered", 
    page_icon=URL_ICONE
)

# Cabeçalho com o Logótipo do Pássaro
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image(URL_ICONE, width=80)
    except:
        st.write("🐦") # Backup caso a imagem falhe

with col2:
    st.title("Registro de Visitas")

st.markdown("---")

# --- CONEXÃO E LÓGICA DE DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data
def carregar_fornecedores():
    arquivo = 'fornecedores.xlsx'
    if os.path.exists(arquivo):
        try:
            df = pd.read_excel(arquivo, engine='openpyxl').dropna(how='all')
            df.columns = [str(col).strip() for col in df.columns]
            return df
        except Exception as e:
            st.error(f"Erro ao ler Excel: {e}")
    return None

df_forn = carregar_fornecedores()

if df_forn is not None:
    # Lógica de colunas: 2ª (Fornecedor) e Última (Loja)
    col_empresa = df_forn.columns[1]
    col_loja = df_forn.columns[-1]

    # Interface de seleção
    lojas = sorted(df_forn[col_loja].dropna().astype(str).unique().tolist())
    loja_sel = st.selectbox("1. Selecione a Loja:", ["Escolha..."] + lojas)

    if loja_sel != "Escolha...":
        filtro = df_forn[df_forn[col_loja].astype(str) == loja_sel]
        fornecedores = sorted(filtro[col_empresa].dropna().astype(str).unique().tolist())
        forn_sel = st.selectbox("2. Selecione o Fornecedor:", ["Escolha..."] + fornecedores)
        
        obs = st.text_input("3. Observação (Opcional):", placeholder="Ex: Falta de estoque, gôndola cheia...")

        if forn_sel != "Escolha...":
            if st.button("Confirmar Check-in", use_container_width=True):
                try:
                    # Ajuste de Horário para Brasília (UTC-3)
                    fuso_br = pytz.timezone('America/Sao_Paulo')
                    agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
                    
                    # Lê os dados atuais da Google Sheet (sem cache para evitar sobreposição)
                    df_existente = conn.read(ttl=0) 
                    
                    # Novo registro alinhado com as colunas da planilha
                    novo_dado = pd.DataFrame([{
                        "Data": agora, 
                        "Loja": loja_sel, 
                        "Fornecedor": forn_sel,
                        "Observacao": obs 
                    }])
                    
                    # Empilha os dados (Append)
                    if df_existente.empty:
                        df_final = novo_dado
                    else:
                        df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
                    
                    # Atualiza a planilha na nuvem
                    conn.update(data=df_final)
                    
                    st.success(f"✅ Registado com sucesso às {agora}!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
else:
    st.info("Aguardando arquivo de fornecedores no GitHub...")
