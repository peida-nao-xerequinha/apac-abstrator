from datetime import datetime
from utils import formatar_num, formatar_char, FIM_LINHA, calcular_campo_controle

def montar_cabecalho(competencia, cnes_dados, total_apacs_gravadas, lista_procedimentos, apac_numero):
    """
    Monta o registro 01 (CABEÇALHO). Tamanho total: 139 (137 dados + FIM_LINHA).
    
    Argumentos:
        competencia (str): Mês de produção (YYYYMM).
        cnes_dados (dict): Dados do CNES/Prestador.
        total_apacs_gravadas (int): Contagem de APACs a serem geradas no arquivo.
        lista_procedimentos (list): Lista de todos os procedimentos para cálculo do controle. <--- NOVO
        apac_numero (str): Número da primeira APAC para cálculo do controle. <--- NOVO
    """
    competencia_fmt = formatar_num(competencia, 6)
    data_geracao = datetime.now().strftime("%Y%m%d")
    
    # Dados de Referência CNES (Mapeamento)
    nome_orgao = cnes_dados.get('cbc-rsp', 'PEDRO TRIES')
    sigla_orgao = cnes_dados.get('cbc-sgl', 'SECRET')
    cgc_prestador = cnes_dados.get('cbc-cgccpf', '47970769000104')
    nome_destino = cnes_dados.get('cbc-dst', 'SMS')
    indicador_destino = cnes_dados.get('cbc-dst-in', 'M')

    # NOVO: Calcula o Campo de Controle, chamando a função com os argumentos
    campo_controle = calcular_campo_controle(lista_procedimentos, apac_numero)

    registro = "01" # 1. Indicador de linha 01 (2)
    registro += formatar_char("#APAC", 5) # 2. CHAR #APAC (5)
    registro += competencia_fmt # 3. Ano e mês da produção (6)
    registro += formatar_num(total_apacs_gravadas, 6) # 4. Quantidade de APACs gravadas (6)
    registro += campo_controle # 5. Campo de controle (4) <--- FUNÇÃO CORRETAMENTE CHAMADA
    registro += formatar_char(nome_orgao, 30) # 6. Nome do órgão de origem (30)
    registro += formatar_char(sigla_orgao, 6) # 7. Sigla ou código do órgão (6)
    registro += formatar_num(cgc_prestador, 14) # 8. CGC/CPF do prestador (14)
    registro += formatar_char(nome_destino, 40) # 9. Nome do órgão de destino (40)
    registro += formatar_char(indicador_destino, 1) # 10. Indicador de destino (1)
    registro += formatar_num(data_geracao, 8) # 11. Data de geração (8)
    registro += formatar_char("VERSAO 03.18", 15) # 12. Versão (15)
    registro += FIM_LINHA # Fim da linha (2)
    
    if len(registro) != 139:
         raise ValueError(f"Erro de formatação no Registro 01: Tamanho incorreto ({len(registro)}).")
    return registro