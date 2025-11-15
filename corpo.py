from utils import formatar_char, formatar_num, FIM_LINHA # Reutiliza nossas funções de formatação

def montar_corpo(dados_linha):
    """
    Formata e concatena todos os 49 campos do Registro 14 (Corpo da APAC) 
    em uma única string de 535 caracteres, usando os tamanhos exatos.
    
    Argumentos:
        dados_linha (dict): Dicionário contendo os 49 campos do layout.
        
    Retorna:
        str: A linha do Registro 14 formatada.
    """
    
    # 1. Indicador de corpo da APAC (apa_corpo - Tam: 2)
    registro = formatar_num(dados_linha.get('apa_corpo', 14), 2)
    
    # 2. Ano e mês da produção (apa_cmp - Tam: 6)
    registro += formatar_num(dados_linha.get('apa_cmp', ''), 6)
    
    # 3. Número da APAC (apa_num - Tam: 13)
    registro += formatar_num(dados_linha.get('apa_num', ''), 13)
    
    # 4. Código da UF (apa_coduf - Tam: 2)
    registro += formatar_num(dados_linha.get('apa_coduf', ''), 2)
    
    # 5. Código da Unidade Prestadora (apa_codcnes - Tam: 7)
    registro += formatar_num(dados_linha.get('apa_codcnes', ''), 7)
    
    # 6. Data processamento (apa_pr - Tam: 8)
    registro += formatar_num(dados_linha.get('apa_pr', ''), 8)
    
    # 7. Data inicial validade (apa_dtiinval - Tam: 8)
    registro += formatar_num(dados_linha.get('apa_dtiinval', ''), 8)
    
    # 8. Data final validade (apa_dtfimval - Tam: 8)
    registro += formatar_num(dados_linha.get('apa_dtfimval', ''), 8)
    
    # 9. Tipo de atendimento (apa_tipate - Tam: 2)
    registro += formatar_num(dados_linha.get('apa_tipate', ''), 2)
    
    # 10. Tipo de APAC (apa_tipapac - Tam: 1)
    registro += formatar_num(dados_linha.get('apa_tipapac', ''), 1)
    
    # 11. Nome do paciente (apa_nomepcnte - Tam: 30)
    registro += formatar_char(dados_linha.get('apa_nomepcnte', ''), 30)
    
    # 12. Nome da mãe (apa_nomemae - Tam: 30)
    registro += formatar_char(dados_linha.get('apa_nomemae', ''), 30)
    
    # 13. Logradouro (apa_logpcnte - Tam: 30)
    registro += formatar_char(dados_linha.get('apa_logpcnte', ''), 30)
    
    # 14. Número residência (apa_numpcnte - Tam: 5)
    registro += formatar_char(dados_linha.get('apa_numpcnte', ''), 5)
    
    # 15. Complemento (apa_cplpcnte - Tam: 10)
    registro += formatar_char(dados_linha.get('apa_cplpcnte', ''), 10)
    
    # 16. CEP (apa_ceppcnte - Tam: 8)
    registro += formatar_num(dados_linha.get('apa_ceppcnte', ''), 8)
    
    # 17. Município IBGE (apa_munpcnte - Tam: 7)
    registro += formatar_char(dados_linha.get('apa_munpcnte', ''), 7)
    
    # 18. Data de nascimento (apa_datanascim - Tam: 8)
    registro += formatar_num(dados_linha.get('apa_datanascim', ''), 8)
    
    # 19. Sexo (apa_sexopcnte - Tam: 1)
    registro += formatar_char(dados_linha.get('apa_sexopcnte', ''), 1)
    
    # 20. Nome do médico responsável (apa_nomeresp - Tam: 30)
    registro += formatar_char(dados_linha.get('apa_nomeresp', ''), 30)
    
    # 21. Código procedimento principal (apa_codprinc - Tam: 10)
    registro += formatar_num(dados_linha.get('apa_codprinc', ''), 10)
    
    # 22. Motivo de Saída/Permanência (apa_motsaida - Tam: 2)
    registro += formatar_num(dados_linha.get('apa_motsaida', ''), 2)
    
    # 23. Data óbito/alta/transferência (apa_dtobitoalta - Tam: 8)
    registro += formatar_char(dados_linha.get('apa_dtobitoalta', ''), 8)
    
    # 24. Nome do Profissional autorizador (apa_nomediretor - Tam: 30)
    registro += formatar_char(dados_linha.get('apa_nomediretor', ''), 30)
    
    # 25. CNS Paciente (apa_cnspct - Tam: 15)
    registro += formatar_char(dados_linha.get('apa_cnspct', ''), 15)
    
    # 26. CNS Médico Responsável (apa_cnsres - Tam: 15)
    registro += formatar_num(dados_linha.get('apa_cnsres', ''), 15)
    
    # 27. CNS do Autorizador (apa_cnsdir - Tam: 15)
    registro += formatar_num(dados_linha.get('apa_cnsdir', ''), 15)
    
    # 28. CID Causas Associadas (apa_cidca - Tam: 4)
    registro += formatar_char(dados_linha.get('apa_cidca', ''), 4)
    
    # 29. Número do Prontuário (apa_npront - Tam: 10)
    registro += formatar_char(dados_linha.get('apa_npront', ''), 10)
    
    # 30. Código CNES do Solicitante (apa_codsol - Tam: 7)
    registro += formatar_num(dados_linha.get('apa_codsol', ''), 7)
    
    # 31. Data da solicitação (apa_datsol - Tam: 8)
    registro += formatar_num(dados_linha.get('apa_datsol', ''), 8)
    
    # 32. Data da autorização (apa_dataut - Tam: 8)
    registro += formatar_num(dados_linha.get('apa_dataut', ''), 8)
    
    # 33. Código do emissor (apa_codemis - Tam: 10)
    registro += formatar_char(dados_linha.get('apa_codemis', ''), 10)
    
    # 34. Carater do atendimento (apa_carate - Tam: 2)
    registro += formatar_num(dados_linha.get('apa_carate', ''), 2)
    
    # 35. Número da APAC anterior (apa_apacant - Tam: 13)
    registro += formatar_num(dados_linha.get('apa_apacant', ''), 13)
    
    # 36. Raça/Cor (apa_raca - Tam: 2)
    registro += formatar_num(dados_linha.get('apa_raca', ''), 2)
    
    # 37. Nome do responsável pelo paciente (apa_nomeresp - Tam: 30)
    registro += formatar_char(dados_linha.get('apa_nomeresp_pcte', ''), 30)
    
    # 38. Código da Nacionalidade (apa_nascpcnte - Tam: 3)
    registro += formatar_num(dados_linha.get('apa_nascpcnte', ''), 3)
    
    # 39. Etnia (APA_etnia - Tam: 4)
    registro += formatar_char(dados_linha.get('APA_etnia', ''), 4)
    
    # 40. Código do Logradouro (apa_cdlogr - Tam: 3)
    registro += formatar_num(dados_linha.get('apa_cdlogr', ''), 3)
    
    # 41. Bairro (apa_bairro - Tam: 30)
    registro += formatar_char(dados_linha.get('apa_bairro', ''), 30)
    
    # 42. DDD do telefone (apa_dddtelcontato - Tam: 2)
    registro += formatar_char(dados_linha.get('apa_dddtelcontato', ''), 2)
    
    # 43. Telefone de contato (apa_telcontato - Tam: 9)
    registro += formatar_char(dados_linha.get('apa_telcontato', ''), 9)
    
    # 44. E-Mail do Paciente (apa_email - Tam: 40)
    registro += formatar_char(dados_linha.get('apa_email', ''), 40)
    
    # 45. CNS Médico Executante (apa_cnsexec - Tam: 15)
    registro += formatar_num(dados_linha.get('apa_cnsexec', ''), 15)
    
    # 46. CPF do indivíduo (apa_cpfpcnte - Tam: 11)
    registro += formatar_num(dados_linha.get('apa_cpfpcnte', ''), 11)
    
    # 47. Identificação nacional de equipes (apa_ine - Tam: 10)
    registro += formatar_char(dados_linha.get('apa_ine', ''), 10)
    
    # 48. Pessoa em situação de Rua (apa_strua - Tam: 1)
    registro += formatar_char(dados_linha.get('apa_strua', ''), 1)
    
    # 49. Fim da linha (apa_fim - Tam: 2)
    registro += FIM_LINHA
    
    if len(registro) != 535:
         raise ValueError(f"Erro de formatação no Registro 14: Tamanho incorreto ({len(registro)}).")
    
    return registro