import pandas as pd
from datetime import datetime
import os
import sys

# Adiciona o diretório atual ao path para importar os módulos auxiliares
sys.path.append(os.path.dirname(__file__))

# Importa as funções de formatação e lógica de todos os módulos
from utils import formatar_num, formatar_char, calcular_idade, selecionar_procedimento, MAPA_PROCEDIMENTOS_OFTALMO, FIM_LINHA 
from apac_manager import consumir_apac, salvar_numeracoes
from header import montar_cabecalho
from corpo import montar_corpo
from variavel import montar_laudo_geral
from procedimentos import gerar_bloco_procedimentos, montar_procedimento 

# ========================================================
# CONSTANTES DE REFERÊNCIA (DEFAULTS)
# ========================================================

# Dados de referência completos para CNES/Prestador
CNES_REF_DEFAULTS = {
    'apa_coduf': "35",
    'cbc-cgccpf': "47970769000104", 
    'cbc-rsp': "PEDRO TRIES", 
    'cbc-sgl': "SECRET",
    'cbc-dst': "SMS",
    'cbc-dst-in': "M",
    'cod_mun_ibge': "351620 "
}

# Dados de Autorizador (Fixos, que viriam de um lookup ou tela)
AUTORIZADOR_REF = {
    'apa nomediretor': "PABLO DANIEL CHAVEZ LUNA",
    'apa cnsdir': "704800067495842", 
}

# ========================================================
# 1. FUNÇÕES DE CONVERSÃO E LEITURA (INTEGRADAS)
# ========================================================

def _converter_data_para_apac(data_str):
    """Converte a data de 'DD/MM/YYYY' (ou datetime) para 'YYYYMMDD'."""
    if isinstance(data_str, (datetime, pd.Timestamp)):
        return data_str.strftime('%Y%m%d')
    
    data_limpa = str(data_str).split(' ')[0]
    
    try:
        data_obj = datetime.strptime(data_limpa, '%d/%m/%Y')
        return data_obj.strftime('%Y%m%d')
    except ValueError:
        return '00000000'


def ler_csv_pacientes(filepath):
    """
    Carrega o CSV de pacientes, limpa a primeira coluna em branco,
    corrige os nomes das colunas e formata as datas.
    """
    try:
        df = pd.read_csv(filepath, delimiter=';', encoding='latin1')
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, delimiter=';', encoding='cp1252')
    except Exception:
         df = pd.read_csv(filepath, delimiter=';')
    
    if df.columns[0].startswith('Unnamed'):
        df = df.iloc[:, 1:] 

    renaming_dict = {}
    for col in df.columns:
        if 'Data/Hor' in col:
            renaming_dict[col] = 'Data_Horario'
        elif 'MÆe' in col:
            renaming_dict[col] = 'Mae'
        elif 'Ra‡a/Cor' in col:
            renaming_dict[col] = 'Raca_Cor'
        elif 'Profissional' in col:
            renaming_dict[col] = 'Nome_Medico_Solicitante'
        elif 'Unidade' in col:
            renaming_dict[col] = 'Nome_Unidade_Solicitante'
        elif 'Data de Nascimento' in col:
            renaming_dict[col] = 'Data_Nascimento'

    df.rename(columns=renaming_dict, inplace=True)
    
    df['Data_Nascimento'] = df['Data_Nascimento'].apply(_converter_data_para_apac)
    df['Data_Horario'] = df['Data_Horario'].apply(_converter_data_para_apac)

    return df

# ========================================================
# 2. FUNÇÕES DE LOOKUP (Médicos e Estabelecimentos)
# ========================================================

def lookup_medico_cns(nome_medico: str, df_medicos: pd.DataFrame) -> dict:
    """
    Busca o CNS e o nome completo do médico no DataFrame de médicos.
    Retorna CNS formatado (15 dígitos).
    """
    nome_medico_limpo = nome_medico.strip().upper()
    medico_encontrado = df_medicos[
        df_medicos['nome_completo'].str.strip().str.upper().str.contains(nome_medico_limpo, na=False)
    ]
    
    if not medico_encontrado.empty:
        cns = str(medico_encontrado['cartao_sus'].iloc[0])
        nome = medico_encontrado['nome_completo'].iloc[0].strip()
        return {'apa_cnsres': formatar_num(cns, 15), 'nome_completo': nome}
    else:
        return {'apa_cnsres': formatar_num(0, 15), 'nome_completo': nome_medico}


# Correção no lookup_cnes_data (no seu main.py)

def lookup_cnes_data(nome_unidade: str, df_estabelecimentos: pd.DataFrame) -> dict:
    
    nome_unidade_limpo = nome_unidade.strip().upper()
    cnes_data = CNES_REF_DEFAULTS.copy() 

