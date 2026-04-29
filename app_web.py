import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz  # Biblioteca para fuso horário
import os

# ... (restante do código inicial permanece igual)

# Dentro da parte onde o botão de check-in é clicado:
if st.button("Confirmar Check-in", use_container_width=True):
    # DEFINE O FUSO HORÁRIO DE BRASÍLIA
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
    
    try:
        df_existente = conn.read() 
        
        novo_dado = pd.DataFrame([{
            "Data": agora, 
            "Loja": loja_sel, 
            "Fornecedor": forn_sel,
            "Observacao": obs
        }])
        
        df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
        conn.update(data=df_final)
        
        st.success(f"✅ Registrado com horário de Brasília: {agora}")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
