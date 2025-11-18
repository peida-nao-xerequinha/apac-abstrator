import pandas as pd
from datetime import datetime
import os
import sys
import apac_manager

# Adiciona o diretório atual ao path para importar os módulos auxiliares
sys.path.append(os.path.dirname(__file__))

# Importa funções dos módulos auxiliares
from utils import formatar_num, formatar_char, calcular_idade, selecionar_procedimento, MAPA_PROCEDIMENTOS_OFTALMO, FIM_LINHA, mapear_raca_cor
from apac_manager import inicializar_manager, consumir_apac, salvar_numeracoes, salvar_relatorio_intervalo_apac
from header import montar_cabecalho
from corpo import montar_corpo
from variavel import montar_laudo_geral
from procedimentos import gerar_bloco_procedimentos, montar_procedimento

# ========================================================
# CONSTANTES DE REFERÊNCIA (DEFAULTS)
# ========================================================

CNES_REF_DEFAULTS = {
    'apa_coduf': "35",
    'cbc-cgccpf': "47970769000104",
    'cbc-rsp': "PEDRO TRIES",
    'cbc-sgl': "SECRET",
    'cbc-dst': "SMS",
    'cbc-dst-in': "M",
    'cod_mun_ibge': "351620 "
}

AUTORIZADOR_REF = {
    'apa nomediretor': "PABLO DANIEL CHAVEZ LUNA",
    'apa cnsdir': "704800067495842",
}

# ========================================================
# FUNÇÕES DE CONVERSÃO E LEITURA
# ========================================================

def _converter_data_para_apac(data_str):
    if isinstance(data_str, (datetime, pd.Timestamp)):
        return data_str.strftime('%Y%m%d')
    
    data_limpa = str(data_str).split(' ')[0]
    try:
        data_obj = datetime.strptime(data_limpa, '%d/%m/%Y')
        return data_obj.strftime('%Y%m%d')
    except ValueError:
        return '00000000'


def ler_csv_pacientes(filepath):
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
        if 'Data/Horário' in col:
            renaming_dict[col] = 'Data_Horario'
        elif 'MÃ£e' in col or 'MÆe' in col or 'Mãe' in col:
            renaming_dict[col] = 'Mae'
        elif 'Ra‡a/Cor' in col or 'RaÃ§a/Cor' in col or 'Raça/Cor' in col:
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
# LOOKUPS
# ========================================================

def lookup_medico_cns(nome_medico: str, df_medicos: pd.DataFrame) -> dict:
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


def lookup_cnes_data(nome_unidade: str, df_estabelecimentos: pd.DataFrame) -> dict:
    nome_unidade_limpo = nome_unidade.strip().upper()
    cnes_data = CNES_REF_DEFAULTS.copy()

    unidade_encontrada = df_estabelecimentos[
        df_estabelecimentos['desc_solicitante'].str.strip().str.upper().str.contains(nome_unidade_limpo, na=False)
    ]

    if not unidade_encontrada.empty:
        cnes_cod = str(unidade_encontrada['cod_solicitante'].iloc[0])
        cnes_data['cnes_solicitante'] = formatar_num(cnes_cod, 7)
    else:
        cnes_data['cnes_solicitante'] = formatar_num("5778204", 7)

    return cnes_data


# ========================================================
# GERAÇÃO DOS BLOCOS POR PACIENTE
# ========================================================