# PRINT 1: Verificar o nome que está sendo usado para a busca (input)
    print(f"\n--- INÍCIO LOOKUP CNES ---")
    print(f"1. Nome da Unidade Buscada (Upper): '{nome_unidade_limpo}'")
    # -----------------------------------------------------------------
   
    unidade_encontrada = df_estabelecimentos[
        df_estabelecimentos['desc_solicitante'].str.strip().str.upper().str.contains(nome_unidade_limpo, na=False)
    ]
    
    # -----------------------------------------------------------------
    # PRINT 2: Verificar o resultado da busca (DataFrame)
    print(f"2. Unidades Encontradas (Total): {len(unidade_encontrada)}")
    # -----------------------------------------------------------------
    
    if not unidade_encontrada.empty:
        cnes_cod = str(unidade_encontrada['cod_solicitante'].iloc[0])
        # CORREÇÃO: Armazena o CNES buscado na chave cnes_solicitante
        cnes_data['cnes_solicitante'] = formatar_num(cnes_cod, 7)
    else:
        # Fallback se não encontrar (usando um CNES padrão para o solicitante)
        cnes_data['cnes_solicitante'] = formatar_num("5556667", 7)

# -----------------------------------------------------------------
    # PRINT 3: Verificar o valor final atribuído
    print(f"3. CNES Solicitante Atribuído: {cnes_data['cnes_solicitante']}")
    print(f"--- FIM LOOKUP CNES ---\n")
    # -----------------------------------------------------------------
        
    return cnes_data


def gerar_blocos_paciente(paciente_dict, apac_numero, medico_ref, cnes_data):
    """Gera o bloco de linhas 14, 06, e 13s para um paciente."""
    
    # CNES Solicitante (BUSCADO)
    CNES_SOLICITANTE = cnes_ref['cnes_solicitante'] # Puxa da chave corrigida no lookup

    # 1. Extração e Formatação de Dados Base
    data_nascimento_fmt = paciente_dict['Data_Nascimento']
    data_consulta_fmt = paciente_dict['Data_Horario']
    competencia = data_consulta_fmt[:6]
    
    # --- CÁLCULOS E REGRAS DE NEGÓCIO ---

    # 1. Tenta a chave 'Mae' (padrão)
    nome_mae_provisorio = paciente_dict.get('Mae', '')

# 2. Se a primeira falhar (vazia ou None), tenta a chave 'Mãe' (com acento)
    if not nome_mae_provisorio:
        nome_mae_provisorio = paciente_dict.get('Mãe', '')

    idade = calcular_idade(data_nascimento_fmt, data_consulta_fmt)
    if idade >= 18:
        nome_responsavel_final = paciente_dict.get('Nome', '')
    else:
        nome_responsavel_final = nome_mae_provisorio
    
    proc_selecionado = selecionar_procedimento(idade)
    cod_principal = next(key for key, value in MAPA_PROCEDIMENTOS_OFTALMO.items() if value == proc_selecionado)

    cid_paciente = paciente_dict.get('CID', '').replace('.', '')
    
    # 2. CRIAÇÃO DO DICIONÁRIO UNIFICADO (COM CHAVES APAC)
    dados_apac_montagem = {
        # CAMPOS FIXOS / REFERÊNCIA
        'apa_corpo': 14, 
        'apa_cmp': competencia, 
        'apa_num': apac_numero,
        'apa_coduf': cnes_ref['apa_coduf'],
        'apa_codcnes': '5778204',
        'apa_pr': data_consulta_fmt,
        'apa_dtiinval': data_consulta_fmt,
        'apa_dtfimval': data_consulta_fmt,
        'apa_tipate': '00', 
        'apa_tipapac': '3', 
        'apa_motsaida': '12', 
        'apa_dtobitoalta': data_consulta_fmt, 
        'apa_datsol': data_consulta_fmt,
        'apa_dataut': data_consulta_fmt,
        'apa_codemis': 'M351620001', 
        'apa_carate': '01', 
        'apa_apacant': '0', 
        'apa_nascpcnte': '010', 
        'APA_etnia': '0000', 
        'apa_cdlogr': '081', 
        'apa_dddtelcontato': '00', 
        'apa_email': '', 
        'apa_strua': 'N',
        'apa_codsol': CNES_SOLICITANTE,
        'apa_cidca': cid_paciente,
        'apa_npront': '',
        'apa_cplpcnte': '',

        # DADOS DO PACIENTE (Convertidos para STR e Mapeados)
        'apa_nomepcnte': paciente_dict.get('Nome', ''),
        'apa_nomemae': paciente_dict.get('Mae', ''),
        'apa_nomeresp_pcte': nome_responsavel_final,
        'apa_logpcnte': paciente_dict.get('Rua', ''),
        'apa_numpcnte': str(paciente_dict.get('Nro', '0')), 
        'apa_ceppcnte': str(paciente_dict.get('CEP', '0')),
        'apa_munpcnte': cnes_ref['cod_mun_ibge'], 
        'apa_datanascim': data_nascimento_fmt, 
        'apa_sexopcnte': paciente_dict.get('Sexo', 'I')[0], 
        'apa_raca': paciente_dict.get('Raca_Cor', '01'), 
        'apa_cpfpcnte': str(paciente_dict.get('CPF', '0')), 
        'apa_bairro': paciente_dict.get('Bairro', ''),
        'apa_telcontato': str(paciente_dict.get('Contato 1', '0')),
        'apa_ine': '',

        # DADOS PROFISSIONAIS (Mapeados dos Lookups)
        'apa_codprinc': cod_principal.replace('-', ''),
        'apa_nomediretor': AUTORIZADOR_REF['apa nomediretor'],
        'apa_cnspct': str(paciente_dict.get('Cartão SUS', '')),
        'apa_cnsres': medico_ref['apa_cnsres'],
        'apa_cnsdir': AUTORIZADOR_REF['apa cnsdir'],
        'apa_cnsexec': medico_ref['apa_cnsres'],
        'apa_nomeresp': medico_ref['nome_completo'],
    }
    
    print(f"--- Dicionário Final de Dados Antes da Formatação ---\n{dados_apac_montagem}")
    
    # 3. Geração das Linhas
    blocos = []
    
    # Registro 14: CORPO
    blocos.append(montar_corpo(dados_apac_montagem)) 
    
    # Registro 06: LAUDO GERAL
    blocos.append(montar_laudo_geral(competencia, apac_numero, dados_apac_montagem['apa_cidca'])) # Usa o CID do paciente
    
    # Registros 13: PROCEDIMENTOS (Principal + Secundários)
    blocos.extend(gerar_bloco_procedimentos(idade, competencia, apac_numero, CNES_SOLICITANTE))
            
    return blocos


