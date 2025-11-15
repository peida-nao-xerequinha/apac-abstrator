import os
from typing import List, Tuple

# Defina o nome do arquivo da numeração
NOME_ARQUIVO_NUMERACAO = "Numeração OCI.TXT"

# Variável GLOBAL para manter as numerações lidas em memória.
# Será a lista principal de onde os números serão consumidos.
NUMERACOES_APAC_MEMORIA: List[str] = []

# --- FUNÇÕES DE PERSISTÊNCIA (LEITURA E ESCRITA) ---

def _ler_numeracoes_disco() -> List[str]:
    """
    Função interna para ler o arquivo TXT do disco e retornar a lista de 13 dígitos.
    (Lógica de leitura mantida).
    """
    numeracoes_completas = []
    
    if not os.path.exists(NOME_ARQUIVO_NUMERACAO):
        return []

    try:
        # Usamos 'latin1' ou 'cp1252' para arquivos TXT de sistemas brasileiros
        with open(NOME_ARQUIVO_NUMERACAO, 'r', encoding='latin1') as f:
            f.readline() # Pula o cabeçalho
            
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                
                # Assume o formato: 352570409959-9. Concatena 12 dígitos + DV.
                if '-' in linha and len(linha) >= 14: 
                    num_base = linha.split('-')[0]
                    dv = linha.split('-')[1]
                    apac_completa = num_base + dv
                    numeracoes_completas.append(apac_completa)
                elif len(linha) >= 13 and linha.isnumeric():
                     # Caso não tenha hífen, tenta usar os 13 dígitos diretos
                    numeracoes_completas.append(linha[:13])
                    
    except Exception as e:
        print(f"ERRO ao ler o arquivo de numeração: {e}")
        
    return numeracoes_completas

def salvar_numeracoes():
    """
    Salva a lista de numerações da memória (NUMERACOES_APAC_MEMORIA) de volta no arquivo TXT, 
    reformatando para 12 dígitos + hífen + DV.
    """
    global NUMERACOES_APAC_MEMORIA
    try:
        with open(NOME_ARQUIVO_NUMERACAO, 'w', encoding='latin1') as f:
            f.write("NUMERAÇÃO APAC\n")
            for apac_completa in NUMERACOES_APAC_MEMORIA:
                if len(apac_completa) == 13:
                    # Recompõe o formato original (12 dígitos)-(DV)
                    formato_arquivo = f"{apac_completa[:12]}-{apac_completa[12]}"
                    f.write(f"{formato_arquivo}\n")
                else:
                    f.write(f"{apac_completa}\n")
                    
    except Exception as e:
        print(f"ERRO ao salvar o arquivo de numeração: {e}")

# --- FUNÇÕES DE GERENCIAMENTO DE ESTADO (MANAGER) ---

def inicializar_manager():
    """
    Função chamada uma vez no início da aplicação para carregar o estado inicial do disco.
    """
    global NUMERACOES_APAC_MEMORIA
    NUMERACOES_APAC_MEMORIA = _ler_numeracoes_disco()
    print(f"Gerenciador APAC inicializado. {len(NUMERACOES_APAC_MEMORIA)} numerações carregadas.")


def consumir_apac() -> Tuple[str, int]:
    """
    Retira e retorna a primeira numeração disponível da memória.
    
    Retorna:
        Tuple[str, int]: (Número da APAC consumida, Total de APACs restantes)
    """
    global NUMERACOES_APAC_MEMORIA
    
    if not NUMERACOES_APAC_MEMORIA:
        return None, 0
        
    # Retira o primeiro item da lista (consumo)
    apac_consumida = NUMERACOES_APAC_MEMORIA.pop(0) 
    
    return apac_consumida, len(NUMERACOES_APAC_MEMORIA)