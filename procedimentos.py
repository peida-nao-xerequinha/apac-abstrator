from utils import (
    formatar_num,
    formatar_char,
    sanitize_basic,
    FIM_LINHA
)

from utils import selecionar_procedimento, MAPA_PROCEDIMENTOS_OFTALMO


def montar_procedimento(competencia, apac_numero, cod_proc, qtd, cnes_terceiro):
    """
    Registro 13 – Procedimentos/Ações Realizadas.
    Tamanho total: 99 caracteres (incluindo CRLF do campo FIM).

    O CRLF faz parte do campo 16, então ELE entra na contagem.
    """

    competencia = sanitize_basic(competencia)
    apac_numero = sanitize_basic(apac_numero)
    cod_proc = sanitize_basic(cod_proc).replace("-", "")
    qtd = sanitize_basic(qtd)
    cnes_terceiro = sanitize_basic(cnes_terceiro)

    CBO = "225265"

    r = ""

    # 1. Indicador
    r += "13"

    # 2. Competência
    r += formatar_num(competencia, 6)

    # 3. APAC
    r += formatar_num(apac_numero, 13)

    # 4. Procedimento
    r += formatar_num(cod_proc, 10)

    # 5. CBO
    r += formatar_num(CBO, 6)

    # 6. Quantidade
    r += formatar_num(qtd, 7)

    # 7. CNPJ cessão – espaços
    r += formatar_char("", 14)

    # 8. Nº NF – espaços
    r += formatar_char("", 6)

    # 9. CID principal – espaços
    r += formatar_char("", 4)

    # 10. CID secundário – espaços
    r += formatar_char("", 4)

    # 11. Serviço – espaços
    r += formatar_char("", 3)

    # 12. Classificação – espaços
    r += formatar_char("", 3)

    # 13. Sequência equipe – espaços
    r += formatar_char("", 8)

    # 14. Área equipe – espaços
    r += formatar_char("", 4)

    # 15. CNES terceiro
    r += formatar_char(cnes_terceiro, 7)

    # 16. FIM (faz parte do registro!)
    r += "\r\n"

    # -------------------------------------------------------
    # VALIDAÇÃO FINAL — Registro tem que ter EXATAMENTE 99
    # -------------------------------------------------------
    if len(r) != 99:
        raise ValueError(
            f"Registro 13 com tamanho inválido: {len(r)} (esperado 99)"
        )

    return r


def gerar_bloco_procedimentos(idade, competencia, apac_numero, cnes_terceiro):
    """
    Gera:
        - 1 procedimento principal
        - N procedimentos secundários
    """

    proc_sel = selecionar_procedimento(idade)

    cod_principal = next(
        key for key, value in MAPA_PROCEDIMENTOS_OFTALMO.items()
        if value == proc_sel
    )

    linhas = []

    # Procedimento principal
    linhas.append(
        montar_procedimento(
            competencia, apac_numero, cod_principal, "1", ""
        )
    )

    # Procedimentos secundários
    for proc in proc_sel["secundarios"]:
        linhas.append(
            montar_procedimento(
                competencia,
                apac_numero,
                proc["cod"],
                proc["qtd"],
                cnes_terceiro
            )
        )

    return linhas
