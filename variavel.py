from utils import (
    formatar_num,
    formatar_char,
    sanitize_basic,
    FIM_LINHA
)

def montar_laudo_geral(competencia, apac_numero, paciente_cid_principal):
    """
    Registro 06 – Laudo Geral
    Tamanho: 25 caracteres + CRLF

    Campos:
        1. Indicador ............... 2
        2. Competência (AAAAMM) .... 6
        3. Nº APAC ................. 13
        4. CID Principal ........... 4
    """

    # Sanitização pré-format
    competencia = sanitize_basic(competencia)
    apac_numero = sanitize_basic(apac_numero)
    cid = sanitize_basic(paciente_cid_principal).upper().strip()

    registro = ""

    # 1. Indicador
    registro += "06"                             # (2)

    # 2. Competência YYYYMM
    registro += formatar_num(competencia, 6)     # (6)

    # 3. Número da APAC
    registro += formatar_num(apac_numero, 13)    # (13)

    # 4. CID Principal
    registro += formatar_char(cid, 4)            # (4)

    # Soma: 2 + 6 + 13 + 4 = 25
    if len(registro) != 25:
        raise ValueError(
            f"Tamanho incorreto do Registro 06: {len(registro)} (esperado 25)."
        )

    return registro + FIM_LINHA