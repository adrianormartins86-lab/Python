import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Check-in Promotores", layout="centered")

st.title("📲 Registro de Visitas")

# Função com cache para não travar o app
@st.cache_data
def carregar_dados():
    # Tenta achar o arquivo independente de maiúsculas/minúsculas na pasta
    arquivo_alvo = 'fornecedores.xlsx'
    caminho_real = None
    
    for f in os.listdir('.'):
        if f.lower() == arquivo_alvo:
            caminho_real = f
            break
            
    if caminho_real:
        try:
            # Forçamos o motor openpyxl que você colocou no requirements.txt
            df = pd.read_excel(caminho_real, engine='openpyxl').dropna(how='all')
            # Limpeza das colunas
            df.columns = [str(col).strip() for col in df.columns]
            return df
        except Exception as e:
            st.error(f"Erro ao ler o Excel: {e}")
    return None

df = carregar_dados()

if df is not None:
    # Usamos a lógica de posição que você pediu: 2ª coluna e Última
    col_empresa = df.columns[1]  
    col_loja = df.columns[-1]    

    lojas = sorted(df[col_loja].dropna().astype(str).unique().tolist())
    loja_sel = st.selectbox("1. Selecione a Loja:", ["Escolha..."] + lojas)

    if loja_sel != "Escolha...":
        filtro = df[df[col_loja].astype(str) == loja_sel]
        fornecedores = sorted(filtro[col_empresa].dropna().astype(str).unique().tolist())
        forn_sel = st.selectbox("2. Selecione o Fornecedor:", ["Escolha..."] + fornecedores)

        if forn_sel != "Escolha...":
            if st.button("Confirmar Check-in", use_container_width=True):
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                # Criamos o registro
                registro = pd.DataFrame([{'Data': agora, 'Loja': loja_sel, 'Fornecedor': forn_sel}])
                
                # No Streamlit Cloud, salvamos temporariamente
                arquivo_saida = 'banco_de_dados.csv'
                registro.to_csv(arquivo_saida, mode='a', index=False, 
                               header=not os.path.exists(arquivo_saida), 
                               sep=';', encoding='utf-8-sig')
                
                st.success(f"✅ Registrado: {forn_sel}")
                st.balloons()
else:
    st.error("⚠️ O arquivo 'fornecedores.xlsx' não foi encontrado no seu GitHub.")
    st.info(f"Arquivos detectados na pasta: {os.listdir('.')}")
