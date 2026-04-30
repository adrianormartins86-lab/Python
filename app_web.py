import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz
import os
import requests
import base64

# --- CONFIGURAÇÃO E LOGO ---
USER_GITHUB = "adrianormartins86-lab"
REPO_GITHUB = "Python"
NOME_IMAGEM = "passaro_logo.png"
URL_ICONE = f"https://raw.githubusercontent.com/{USER_GITHUB}/{REPO_GITHUB}/main/{NOME_IMAGEM}"

st.set_page_config(page_title="Check-in Promotores", layout="centered", page_icon=URL_ICONE)

# --- FUNÇÃO DE UPLOAD PARA O IMGBB (SOLUÇÃO DEFINITIVA) ---
def upload_para_imgbb(arquivo_foto):
    """Faz o upload para o ImgBB e retorna o link direto da imagem"""
    try:
        api_key = st.secrets["imgbb"]["api_key"]
        url = "https://api.imgbb.com/1/upload"
        
        # Converte a imagem para Base64 (formato que a API aceita)
        foto_base64 = base64.b64encode(arquivo_foto.getvalue()).decode('utf-8')
        
        payload = {
            "key": api_key,
            "image": foto_base64,
        }
        
        response = requests.post(url, payload)
        resultado = response.json()
        
        if resultado['success']:
            # Retorna a URL direta da imagem (perfeita para o Power BI)
            return resultado['data']['url']
        else:
            st.error(f"Erro na API do ImgBB: {resultado['error']['message']}")
            return "Erro no Upload"
    except Exception as e:
        st.error(f"⚠️ Erro ao conectar com ImgBB: {e}")
        return "Erro no Upload"

# --- CABEÇALHO ---
col1, col2 = st.columns([1, 5])
with col1:
    try: st.image(URL_ICONE, width=100)
    except: st.write("🐦")
with col2:
    st.title("Visita Promotores")

st.markdown("---")

# --- CONEXÃO E CARREGAMENTO ---
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
    col_frequencia = df_forn.columns[6] 
    col_loja = df_forn.columns[-1]    

    loja_sel = st.selectbox("1. Selecione a Loja:", ["Escolha..."] + sorted(df_forn[col_loja].dropna().astype(str).unique().tolist()))

    if loja_sel != "Escolha...":
        filtro = df_forn[df_forn[col_loja].astype(str) == loja_sel]
        fornecedores = sorted(filtro[col_empresa].dropna().astype(str).unique().tolist())
        forn_sel = st.selectbox("2. Selecione o Fornecedor:", ["Escolha..."] + fornecedores)

        if forn_sel != "Escolha...":
            dados_sel = filtro[filtro[col_empresa] == forn_sel]
            frequencia = dados_sel[col_frequencia].iloc[0]
            st.info(f"📅 **Frequência Programada:** {frequencia}")
            
            obs = st.text_input("3. Observação (Opcional):")

            st.markdown("### 📸 Registro Fotográfico")
            foto = st.file_uploader("Selecione ou tire uma foto", type=["jpg", "jpeg", "png"])
            
            if foto:
                st.image(foto, caption="Prévia da foto", width=200)

            if st.button("Confirmar Check-in", use_container_width=True):
                if foto is None:
                    st.warning("⚠️ Por favor, anexe uma foto antes de confirmar.")
                else:
                    try:
                        fuso_br = pytz.timezone('America/Sao_Paulo')
                        agora_str = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
                        
                        with st.spinner('🚀 Enviando imagem e salvando check-in...'):
                            link_final_foto = upload_para_imgbb(foto)
                        
                        if link_final_foto != "Erro no Upload":
                            df_existente = conn.read(ttl=0) 
                            
                            novo_dado = pd.DataFrame([{
                                "Data": agora_str, 
                                "Loja": loja_sel, 
                                "Fornecedor": forn_sel,
                                "Frequencia": frequencia,
                                "Observacao": obs,
                                "Arquivo_Foto": link_final_foto 
                            }])
                            
                            df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
                            conn.update(data=df_final)
                            
                            st.success(f"✅ Registrado com sucesso!")
                            st.balloons()
                        else:
                            st.error("❌ Falha no upload. O registro não foi salvo.")
                            
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {e}")
else:
    st.info("Aguardando arquivo de fornecedores...")
