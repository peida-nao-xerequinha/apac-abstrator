from datetime import datetime, date

# ====================================================
# CONSTANTES E FUNÇÕES GLOBAIS DE FORMATAÇÃO
# ====================================================

# Caracteres de controle de fim de linha obrigatório pelo DATASUS (CR + LF)
FIM_LINHA = "\r\n"

def formatar_num(valor, tamanho):
    """
    Preenche valores NUMÉRICOS com zeros à esquerda (zfill).
    Trunca se o valor for maior que o tamanho definido.
    """
    # 1. Converte para string e trunca para o tamanho máximo
    valor_str = str(valor)[:tamanho]
    # 2. Preenche com zeros à esquerda
    return valor_str.zfill(tamanho)

def formatar_char(valor, tamanho):
    """
    Preenche valores ALFANUMÉRICOS com espaços à direita (ljust).
    Trunca se o valor for maior que o tamanho definido.
    """
    # 1. Converte para string e trunca para o tamanho máximo
    valor_str = str(valor)[:tamanho]
    # 2. Preenche com espaços à direita
    return valor_str.ljust(tamanho)

# ====================================================
# LÓGICA DE NEGÓCIO (MAPAS E IDADE)
# ====================================================

MAPA_PROCEDIMENTOS_OFTALMO = {
    # 9 Anos ou mais (6 Procedimentos)
    "090501003-5": {
        "descricao": "OCI AVAL. INICIAL EM OFTALMO - A PARTIR DE 9 ANOS",
        "secundarios": [
            {"cod": "021106002-0", "qtd": "1"}, 
            {"cod": "030101007-2", "qtd": "2"}, 
            {"cod": "021106012-7", "qtd": "1"}, 
            {"cod": "021106023-2", "qtd": "1"}, 
            {"cod": "021106025-9", "qtd": "1"}, 
        ]
    },
    # 0 a 8 Anos (5 Procedimentos)
    "090501001-9": {
        "descricao": "OCI AVAL. INICIAL EM OFTALMO - 0 A 8 ANOS",
        "secundarios": [
            {"cod": "021106002-0", "qtd": "1"},
            {"cod": "030101007-2", "qtd": "2"},
            {"cod": "021106012-7", "qtd": "1"},
            {"cod": "021106023-2", "qtd": "1"},
        ]
    }
}

# Mapeamento estático da Raça/Cor
MAPA_RACA_COR = {
    'BRANCA': '01',
    'PRETA': '02',
    'PARDA': '03',
    'AMARELA': '04',
    'INDIGENA': '05',
    'INDÍGENA': '05' # Incluir variação acentuada, se necessário
}

def mapear_raca_cor(raca_str: str) -> str:
    # 🚨 DEBUG: O que a função está recebendo?
    print(f"\n[DEBUG RACA/COR] Valor de entrada (raca_str): '{raca_str}'")
    
    if not raca_str:
        print("[DEBUG RACA/COR] String de entrada vazia/None. Retornando '01' (Default).")
        return '01' 
        
    raca_limpa = raca_str.strip().upper()
    
    # 🚨 DEBUG: O que a função está procurando no mapa?
    print(f"[DEBUG RACA/COR] Valor de busca (raca_limpa): '{raca_limpa}'")
    
    codigo_final = MAPA_RACA_COR.get(raca_limpa, '01')
    
    # 🚨 DEBUG: O que a função encontrou?
    print(f"[DEBUG RACA/COR] Código APAC retornado: {codigo_final}")
    
    return codigo_final

def calcular_idade(data_nasc_str, data_consulta_str):
    """Calcula a idade em anos completos."""
    try:
        nasc = datetime.strptime(data_nasc_str, "%Y%m%d").date()
        consulta = datetime.strptime(data_consulta_str, "%Y%m%d").date()
        idade = consulta.year - nasc.year - ((consulta.month, consulta.day) < (nasc.month, nasc.day))
        return idade
    except ValueError:
        return 0

def selecionar_procedimento(idade):
    """Retorna o dicionário de procedimentos (principal + secundários) baseado na idade."""
    if idade >= 9:
        return MAPA_PROCEDIMENTOS_OFTALMO["090501003-5"]
    else:
        return MAPA_PROCEDIMENTOS_OFTALMO["090501001-9"]

# ====================================================
# FUNÇÃO DE CÁLCULO DE CONTROLE
# ====================================================

def calcular_campo_controle(lista_procedimentos, apac_numero):
    """
    Calcula o valor do Campo de Controle (4 dígitos) para o Registro 01 do Cabeçalho,
    seguindo a PORTARIA/SAS Nº 197, DE 30 DE OUTUBRO DE 1998.

    Args:
        lista_procedimentos (list): Lista de dicionários de procedimentos, 
                                    onde cada item tem 'cod' e 'qtd'.
        apac_numero (str): Número da APAC (13 dígitos).

    Returns:
        str: O valor do campo de controle (4 dígitos, preenchido com zeros à esquerda).
    """
    
    # 1. Somar o código de todos os procedimentos + quantidade + número da APAC.
    
    try:
        # Usaremos os 13 dígitos completos conforme o cálculo costuma exigir
        soma = int(apac_numero)
    except ValueError:
        soma = 0 

    # Soma os códigos e quantidades de cada procedimento
    for proc in lista_procedimentos:
        try:
            # O código do procedimento (10 dígitos) e a quantidade (7 dígitos) precisam ser somados.
            cod_proc = proc['cod'].replace('-', '') 
            qtd_proc = proc['qtd']

            soma += int(cod_proc)
            soma += int(qtd_proc)
        except ValueError:
            continue

    # 2. Obter o resto da divisão do resultado acima por 1111.
    resto = soma % 1111

    # 3. Somar 1111 ao resto da divisão acima.
    campo_controle = resto + 1111

    # Retorna o resultado formatado em 4 dígitos (ex: 0001)
    return formatar_num(campo_controle, 4)