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

# Criar pasta para fotos se não existir
if not os.path.exists("fotos_checkin"):
    os.makedirs("fotos_checkin")

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
    # --- MAPEAMENTO AJUSTADO ---
    col_empresa = df_forn.columns[1]    # Coluna B
    col_frequencia = df_forn.columns[5]  # AJUSTE: Coluna G (Frequência de Visita)
    col_loja = df_forn.columns[-1]      # Última Coluna (Loja)

    # 1. Seleção da Loja
    lojas = sorted(df_forn[col_loja].dropna().astype(str).unique().tolist())
    loja_sel = st.selectbox("1. Selecione a Loja:", ["Escolha..."] + lojas)

    if loja_sel != "Escolha...":
        filtro = df_forn[df_forn[col_loja].astype(str) == loja_sel]
        fornecedores = sorted(filtro[col_empresa].dropna().astype(str).unique().tolist())
        forn_sel = st.selectbox("2. Selecione o Fornecedor:", ["Escolha..."] + fornecedores)

        if forn_sel != "Escolha...":
            # --- EXIBIÇÃO DA FREQUÊNCIA (TER/QUI/SAB...) ---
            dados_sel = filtro[filtro[col_empresa] == forn_sel]
            frequencia_info = dados_sel[col_frequencia].iloc[0]
            st.info(f"📅 **Frequência de Visita:** {frequencia_info}")
            
            obs = st.text_input("3. Observação (Opcional):")

            # 📸 REGISTRO FOTOGRÁFICO
            foto = st.file_uploader("4. Tire uma foto ou anexe", type=["jpg", "jpeg", "png"])
            
            if foto:
                st.image(foto, caption="Foto selecionada", width=200)

            # 5. BOTÃO DE CONFIRMAÇÃO
            if st.button("Confirmar Check-in", use_container_width=True):
                try:
                    fuso_br = pytz.timezone('America/Sao_Paulo')
                    agora_dt = datetime.now(fuso_br)
                    agora_str = agora_dt.strftime("%d/%m/%Y %H:%M:%S")
                    
                    nome_arquivo_foto = "Sem foto"
                    
                    if foto is not None:
                        nome_arquivo_foto = f"{agora_dt.strftime('%Y%m%d_%H%M%S')}_{forn_sel}.jpg".replace(" ", "_")
                        caminho_completo = os.path.join("fotos_checkin", nome_arquivo_foto)
                        with open(caminho_completo, "wb") as f:
                            f.write(foto.getbuffer())
                    
                    # Envio para o Sheets (SEM a coluna de frequência, conforme solicitado)
                    df_existente = conn.read(ttl=0) 
                    novo_dado = pd.DataFrame([{
                        "Data": agora_str, 
                        "Loja": loja_sel, 
                        "Fornecedor": forn_sel,
                        "Observacao": obs,
                        "Foto_Ref": nome_arquivo_foto 
                    }])
                    
                    df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
                    conn.update(data=df_final)
                    
                    st.success(f"✅ Registrado com sucesso!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
else:
    st.info("Aguardando arquivo de fornecedores...")
