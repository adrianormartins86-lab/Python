import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import os

st.set_page_config(page_title="Check-in Promotores", layout="centered")

st.title("📲 Registro de Visitas")

# 1. Ligação simplificada (ele vai buscar a URL direto ao Secret)
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
    # Lógica de colunas (2ª e Última)
    col_empresa = df_forn.columns[1]
    col_loja = df_forn.columns[-1]

    lojas = sorted(df_forn[col_loja].dropna().astype(str).unique().tolist())
    loja_sel = st.selectbox("1. Selecione a Loja:", ["Escolha..."] + lojas)

    if loja_sel != "Escolha...":
        filtro = df_forn[df_forn[col_loja].astype(str) == loja_sel]
        fornecedores = sorted(filtro[col_empresa].dropna().astype(str).unique().tolist())
        forn_sel = st.selectbox("2. Selecione o Fornecedor:", ["Escolha..."] + fornecedores)

        if forn_sel != "Escolha...":
            if st.button("Confirmar Check-in", use_container_width=True):
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                try:
                    # Lê os dados atuais da Google Sheet definida no Secret
                    df_existente = conn.read() 
                    
                    novo_dado = pd.DataFrame([{"Data": agora, "Loja": loja_sel, "Fornecedor": forn_sel}])
                    df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
                    
                    # Atualiza a folha de cálculo
                    conn.update(data=df_final)
                    
                    st.success(f"✅ Registado na Nuvem: {forn_sel}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro de Conexão: Verifique se a planilha está como 'Editor' para todos com o link. (Detalhe: {e})")
else:
    st.info("Aguardando ficheiro de fornecedores...")
