from utils import formatar_num, formatar_char, FIM_LINHA

def montar_laudo_geral(competencia, apac_numero, paciente_cid_principal):
    """
    Monta o registro 06 (PARTE VARIÁVEL LAUDO GERAL).
    Tamanho total da linha: 39 (37 dados + FIM_LINHA).
    
    Argumentos:
        competencia (str): Mês de produção (YYYYMM).
        apac_numero (str): Número da APAC de 13 dígitos.
        paciente_cid_principal (str): CID Principal do paciente.
    """
    
    # 1. Indicador de linha 06 (2)
    registro = "06" 
    # 2. Ano e mês da produção (6)
    registro += formatar_num(competencia, 6) 
    # 3. Número da APAC (13)
    registro += formatar_num(apac_numero, 13) 
    # 4. CID PRINCIPAL (4)
    registro += formatar_char(paciente_cid_principal, 4) 
    # 5. CID SECUNDÁRIO (4) - Opcional, preencher com espaços
    registro += formatar_char('', 4)
    # 6. Data da identificação patológica (8) - Opcional, preencher com espaços
    registro += formatar_char('', 8) 
    # 7. Fim da linha (2)
    registro += FIM_LINHA
    
    # Verificação de largura (37 dados + 2 FIM_LINHA = 39)
    if len(registro) != 39:
         raise ValueError(f"Erro de formatação no Registro 06: Tamanho incorreto ({len(registro)}).")
    return registro