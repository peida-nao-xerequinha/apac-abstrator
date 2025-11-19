from utils import (
    formatar_char,
    formatar_num,
    sanitize_basic,
    FIM_LINHA
)

def montar_corpo(dados):
    """
    Registro 14 — CORPO DA APAC.
    Total exato: 535 caracteres (inclui o apa_fim = CRLF).
    """

    r = ""

    def num(c, t):
        return formatar_num(sanitize_basic(dados.get(c, "")), t)

    def char(c, t):
        return formatar_char(sanitize_basic(dados.get(c, "")), t)

    # --- início (campos 1 a 48) ---
    r += num("apa_corpo", 2)
    r += num("apa_cmp", 6)
    r += num("apa_num", 13)
    r += num("apa_coduf", 2)
    r += num("apa_codcnes", 7)
    r += num("apa_pr", 8)
    r += num("apa_dtiinval", 8)
    r += num("apa_dtfimval", 8)
    r += num("apa_tipate", 2)
    r += num("apa_tipapac", 1)
    r += char("apa_nomepcnte", 30)
    r += char("apa_nomemae", 30)
    r += char("apa_logpcnte", 30)
    r += char("apa_numpcnte", 5)       # CORRIGIDO
    r += char("apa_cplpcnte", 10)
    r += num("apa_ceppcnte", 8)
    r += char("apa_munpcnte", 7)
    r += num("apa_datanascim", 8)
    r += char("apa_sexopcnte", 1)
    r += char("apa_nomeresp", 30)
    r += num("apa_codprinc", 10)
    r += num("apa_motsaida", 2)
    r += char("apa_dtobitoalta", 8)
    r += char("apa_nomediretor", 30)
    r += formatar_char("", 15)
    r += num("apa_cnsres", 15)
    r += num("apa_cnsdir", 15)
    r += char("apa_cidca", 4)
    r += char("apa_npront", 10)
    r += num("apa_codsol", 7)
    r += num("apa_datsol", 8)
    r += num("apa_dataut", 8)
    r += char("apa_codemis", 10)
    r += num("apa_carate", 2)
    r += num("apa_apacant", 13)
    r += num("apa_raca", 2)
    r += char("apa_nomeresp_pcte", 30)
    r += num("apa_nascpcnte", 3)
    r += char("APA_etnia", 4)
    r += num("apa_cdlogr", 3)
    r += char("apa_bairro", 30)
    r += char("apa_dddtelcontato", 2)
    r += char("apa_telcontato", 9)     # revisar origem deste campo
    r += char("apa_email", 40)
    r += num("apa_cnsexec", 15)
    r += num("apa_cpfpcnte", 11)
    r += char("apa_ine", 10)
    r += char("apa_strua", 1)

    # --- campo 49: final CRLF ---
    r += "\r\n"  # EXATAMENTE 2 BYTES

    # validação
    if len(r) != 535:
        raise ValueError(f"Registro 14 incorreto: {len(r)} bytes (esperado 535).")

    return r