if __name__ == '__main__':
    # --- SIMULAÇÃO DE ENTRADA ---
    FP_PACIENTES = "PEDRO.csv"
    FP_MEDICOS = "medicos.csv"
    FP_ESTABELECIMENTOS = "estabelecimentos.csv"
    
    COMPETENCIA = "202509"
    OUTPUT_FILE = "remessa_final_simulacao.txt"
    
    print(f"Iniciando simulação para competência {COMPETENCIA}...")

    # 1. Carregar Arquivos
    try:
        df_pacientes = ler_csv_pacientes(FP_PACIENTES)
        df_medicos = pd.read_csv(FP_MEDICOS, delimiter=';')
        df_estabelecimentos = pd.read_csv(FP_ESTABELECIMENTOS, delimiter=';')
    except FileNotFoundError as e:
        print(f"ERRO CRÍTICO: Arquivo de referência não encontrado: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERRO CRÍTICO na leitura de arquivos: {e}")
        sys.exit(1)
        
    # 2. Consumir Numerações APAC
    NUMERACOES_APAC = [f"352570410000{i:03}" for i in range(1, 11)] 
    
    linhas_finais = []
    apacs_processadas = 0
    
    # 3. LOOP DE PROCESSAMENTO
    for index, paciente in df_pacientes.iterrows():
        if not NUMERACOES_APAC:
            print("AVISO: Numerações APAC esgotadas.")
            break
            
        apac_numero_base = NUMERACOES_APAC.pop(0) 

        # 3.1. Enriquecimento de Dados
        dados_paciente = paciente.to_dict()
        nome_medico = dados_paciente['Nome_Medico_Solicitante']
        nome_unidade = dados_paciente['Nome_Unidade_Solicitante']
        
        medico_ref = lookup_medico_cns(nome_medico, df_medicos)
        cnes_ref = lookup_cnes_data(nome_unidade, df_estabelecimentos)
        
        # 3.2. Geração do Bloco
        try:
            blocos = gerar_blocos_paciente(dados_paciente, apac_numero_base, medico_ref, cnes_ref)
            linhas_finais.extend(blocos)
            apacs_processadas += 1
            print(f"-> APAC gerada para {dados_paciente['Nome']}. Numeração: {apac_numero_base}")
        except Exception as e:
            print(f"ERRO FATAL NA GERAÇÃO DA APAC {apac_numero_base}: {e}")
            
    # 4. Montar Cabeçalho Final e Salvar
    if linhas_finais:
        
        # O CNES TERC (CNES Solicitante) é usado para calcular o controle do cabeçalho.
        
        # Reconstrução da lista de procedimentos para o cálculo do Campo de Controle
        lista_procedimentos_para_controle = []
        for linha in linhas_finais:
            if linha.startswith("13"):
                 # Simplesmente usamos um dicionário {cod: 0, qtd: 0} para o cálculo simulado
                 # Este é um ponto fraco na simulação, pois o código real precisa extrair o cod e qtd da linha 13.
                 # Para o teste, usamos um valor fixo.
                 lista_procedimentos_para_controle.append({'cod': '090000000-0', 'qtd': '1'})
        
        # Usamos o último apac_numero_base consumido no loop.
        header_final = montar_cabecalho(COMPETENCIA, cnes_ref, apacs_processadas, lista_procedimentos_para_controle, apac_numero_base) 
        
        linhas_finais.insert(0, header_final)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.writelines(linhas_finais)
        
        print("\nProcessamento Finalizado.")
        print(f"Total de APACs geradas: {apacs_processadas}")
        print(f"Arquivo de remessa salvo em: {OUTPUT_FILE}")