import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Check-in Promotores", layout="centered")

# Estilização básica
st.title("📲 Registro de Visitas")
st.markdown("---")

def carregar_dados():
    arquivo = 'fornecedores.xlsx'
    if os.path.exists(arquivo):
        try:
            df = pd.read_excel(arquivo).dropna(how='all')
            return df
        except Exception as e:
            st.error(f"Erro ao ler Excel: {e}")
    return None

df = carregar_dados()

if df is not None:
    # Identifica as colunas por posição
    col_empresa = df.columns[1]  # 2ª coluna
    col_loja = df.columns[-1]     # Última coluna

    # 1. Seleção da Loja
    lojas = sorted(df[col_loja].dropna().astype(str).unique().tolist())
    loja_sel = st.selectbox("Selecione a Unidade (Loja):", ["Escolha..."] + lojas)

    if loja_sel != "Escolha...":
        # 2. Seleção do Fornecedor filtrado
        filtro = df[df[col_loja].astype(str) == loja_sel]
        fornecedores = sorted(filtro[col_empresa].dropna().astype(str).unique().tolist())
        forn_sel = st.selectbox("Selecione o Fornecedor:", ["Escolha..."] + fornecedores)

        if forn_sel != "Escolha...":
            if st.button("Confirmar Check-in", use_container_width=True):
                # Registro dos dados
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                novo_registro = pd.DataFrame([{'Data': agora, 'Loja': loja_sel, 'Fornecedor': forn_sel}])
                
                arquivo_saida = 'banco_de_dados.csv'
                # Salva no arquivo CSV
                novo_registro.to_csv(arquivo_saida, mode='a', index=False, 
                                   header=not os.path.exists(arquivo_saida), 
                                   sep=';', encoding='utf-8-sig')
                
                st.success(f"✅ Check-in de {forn_sel} realizado com sucesso!")
                st.balloons()
else:
    st.warning("⚠️ Arquivo 'fornecedores.xlsx' não encontrado na pasta.")

st.markdown("---")
st.caption("Sistema de Controle de Promotores v2.0")