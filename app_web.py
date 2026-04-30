import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# --- CONFIGURAÇÃO E LOGO ---
USER_GITHUB = "adrianormartins86-lab"
REPO_GITHUB = "Python"
NOME_IMAGEM = "passaro_logo.png"
URL_ICONE = f"https://raw.githubusercontent.com/{USER_GITHUB}/{REPO_GITHUB}/main/{NOME_IMAGEM}"

st.set_page_config(page_title="Check-in Promotores", layout="centered", page_icon=URL_ICONE)

# --- FUNÇÃO DE UPLOAD PARA O GOOGLE DRIVE ---
def upload_para_drive(arquivo_foto, nome_arquivo):
    """Faz o upload para o Drive e retorna o link direto para o Power BI"""
    try:
        # Autenticação (Requer arquivo settings.yaml ou credentials configuradas)
        gauth = GoogleAuth()
        drive = GoogleDrive(gauth)
        
        # ID da pasta 'Fotos_Checkin' que você criou no seu Drive
        ID_PASTA_DRIVE = "https://drive.google.com/drive/folders/1VSrgXLR9nKtVclapeZWHkV_ojK55_JtO?usp=drive_link" 
        
        file_drive = drive.CreateFile({
            'title': nome_arquivo,
            'parents': [{'id': ID_PASTA_DRIVE}]
        })
        
        # O Streamlit file_uploader retorna um BytesIO, precisamos ler o conteúdo
        file_drive.SetContentString(arquivo_foto.getvalue()) # Para arquivos binários use SetContentFile se for local
        # Correção para binários no Streamlit:
        arquivo_foto.seek(0)
        file_drive.content = arquivo_foto
        
        file_drive.Upload()
        
        # Gera o link de visualização direta (webContentLink) para o Power BI
        return file_drive['webContentLink']
    except Exception as e:
        st.error(f"Erro no upload para o Drive: {e}")
        return "Erro no Upload"

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
                try:
                    fuso_br = pytz.timezone('America/Sao_Paulo')
                    agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
                    
                    link_final_foto = "Sem foto"
                    
                    # Se tiver foto, faz o upload e pega o link
                    if foto:
                        nome_img = f"checkin_{forn_sel}_{datetime.now(fuso_br).strftime('%Y%m%d_%H%M%S')}.jpg"
                        with st.spinner('Enviando foto para o Google Drive...'):
                            link_final_foto = upload_para_drive(foto, nome_img)
                    
                    df_existente = conn.read(ttl=0) 
                    
                    novo_dado = pd.DataFrame([{
                        "Data": agora, 
                        "Loja": loja_sel, 
                        "Fornecedor": forn_sel,
                        "Frequencia": frequencia,
                        "Observacao": obs,
                        "Arquivo_Foto": link_final_foto # AGORA SALVA O LINK CLICÁVEL
                    }])
                    
                    df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
                    conn.update(data=df_final)
                    
                    st.success(f"✅ Registrado com sucesso!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
else:
    st.info("Aguardando arquivo de fornecedores...")
