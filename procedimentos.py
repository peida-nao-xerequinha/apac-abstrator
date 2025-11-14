from utils import formatar_num, formatar_char, FIM_LINHA, selecionar_procedimento, MAPA_PROCEDIMENTOS_OFTALMO

def montar_procedimento(competencia, apac_numero, cod_proc, qtd, cnes_terceiro):
    """
    Monta uma única linha do registro 13 (REGISTRO DE PROCEDIMENTOS/AÇÕES). 
    Tamanho total: 99 (97 dados + FIM_LINHA).
    """
    cbo = '225265'
    
    registro_replicate = "13" # 2
    registro_replicate += formatar_num(competencia, 6) # 6
    registro_replicate += formatar_num(apac_numero, 13) # 13
    registro_replicate += formatar_num(cod_proc.replace('-', ''), 10) # 10
    registro_replicate += formatar_num(cbo, 6) # 6
    registro_replicate += formatar_num(qtd, 7) # 6. Quantidade de procedimentos (7)
    
    # --- PREENCHIMENTO DE CAMPOS OPCIONAIS (ADJACENTES A QUANTIDADE) ---
    # Para replicar o alvo (que não usa zeros em NUM opcionais):
    
    # 7. CNPJ cessão (pap CGC - NUM, 14) -> Usar CHAR para espaço, replicando o alvo
    registro_replicate += formatar_char('', 14) 
    
    # 8. Número NF Cessão (pap NF - CHAR, 6)
    registro_replicate += formatar_char('', 6)
    
    # 9. CID Principal (pap_CIDP - CHAR, 4)
    registro_replicate += formatar_char('', 4)
    
    # 10. CID Secundário (pap_CIDS - CHAR, 4)
    registro_replicate += formatar_char('', 4)
    
    # 11. Código do Serviço (pap SRV - CHAR, 3)
    registro_replicate += formatar_char('', 3)
    
    # 12. Código da Classificação (pap CLF - NUM, 3) -> Usar CHAR para espaço
    registro_replicate += formatar_char('', 3) 
    
    # 13. Código da Sequência da Equipe (pap equipe Seq - NUM, 8) -> Usar CHAR para espaço
    registro_replicate += formatar_char('', 8)
    
    # 14. Código da Área da Equipe (pap equipe Area - NUM, 4) -> Usar CHAR para espaço
    registro_replicate += formatar_char('', 4)

    # 15. Código da Unidade Prestadora Terceiro (pap_cnes_terc - NUM, 7)
    # INJEÇÃO FINAL DO CNES TERCEIRO (3312445)
    registro_replicate += formatar_num(cnes_terceiro, 7) 

    registro_replicate += FIM_LINHA
    
    if len(registro_replicate) != 99:
         raise ValueError(f"Erro de formatação no Registro 13: Tamanho incorreto ({len(registro_replicate)}).")
    
    return registro_replicate


def gerar_bloco_procedimentos(paciente_idade, competencia, apac_numero, cnes_terceiro):
    # ... (Esta função é mantida, pois a lógica de idade e loop está correta)
    proc_selecionado = selecionar_procedimento(paciente_idade)
    cod_principal = next(key for key, value in MAPA_PROCEDIMENTOS_OFTALMO.items() if value == proc_selecionado)
    
    linhas_procedimentos = []
    
    # 1. Procedimento Principal
    linhas_procedimentos.append(montar_procedimento(
        competencia, apac_numero, cod_principal, "1", cnes_terceiro
    ))
    
    # 2. Procedimentos Secundários
    for proc_sec in proc_selecionado['secundarios']:
        linhas_procedimentos.append(montar_procedimento(
            competencia, apac_numero, proc_sec['cod'], proc_sec['qtd'], cnes_terceiro
        ))
        
    return linhas_procedimentos