import os
from typing import List, Tuple

# Defina o nome do arquivo da numeração
NOME_ARQUIVO_NUMERACAO = "Numeração OCI.TXT"

def ler_numeracoes() -> List[str]:
    """
    Lê o arquivo de numeração da APAC, ignora o cabeçalho e 
    retorna uma lista dos números (apenas os 12 dígitos, sem o DV/hífen).
    """
    numeracoes_limpas = []
    
    # Verifica se o arquivo existe antes de tentar ler
    if not os.path.exists(NOME_ARQUIVO_NUMERACAO):
        print(f"ERRO: Arquivo de numeração não encontrado: {NOME_ARQUIVO_NUMERACAO}")
        return []

    try:
        with open(NOME_ARQUIVO_NUMERACAO, 'r', encoding='utf-8') as f:
            # Pula o cabeçalho ("NUMERAÇÃO APAC" na primeira linha)
            f.readline() 
            
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue # Ignora linhas em branco
                
                # O formato é: 352570409959-9. Queremos apenas os 12 dígitos antes do hífen.
                # O número completo da APAC (com DV) tem 13 dígitos.
                if '-' in linha and len(linha) >= 14: 
                    # Extrai os 12 primeiros dígitos (sem o DV)
                    numero_sem_dv = linha.split('-')[0][:12] 
                    numeracoes_limpas.append(numero_sem_dv)
                else:
                    print(f"AVISO: Linha ignorada por formato inválido: {linha}")
                    
    except Exception as e:
        print(f"ERRO ao ler o arquivo de numeração: {e}")
        
    return numeracoes_limpas

def salvar_numeracoes(numeracoes: List[str]):
    """
    Salva a lista de numerações restantes no arquivo, recriando o arquivo.
    """
    try:
        with open(NOME_ARQUIVO_NUMERACAO, 'w', encoding='utf-8') as f:
            f.write("NUMERAÇÃO APAC\n") # Recria o cabeçalho
            for num in numeracoes:
                # Recompõe o formato original (12 dígitos + DV). 
                # Como a leitura só pegou 12, vamos usar um placeholder para o DV.
                # Se for necessário recalcular o DV, isso precisará ser feito,
                # mas por hora, o formato é: '12 dígitos' + '-' + '1 dígito'.
                # A APAC é um número de 13 dígitos. Vamos assumir que a numeração fornecida é o número completo de 13 dígitos.
                # **INCONSISTÊNCIA DETECTADA**: O arquivo tem 12 dígitos + DV (14 chars total). O layout APAC tem 13 dígitos.
                # Vamos assumir que os 12 são a numeração e o último é o DV. A APAC no layout precisa dos 13 dígitos.
                
                # Para salvar de volta no formato original (12 + DV), vamos ter que confiar no formato de entrada.
                # *Ajuste de Assunção*: A APAC completa (com DV) tem 13 dígitos. O seu arquivo mostra 12 dígitos + DV: `352570409959-9`. 
                # Isso sugere 12 digitos + DV separado. O layout APAC pede 13.
                # Vamos manter o formato original para salvar: num (12 dígitos) + DV (recalcular ou assumir o formato do arquivo original).
                # Como não temos o DV original após a leitura, vamos apenas salvar os 12 dígitos lidos, para manter a lógica simples de consumo.
                
                # **Revisando a Leitura do Usuário**: A APAC tem 13 dígitos.
                # A linha no arquivo é: 352570409959-9. Total: 14 caracteres.
                # Se o número da APAC for `3525704099599` (13 dígitos), o arquivo está formatado de forma estranha.
                # Para o cálculo de controle e o corpo da APAC, precisamos dos 13 dígitos.
                
                # SOLUÇÃO: Vamos extrair os 13 dígitos (12 da numeração + 1 do DV).
                f.write(f"{num}\n") # Simplificado para salvar apenas os 12 dígitos lidos.
                
    except Exception as e:
        print(f"ERRO ao salvar o arquivo de numeração: {e}")

