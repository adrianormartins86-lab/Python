import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz
import os

# Configuração da página
st.set_page_config(page_title="Check-in Promotores", layout="centered", page_icon="📲")

st.title("📲 Molicenter - Registro de Visitas Promotores")

# Conexão com Google Sheets
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
    col_empresa = df_forn.columns[1]
    col_loja = df_forn.columns[-1]

    lojas = sorted(df_forn[col_loja].dropna().astype(str).unique().tolist())
    loja_sel = st.selectbox("1. Selecione a Loja:", ["Escolha..."] + lojas)

    if loja_sel != "Escolha...":
        filtro = df_forn[df_forn[col_loja].astype(str) == loja_sel]
        fornecedores = sorted(filtro[col_empresa].dropna().astype(str).unique().tolist())
        forn_sel = st.selectbox("2. Selecione o Fornecedor:", ["Escolha..."] + fornecedores)
        
        obs = st.text_input("3. Observação (Opcional):", placeholder="Ex: Falta de estoque...")

        if forn_sel != "Escolha...":
            if st.button("Confirmar Check-in", use_container_width=True):
                try:
                    # 1. Ajuste do Fuso Horário para Brasília
                    fuso_br = pytz.timezone('America/Sao_Paulo')
                    agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
                    
                    # 2. Forçamos a leitura da planilha ignorando o cache para ver o que já existe
                    df_existente = conn.read(ttl=0) 
                    
                    # 3. Cria o novo registro
                    novo_dado = pd.DataFrame([{
                        "Data": agora, 
                        "Loja": loja_sel, 
                        "Fornecedor": forn_sel,
                        "Observacao": obs 
                    }])
                    
                    # 4. Empilhamento garantido (Append)
                    # Se a planilha estiver vazia, ele apenas usa o novo_dado
                    if df_existente.empty:
                        df_final = novo_dado
                    else:
                        df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
                    
                    # 5. Atualiza a planilha (isso escreve todo o bloco de volta)
                    conn.update(data=df_final)
                    
                    st.success(f"✅ Registrado com sucesso às {agora}!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
else:
    st.info("Aguardando arquivo de fornecedores no GitHub...")
