import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import os

st.set_page_config(page_title="Check-in Promotores", layout="centered")

st.title("📲 Registro de Visitas")

# Conexão com Google Sheets (usando os Secrets que você já salvou)
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
    # Lógica de colunas: 2ª (Empresa) e Última (Loja)
    col_empresa = df_forn.columns[1]
    col_loja = df_forn.columns[-1]

    lojas = sorted(df_forn[col_loja].dropna().astype(str).unique().tolist())
    loja_sel = st.selectbox("1. Selecione a Loja:", ["Escolha..."] + lojas)

    if loja_sel != "Escolha...":
        filtro = df_forn[df_forn[col_loja].astype(str) == loja_sel]
        fornecedores = sorted(filtro[col_empresa].dropna().astype(str).unique().tolist())
        forn_sel = st.selectbox("2. Selecione o Fornecedor:", ["Escolha..."] + fornecedores)
        
        # --- NOVO CAMPO DE OBSERVAÇÃO ---
        obs = st.text_input("3. Observação (Opcional):", placeholder="Ex: Falta de estoque, gôndola cheia...")

        if forn_sel != "Escolha...":
            if st.button("Confirmar Check-in", use_container_width=True):
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                try:
                    # Lê os dados atuais da Google Sheet
                    df_existente = conn.read() 
                    
                    # Cria o novo registro incluindo a observação
                    novo_dado = pd.DataFrame([{
                        "Data": agora, 
                        "Loja": loja_sel, 
                        "Fornecedor": forn_sel,
                        "Observacao": obs  # Salva o que foi digitado
                    }])
                    
                    df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
                    
                    # Atualiza a planilha na nuvem
                    conn.update(data=df_final)
                    
                    st.success(f"✅ Registrado: {forn_sel}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
else:
    st.info("Aguardando arquivo de fornecedores no GitHub...")