def consumir_apac() -> Tuple[str, List[str]]:
    """
    Lê a lista de numerações, retorna a primeira disponível (para uso) e 
    salva a lista atualizada (sem o número consumido).
    
    Retorna:
        Tuple[str, List[str]]: (Numero da APAC para uso, Lista restante)
    """
    numeracoes = ler_numeracoes()
    
    if not numeracoes:
        return None, []
        
    # O número da APAC a ser usado é o primeiro da lista
    apac_consumida = numeracoes.pop(0) 
    
    # Salva a lista restante
    salvar_numeracoes(numeracoes)
    
    # Retorna o número consumido. 
    # **Nota Importante**: Para o layout APAC, o número deve ter 13 dígitos. 
    # O arquivo fornecido `352570409959-9` tem 12 dígitos + DV. 
    # Assumindo que a APAC completa é `3525704099599`, o `pop(0)` retorna `352570409959`.
    # O módulo principal terá que anexar o dígito verificador ('9' neste caso) para ter o número completo de 13.
    
    # Vamos reajustar a leitura para pegar o número completo de 13 dígitos (12 + DV)
    # E vamos ajustar a função de leitura.
    
    return apac_consumida, numeracoes

# --- REAJUSTE NA FUNÇÃO DE LEITURA PARA OBTER 13 DÍGITOS ---

def ler_numeracoes() -> List[str]:
    """
    Lê o arquivo de numeração da APAC, ignora o cabeçalho e 
    retorna uma lista dos números completos da APAC (13 dígitos, 12 + DV).
    """
    numeracoes_completas = []
    
    if not os.path.exists(NOME_ARQUIVO_NUMERACAO):
        print(f"ERRO: Arquivo de numeração não encontrado: {NOME_ARQUIVO_NUMERACAO}")
        return []

    try:
        with open(NOME_ARQUIVO_NUMERACAO, 'r', encoding='utf-8') as f:
            f.readline() 
            
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                
                # Formato: 352570409959-9. Os 13 dígitos da APAC são '352570409959' + '9'
                if '-' in linha and len(linha) >= 14: 
                    # 12 dígitos
                    num_base = linha.split('-')[0]
                    # 1 dígito verificador
                    dv = linha.split('-')[1]
                    
                    # Concatena os 13 dígitos da APAC (Ex: '3525704099599')
                    apac_completa = num_base + dv
                    numeracoes_completas.append(apac_completa)
                else:
                    # Se não tiver o hífen, tenta pegar os 13 primeiros caracteres
                    if len(linha) >= 13 and linha.isnumeric():
                        numeracoes_completas.append(linha[:13])
                    else:
                        print(f"AVISO: Linha ignorada por formato inválido: {linha}")
                    
    except Exception as e:
        print(f"ERRO ao ler o arquivo de numeração: {e}")
        
    return numeracoes_completas

def salvar_numeracoes(numeracoes: List[str]):
    """
    Salva a lista de numerações restantes no arquivo, formatando de volta
    para 12 dígitos + hífen + DV.
    """
    try:
        with open(NOME_ARQUIVO_NUMERACAO, 'w', encoding='utf-8') as f:
            f.write("NUMERAÇÃO APAC\n")
            for apac_completa in numeracoes:
                if len(apac_completa) == 13:
                    # Recompõe o formato (12 dígitos)-(DV)
                    formato_arquivo = f"{apac_completa[:12]}-{apac_completa[12]}"
                    f.write(f"{formato_arquivo}\n")
                else:
                    # Em caso de numeração corrompida, salva como está (melhor do que perder)
                    f.write(f"{apac_completa}\n")
                    
    except Exception as e:
        print(f"ERRO ao salvar o arquivo de numeração: {e}")
        
# A função consumir_apac() usa as funções reajustadas acima.