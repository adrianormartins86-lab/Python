import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import os

st.set_page_config(page_title="Check-in Promotores", layout="centered")

st.title("📲 Registro de Visitas (Cloud)")

# Inicializa a conexão com o Google Sheets
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
            st.error(f"Erro ao ler fornecedores: {e}")
    return None

df_forn = carregar_fornecedores()

if df_forn is not None:
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
                # 1. Obter data e hora
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                # 2. Ler os dados atuais da Planilha Google para não sobrescrever
                # (Troque a URL abaixo pela URL da sua planilha)
                url_planilha = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"
                
                try:
                    df_existente = conn.read(spreadsheet=url_planilha)
                    novo_dado = pd.DataFrame([{"Data": agora, "Loja": loja_sel, "Fornecedor": forn_sel}])
                    df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
                    
                    # 3. Salvar de volta na Google Sheets
                    conn.update(spreadsheet=url_planilha, data=df_final)
                    
                    st.success(f"✅ Registrado no Google Sheets: {forn_sel}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar na nuvem: {e}")
else:
    st.info("Aguardando arquivo de fornecedores...")
