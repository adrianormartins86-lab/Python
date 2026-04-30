import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz
import os

# --- CONFIGURAÇÃO E LOGO ---
USER_GITHUB = "adrianormartins86-lab"
REPO_GITHUB = "Python"
NOME_IMAGEM = "passaro_logo.png"
URL_ICONE = f"https://raw.githubusercontent.com/{USER_GITHUB}/{REPO_GITHUB}/main/{NOME_IMAGEM}"

st.set_page_config(page_title="Check-in Promotores", layout="centered", page_icon=URL_ICONE)

# Cabeçalho
col1, col2 = st.columns([1, 5])
with col1:
    try: st.image(URL_ICONE, width=100)
    except: st.write("🐦")
with col2:
    st.title("Visita Promotores")

st.markdown("---")

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data
def carregar_fornecedores():
    arquivo = 'fornecedores.xlsx'
    if os.path.exists(arquivo):
        try:
            # Carregando a base nova
            df = pd.read_excel(arquivo, engine='openpyxl').dropna(how='all')
            df.columns = [str(col).strip() for col in df.columns]
            return df
        except Exception as e:
            st.error(f"Erro ao ler Excel: {e}")
    return None

df_forn = carregar_fornecedores()

if df_forn is not None:
    # Identificação das colunas baseada na sua nova imagem (A: ID, B: Empresa, G: Frequência, S: Loja)
    col_empresa = df_forn.columns[1]  # Coluna B
    col_frequencia = df_forn.columns[6] # Coluna G
    col_loja = df_forn.columns[-1]    # Última Coluna

    # 1. Seleção da Loja
    lojas = sorted(df_forn[col_loja].dropna().astype(str).unique().tolist())
    loja_sel = st.selectbox("1. Selecione a Loja:", ["Escolha..."] + lojas)

    if loja_sel != "Escolha...":
        filtro = df_forn[df_forn[col_loja].astype(str) == loja_sel]
        fornecedores = sorted(filtro[col_empresa].dropna().astype(str).unique().tolist())
        forn_sel = st.selectbox("2. Selecione o Fornecedor:", ["Escolha..."] + fornecedores)

        if forn_sel != "Escolha...":
            # --- EXIBIÇÃO DA FREQUÊNCIA (INCREMENTO) ---
            dados_sel = filtro[filtro[col_empresa] == forn_sel]
            frequencia = dados_sel[col_frequencia].iloc[0]
            st.info(f"📅 **Frequência Programada:** {frequencia}")
            
            # 2. Observações
            obs = st.text_input("3. Observação (Opcional):", placeholder="Ex: Gôndola organizada...")

            # 3. UPLOAD DE FOTO
            st.markdown("### 📸 Registro Fotográfico")
            foto = st.file_uploader("Selecione ou tire uma foto", type=["jpg", "jpeg", "png"])
            
            if foto:
                st.image(foto, caption="Prévia da foto", width=200)

            # 4. BOTÃO DE CONFIRMAÇÃO
            if st.button("Confirmar Check-in", use_container_width=True):
                try:
                    fuso_br = pytz.timezone('America/Sao_Paulo')
                    agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
                    
                    df_existente = conn.read(ttl=0) 
                    
                    # Nome do arquivo da foto para salvar no Sheets
                    nome_foto = foto.name if foto else "Sem foto"
                    
                    novo_dado = pd.DataFrame([{
                        "Data": agora, 
                        "Loja": loja_sel, 
                        "Fornecedor": forn_sel,
                        "Frequencia": frequencia, # Salvando a frequência no log
                        "Observacao": obs,
                        "Arquivo_Foto": nome_foto # Nome da foto no registro
                    }])
                    
                    df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
                    conn.update(data=df_final)
                    
                    st.success(f"✅ Registrado com sucesso às {agora}!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
else:
    st.info("Aguardando arquivo de fornecedores...")
