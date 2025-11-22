from datetime import datetime
from utils import (
    formatar_num,
    formatar_char,
    sanitize_basic,
    FIM_LINHA,
    calcular_campo_controle
)


def montar_cabecalho(competencia, cnes_dados, total_apacs_gravadas, lista_procedimentos, apac_primeira, versao):
    """
    Registro 01 – Cabeçalho da Remessa APAC
    Tamanho total: 139 caracteres (137 dados + CRLF)

    Campos:
        01 – Indicador (01) ....................... 2
        02 – Literal "#APAC" ...................... 5
        03 – Competência (AAAAMM) ................. 6
        04 – Qtde APACs geradas ................... 6
        05 – Campo de controle ..................... 4
        06 – Nome órgão origem .................... 30
        07 – Sigla órgão origem .................... 6
        08 – CGC/CPF Prestador .................... 14
        09 – Nome órgão destino ................... 40
        10 – Indicador destino ..................... 1
        11 – Data geração (AAAAMMDD) ............... 8
        12 – Versão ................................ 15
    """

    # Sanitização
    competencia = sanitize_basic(competencia)
    total_apacs_gravadas = sanitize_basic(total_apacs_gravadas)

    # Campo de controle (método oficial DATASUS)
    campo_controle = calcular_campo_controle(lista_procedimentos, apac_primeira)

    # Dados do CNES
    nome_orgao = sanitize_basic(cnes_dados.get("cbc-rsp", ""))
    sigla_orgao = sanitize_basic(cnes_dados.get("cbc-sgl", ""))
    cgc = sanitize_basic(cnes_dados.get("cbc-cgccpf", ""))
    nome_destino = sanitize_basic(cnes_dados.get("cbc-dst", ""))
    indicador_destino = sanitize_basic(cnes_dados.get("cbc-dst-in", ""))[:1]

    data_geracao = datetime.now().strftime("%Y%m%d")

    r = ""

    # 1. Indicador
    r += "01"

    # 2. Literal: "#APAC"
    r += formatar_char("#APAC", 5)

    # 3. Competência
    r += formatar_num(competencia, 6)

    # 4. Qtde APACs gravadas
    r += formatar_num(total_apacs_gravadas, 6)

    # 5. Campo de controle
    r += formatar_num(campo_controle, 4)

    # 6. Nome órgão origem
    r += formatar_char(nome_orgao, 30)

    # 7. Sigla
    r += formatar_char(sigla_orgao, 6)

    # 8. CGC/CPF prestador
    r += formatar_num(cgc, 14)

    # 9. Nome órgão destino
    r += formatar_char(nome_destino, 40)

    # 10. Indicador destino
    r += formatar_char(indicador_destino, 1)

    # 11. Data geração
    r += formatar_num(data_geracao, 8)

    # 12. Versão do layout
    r += formatar_char(versao, 15)

    # Validação de tamanho
    if len(r) != 137:
        raise ValueError(f"Registro 01 inválido ({len(r)} chars). Esperado: 137")

    return r + FIM_LINHA
