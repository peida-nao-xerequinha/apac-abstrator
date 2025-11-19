from datetime import datetime

# ====================================================
# CONSTANTES E FUNÇÕES GLOBAIS DE FORMATAÇÃO
# ====================================================

# Fim de linha obrigatório pelo DATASUS (CRLF)
FIM_LINHA = "\r\n"


# ============================
# 🔐 FUNÇÕES DE SANITIZAÇÃO
# ============================

def sanitize_basic(value):
    """
    Converte qualquer coisa para string simples,
    remove espaços extras e caracteres de controle comuns.
    """
    if value is None:
        return ""
    try:
        s = str(value)
        # remove null bytes e caracteres de controle básicos
        s = s.replace('\x00', '')
        # normaliza CR/LF para espaços e remove tabs
        s = s.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return s.strip()
    except Exception:
        return ""


def sanitize_numeric(value):
    """
    Remove tudo que NÃO for número.
    Trata floats (evita notação científica) e strings com pontuação.
    Exemplos:
      - '519.500.107-83' -> '51950010783'
      - 5.1950010783e10  -> '51950010783' (quando for inteiro equivalente)
    """
    if value is None:
        return ""

    # Protege floats para evitar notação científica estranha
    if isinstance(value, float):
        # se for inteiro equivalente, transforme para int
        if value.is_integer():
            value = str(int(value))
        else:
            value = str(value)

    s = str(value)

    # Remove separadores comuns e parênteses
    for ch in " .,-/\\()":
        s = s.replace(ch, "")

    # Mantém apenas dígitos
    s = ''.join(c for c in s if c.isdigit())

    return s.strip()


def sanitize_alpha(value):
    """
    Mantém apenas letras, espaços e alguns sinais simples.
    Útil para campos de nome/descrição quando quiser garantir ausência de números.
    """
    if value is None:
        return ""
    s = str(value)
    return ''.join(c for c in s if c.isalpha() or c.isspace()).strip()


# ======================================
# 🔧 FORMATADORES — agora com sanitização
# ======================================

def formatar_num(valor, tamanho):
    """
    Formata campo numérico:
      - sanitiza (mantém só dígitos)
      - remove notação científica de floats
      - preenche com zeros à esquerda
      - se exceder o tamanho, TRUNCA à direita (apenas último recurso de compatibilidade)
    Obs: truncagem explícita evita exceções em massa; você pode transformar isto em erro
    se preferir falhar rápido quando houver dados maiores que o layout.
    """
    valor_sanit = sanitize_numeric(valor)

    # Se exceder o tamanho, trunca (mantendo os dígitos mais à esquerda)
    if len(valor_sanit) > tamanho:
        valor_sanit = valor_sanit[:tamanho]

    return valor_sanit.zfill(tamanho)


def formatar_char(valor, tamanho):
    """
    Formata campo alfanumérico:
      - sanitiza textos (remove CR/LF, tabs, nulls)
      - trunca se exceder o tamanho
      - preenche espaços à direita até o tamanho
    """
    valor_sanit = sanitize_basic(valor)

    if len(valor_sanit) > tamanho:
        valor_sanit = valor_sanit[:tamanho]

    return valor_sanit.ljust(tamanho)


# ====================================================
# LÓGICA DE NEGÓCIO (MAPAS E IDADE) - mantida para compatibilidade
# ====================================================

MAPA_PROCEDIMENTOS_OFTALMO = {
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

MAPA_RACA_COR = {
    "BRANCA": "01",
    "PRETA": "02",
    "PARDA": "03",
    "AMARELA": "04",
    "INDIGENA": "05",
    "INDÍGENA": "05",
}

def mapear_raca_cor(raca_str: str) -> str:
    r = sanitize_basic(raca_str).upper()
    return MAPA_RACA_COR.get(r, "01")


def calcular_idade(data_nasc_str, data_consulta_str):
    try:
        nasc = datetime.strptime(data_nasc_str, "%Y%m%d").date()
        cons = datetime.strptime(data_consulta_str, "%Y%m%d").date()
        return cons.year - nasc.year - ((cons.month, cons.day) < (nasc.month, nasc.day))
    except Exception:
        return 0


def selecionar_procedimento(idade):
    return MAPA_PROCEDIMENTOS_OFTALMO["090501003-5"] if idade >= 9 else MAPA_PROCEDIMENTOS_OFTALMO["090501001-9"]


# ====================================================
# CAMPO DE CONTROLE
# ====================================================

def calcular_campo_controle(lista_procedimentos, apac_numero):
    try:
        soma = int(sanitize_numeric(apac_numero) or 0)
    except Exception:
        soma = 0

    for proc in lista_procedimentos:
        try:
            soma += int(sanitize_numeric(proc.get("cod", "")) or 0)
            soma += int(sanitize_numeric(proc.get("qtd", "")) or 0)
        except Exception:
            pass

    resto = soma % 1111
    controle = resto + 1111
    return formatar_num(controle, 4)
