import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO E LOGO ---
USER_GITHUB = "adrianormartins86-lab"
REPO_GITHUB = "Python"
NOME_IMAGEM = "passaro_logo.png"
URL_ICONE = f"https://raw.githubusercontent.com/{USER_GITHUB}/{REPO_GITHUB}/main/{NOME_IMAGEM}"

st.set_page_config(page_title="Check-in Promotores", layout="centered", page_icon=URL_ICONE)

# --- FUNÇÃO DE UPLOAD PARA O GOOGLE DRIVE ---
def upload_para_drive(arquivo_foto, nome_arquivo):
    """Faz o upload para o Drive usando o método de dicionário das Secrets"""
    try:
        # Define o escopo de acesso necessário
        scope = ['https://www.googleapis.com/auth/drive']
        
        # AJUSTE: Uso do método correto para ler o bloco [gdrive] das Secrets
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gdrive"], scope)
        
        gauth = GoogleAuth()
        gauth.credentials = creds  # Atribui as credenciais (c minúsculo)
        drive = GoogleDrive(gauth)
        
        # ID da pasta oficial compartilhada com a Conta de Serviço
        ID_PASTA_DRIVE = "1VSrgXLR9nKtVclapeZWHkV_ojK55_JtO" 
        
        file_drive = drive.CreateFile({
            'title': nome_arquivo,
            'parents': [{'id': ID_PASTA_DRIVE}],
            'mimeType': 'image/jpeg'
        })
        
        # Garante que o arquivo está no início para leitura binária
        arquivo_foto.seek(0)
        file_drive.content = arquivo_foto  
        file_drive.Upload()
        
        # Retorna o link de visualização direta (webContentLink) para o Power BI
        return file_drive['webContentLink']
    except Exception as e:
        st.error(f"⚠️ Erro técnico no upload para o Drive: {e}")
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
    # Mapeamento de colunas (B=1, G=6, Última=Loja)
    col_empresa = df_forn.columns[1]  
    col_frequencia = df_forn.columns[6] 
    col_loja = df_forn.columns[-1]    

    # 1. Seleção da Loja
    lojas = sorted(df_forn[col_loja].dropna().astype(str).unique().tolist())
    loja_sel = st.selectbox("1. Selecione a Loja:", ["Escolha..."] + lojas)

    if loja_sel != "Escolha...":
        filtro = df_forn[df_forn[col_loja].astype(str) == loja_sel]
        fornecedores = sorted(filtro[col_empresa].dropna().astype(str).unique().tolist())
        forn_sel = st.selectbox("2. Selecione o Fornecedor:", ["Escolha..."] + fornecedores)

        if forn_sel != "Escolha...":
            # Exibição da Frequência (TER/QUI/SAB...)
            dados_sel = filtro[filtro[col_empresa] == forn_sel]
            frequencia = dados_sel[col_frequencia].iloc[0]
            st.info(f"📅 **Frequência Programada:** {frequencia}")
            
            # 2. Observações
            obs = st.text_input("3. Observação (Opcional):", placeholder="Ex: Gôndola organizada...")

            # 3. Upload de Foto
            st.markdown("### 📸 Registro Fotográfico")
            foto = st.file_uploader("Selecione ou tire uma foto", type=["jpg", "jpeg", "png"])
            
            if foto:
                st.image(foto, caption="Prévia da foto", width=200)

            # 4. Botão de Confirmação
            if st.button("Confirmar Check-in", use_container_width=True):
                if foto is None:
                    st.warning("⚠️ Por favor, anexe uma foto antes de confirmar.")
                else:
                    try:
                        # Horário de Brasília
                        fuso_br = pytz.timezone('America/Sao_Paulo')
                        agora_dt = datetime.now(fuso_br)
                        agora_str = agora_dt.strftime("%d/%m/%Y %H:%M:%S")
                        
                        nome_img = f"checkin_{forn_sel}_{agora_dt.strftime('%Y%m%d_%H%M%S')}.jpg"
                        
                        with st.spinner('🚀 Enviando foto e registrando no sistema...'):
                            link_final_foto = upload_para_drive(foto, nome_img)
                        
                        # Apenas prossegue se o upload da foto foi concluído
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
                            st.error("❌ Falha crítica: O registro não foi salvo porque a foto não subiu.")
                            
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {e}")
else:
    st.info("Aguardando arquivo de fornecedores...")