def gerar_blocos_paciente(paciente_dict, apac_numero, medico_ref, cnes_data):
    CNES_SOLICITANTE = cnes_ref['cnes_solicitante']

    if CNES_SOLICITANTE == '5778204':
        cnes_terceiro_final = formatar_char('', 7)
    else:
        cnes_terceiro_final = CNES_SOLICITANTE

    data_nascimento_fmt = paciente_dict['Data_Nascimento']
    data_consulta_fmt = paciente_dict['Data_Horario']
    competencia = 202510

    nome_mae = paciente_dict.get('Mae', '') or paciente_dict.get('Mãe', '')
    idade = calcular_idade(data_nascimento_fmt, data_consulta_fmt)

    nome_responsavel = paciente_dict['Nome'] if idade >= 18 else nome_mae

    proc_sel = selecionar_procedimento(idade)
    cod_principal = next(key for key, value in MAPA_PROCEDIMENTOS_OFTALMO.items() if value == proc_sel)

    raca_paciente_codigo = mapear_raca_cor(paciente_dict.get('Raca_Cor', ''))

    dados_apac = {
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
        'apa_dddtelcontato': '',
        'apa_email': '',
        'apa_strua': 'N',
        'apa_codsol': CNES_SOLICITANTE,
        'apa_npront': '',
        'apa_cplpcnte': '',

        'apa_nomepcnte': paciente_dict.get('Nome', ''),
        'apa_nomemae': paciente_dict.get('Mae', ''),
        'apa_nomeresp_pcte': nome_responsavel,
        'apa_logpcnte': paciente_dict.get('Rua', ''),
        'apa_numpcnte': str(paciente_dict.get('Nro', '0')),
        'apa_ceppcnte': str(paciente_dict.get('CEP', '0')),
        'apa_munpcnte': cnes_ref['cod_mun_ibge'],
        'apa_datanascim': data_nascimento_fmt,
        'apa_sexopcnte': paciente_dict.get('Sexo', 'I')[0],
        'apa_raca': raca_paciente_codigo,
        'apa_cpfpcnte': str(paciente_dict.get('CPF', '0')),
        'apa_bairro': paciente_dict.get('Bairro', ''),
        'apa_telcontato': str(paciente_dict.get('Contato 1', '')),
        'apa_ine': '',
        'cid_paciente': paciente_dict.get('CID', '').replace('.', ''),

        'apa_codprinc': cod_principal.replace('-', ''),
        'apa_nomediretor': AUTORIZADOR_REF['apa nomediretor'],
        'apa_cnspct': str(paciente_dict.get('Cartão SUS', '')),
        'apa_cnsres': medico_ref['apa_cnsres'],
        'apa_cnsdir': AUTORIZADOR_REF['apa cnsdir'],
        'apa_cnsexec': medico_ref['apa_cnsres'],
        'apa_nomeresp': medico_ref['nome_completo'],
    }

    blocos = []
    blocos.append(montar_corpo(dados_apac))
    blocos.append(montar_laudo_geral(competencia, apac_numero, dados_apac['cid_paciente']))
    blocos.extend(gerar_bloco_procedimentos(idade, competencia, apac_numero, cnes_terceiro_final))

    return blocos


# ========================================================
# MÓDULO PRINCIPAL
# ========================================================

if __name__ == '__main__':

    FP_PACIENTES = "PEDRO.csv"
    FP_MEDICOS = "medicos.csv"
    FP_ESTABELECIMENTOS = "estabelecimentos.csv"

    COMPETENCIA = "202510"
    OUTPUT_FILE = "remessa_final_simulacao.txt"

    print(f"Iniciando simulação para competência {COMPETENCIA}...")

    # INICIALIZAR APACs NA MEMÓRIA
    try:
        inicializar_manager()
    except Exception as e:
        print(f"ERRO CRÍTICO na inicialização do APAC Manager: {e}")
        sys.exit(1)

    try:
        df_pacientes = ler_csv_pacientes(FP_PACIENTES)
        df_medicos = pd.read_csv(FP_MEDICOS, delimiter=';')
        df_estabelecimentos = pd.read_csv(FP_ESTABELECIMENTOS, delimiter=';')
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        sys.exit(1)

    linhas_finais = []
    apacs_processadas = 0

    primeira_apac_usada = None
    ultima_apac_usada = None

    # LOOP PRINCIPAL
    for index, paciente in df_pacientes.iterrows():

        apac_numero_base, restantes = consumir_apac()

        if not apac_numero_base:
            print("Numerações APAC esgotadas.")
            break

        # REGISTRA INTERVALO
        if primeira_apac_usada is None:
            primeira_apac_usada = apac_numero_base
        ultima_apac_usada = apac_numero_base

        dados_paciente = paciente.to_dict()
        nome_medico = dados_paciente['Nome_Medico_Solicitante']
        nome_unidade = dados_paciente['Nome_Unidade_Solicitante']

        medico_ref = lookup_medico_cns(nome_medico, df_medicos)
        cnes_ref = lookup_cnes_data(nome_unidade, df_estabelecimentos)

        try:
            blocos = gerar_blocos_paciente(dados_paciente, apac_numero_base, medico_ref, cnes_ref)
            linhas_finais.extend(blocos)
            apacs_processadas += 1
        except Exception as e:
            print(f"ERRO ao gerar a APAC {apac_numero_base}: {e}")

    # FINALIZA REMESSA
    if linhas_finais:

        lista_procedimentos_para_controle = []
        for linha in linhas_finais:
            if linha.startswith("13"):
                lista_procedimentos_para_controle.append({'cod': '090000000-0', 'qtd': '1'})

        header_final = montar_cabecalho(
            COMPETENCIA,
            cnes_ref,
            apacs_processadas,
            lista_procedimentos_para_controle,
            ultima_apac_usada
        )

        linhas_finais.insert(0, header_final)

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.writelines(linhas_finais)

        print("Processamento Finalizado.")
        salvar_numeracoes()

        # 🔥 AQUI CRIA O ARQUIVO intervalo_apac.txt
        salvar_relatorio_intervalo_apac(
            OUTPUT_FILE,
            primeira_apac_usada,
            ultima_apac_usada
        )

        print(f"Arquivo de remessa salvo em: {OUTPUT_FILE}")
        print(f"Primeira APAC: {primeira_apac_usada}")
        print(f"Última APAC: {ultima_apac_usada}")