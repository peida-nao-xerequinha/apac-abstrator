import pandas as pd
from datetime import datetime
import os
import sys
import unicodedata

sys.path.append(os.path.dirname(__file__))

from utils import (
    formatar_num,
    formatar_char,
    calcular_idade,
    selecionar_procedimento,
    MAPA_PROCEDIMENTOS_OFTALMO,
    FIM_LINHA,
    mapear_raca_cor,
    sanitize_basic
)

from apac_manager import (
    inicializar_manager,
    consumir_apac,
    salvar_numeracoes,
    salvar_relatorio_intervalo_apac
)

from header import montar_cabecalho
from corpo import montar_corpo
from variavel import montar_laudo_geral
from procedimentos import gerar_bloco_procedimentos


# ======================================================
# CONSTANTES
# ======================================================

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


# ======================================================
# UTILITÁRIOS LOCAIS
# ======================================================

def _converter_data_para_apac(data_str):
    """DD/MM/YYYY -> YYYYMMDD"""
    if isinstance(data_str, (datetime, pd.Timestamp)):
        return data_str.strftime('%Y%m%d')
    try:
        base = str(data_str).split(" ")[0]
        obj = datetime.strptime(base, "%d/%m/%Y")
        return obj.strftime("%Y%m%d")
    except Exception:
        return "00000000"


def remover_acentos_para_ascii(s: str) -> str:
    """
    Normaliza string para caracteres ASCII (remove acentos e símbolos não ASCII).
    Retorna string (pode ficar vazia).
    """
    if s is None:
        return ""
    s = str(s)
    # Normaliza e remove diacríticos; depois remove qualquer caractere não-ascii
    nfkd = unicodedata.normalize('NFKD', s)
    ascii_bytes = nfkd.encode('ASCII', 'ignore')
    return ascii_bytes.decode('ASCII')


def ler_csv_pacientes(fp):
    """Lê CSV de pacientes com tolerância a encoding e padroniza colunas e datas."""
    try:
        df = pd.read_csv(fp, delimiter=";", encoding="latin1")
    except UnicodeDecodeError:
        df = pd.read_csv(fp, delimiter=";", encoding="cp1252")
    except Exception:
        df = pd.read_csv(fp, delimiter=";")

    # Corrige primeira coluna vazia
    if len(df.columns) > 0 and str(df.columns[0]).startswith("Unnamed"):
        df = df.iloc[:, 1:]


    ren = {}
    for col in df.columns:
        if "Hor" in col:
            ren[col] = "Data_Horario"
        elif "Mãe" in col or "MAE" in col or "MÃ£" in col:
            ren[col] = "Mae"
        elif "Ra" in col and "Cor" in col:
            ren[col] = "Raca_Cor"
        elif "Profissional" in col:
            ren[col] = "Nome_Medico_Solicitante"
        elif "Unidade" in col:
            ren[col] = "Nome_Unidade_Solicitante"
        elif "Nascimento" in col:
            ren[col] = "Data_Nascimento"

    if ren:
        df.rename(columns=ren, inplace=True)

    df["Data_Nascimento"] = df.get("Data_Nascimento", "").apply(_converter_data_para_apac)
    df["Data_Horario"] = df.get("Data_Horario", "").apply(_converter_data_para_apac)

    return df


def lookup_medico_cns(nome, df):
    nome_l = sanitize_basic(nome).upper()
    if not nome_l:
        return {"apa_cnsres": formatar_num(0, 15), "nome_completo": ""}

    try:
        match = df[df["nome_completo"].str.upper().str.contains(nome_l, na=False)]
        if not match.empty:
            cns = sanitize_basic(match.iloc[0]["cartao_sus"])
            nm = sanitize_basic(match.iloc[0]["nome_completo"])
            return {"apa_cnsres": formatar_num(cns, 15), "nome_completo": nm}
    except Exception:
        pass

    return {"apa_cnsres": formatar_num(0, 15), "nome_completo": nome_l}


def lookup_cnes_data(unidade, df):
    nome = sanitize_basic(unidade).upper()
    base = CNES_REF_DEFAULTS.copy()
    if not nome:
        base["cnes_solicitante"] = "5778204"
        return base

    try:
        match = df[df["desc_solicitante"].str.upper().str.contains(nome, na=False)]
        if not match.empty:
            cnes = sanitize_basic(match.iloc[0]["cod_solicitante"])
            base["cnes_solicitante"] = formatar_num(cnes, 7)
            return base
    except Exception:
        pass

    base["cnes_solicitante"] = "5778204"
    return base


# ======================================================
# GERAÇÃO DO BLOCO (por paciente)
# ======================================================

def gerar_blocos_paciente(p, apac_num, medico_ref, cnes_ref):
    """
    Gera blocos: corpo (14), laudo (06) e procedimentos (13s) para um paciente.
    """
    cnes_solic = cnes_ref.get("cnes_solicitante", "5778204")
    cnes_terc = " " * 7 if cnes_solic == "5778204" else cnes_solic

    nasc = sanitize_basic(p.get("Data_Nascimento"))
    cons = sanitize_basic(p.get("Data_Horario"))

    if not nasc or len(nasc) != 8:
        raise ValueError(f"Data de nascimento inválida: {nasc}")
    if not cons or len(cons) != 8:
        raise ValueError(f"Data de consulta inválida: {cons}")

    idade = calcular_idade(nasc, cons)

    proc_sel = selecionar_procedimento(idade)
    try:
        cod_princ = next(k for k, v in MAPA_PROCEDIMENTOS_OFTALMO.items() if v == proc_sel)
    except StopIteration:
        raise ValueError("Procedimento principal não encontrado.")

    cod_princ_fmt = cod_princ.replace("-", "")

    raca = mapear_raca_cor(sanitize_basic(p.get("Raca_Cor", "")))

    cid_raw = sanitize_basic(p.get("CID", "")).upper()
    cid = "".join(ch for ch in cid_raw if ch.isalnum())[:4]

    mae = sanitize_basic(p.get("Mae", ""))
    nome_resp = sanitize_basic(p.get("Nome", "")) if idade >= 18 else mae

    dados = {
        "apa_corpo": 14,
        "apa_cmp": formatar_num("202510", 6),
        "apa_num": apac_num,
        "apa_coduf": cnes_ref.get("apa_coduf", CNES_REF_DEFAULTS["apa_coduf"]),
        "apa_codcnes": "5778204",
        "apa_pr": cons,
        "apa_dtiinval": cons,
        "apa_dtfimval": cons,
        "apa_tipate": "00",
        "apa_tipapac": "3",
        "apa_motsaida": "12",
        "apa_dtobitoalta": cons,
        "apa_datsol": cons,
        "apa_dataut": cons,
        "apa_codemis": "M351620001",
        "apa_carate": "01",
        "apa_apacant": "0",
        "apa_nascpcnte": "010",
        "APA_etnia": "",
        "apa_cdlogr": "081",

        "apa_dddtelcontato": formatar_char(sanitize_basic(p.get("DDD")), 2),
        "apa_email": sanitize_basic(p.get("Email", "")),
        "apa_strua": "N",
        "apa_codsol": formatar_char(cnes_solic, 7),
        "apa_npront": "",
        "apa_cplpcnte": "",

        "apa_nomepcnte": sanitize_basic(p.get("Nome", "")),
        "apa_nomemae": mae,
        "apa_nomeresp_pcte": nome_resp,
        "apa_logpcnte": sanitize_basic(p.get("Rua", "")),

        # nº residência: CHAR(5) conforme layout oficial
        "apa_numpcnte": formatar_char(sanitize_basic(p.get("Nro", "")), 5),
        "apa_ceppcnte": formatar_num(sanitize_basic(p.get("CEP", "")), 8),
        "apa_munpcnte": cnes_ref.get("cod_mun_ibge", CNES_REF_DEFAULTS["cod_mun_ibge"]),

        "apa_datanascim": nasc,
        "apa_sexopcnte": sanitize_basic(p.get("Sexo", "I"))[:1] or "I",
        "apa_raca": raca,
        "apa_cpfpcnte": formatar_num(sanitize_basic(p.get("CPF", "")), 11),

        "apa_bairro": sanitize_basic(p.get("Bairro", "")),
        "apa_telcontato": formatar_char(sanitize_basic(p.get("Contato 1", "")), 9),
        "apa_ine": "",

        "cid_paciente": cid,
        "cid_secundario": "",

        "apa_codprinc": cod_princ_fmt,

        "apa_nomediretor": AUTORIZADOR_REF["apa nomediretor"],
        "apa_cnspct": formatar_num(sanitize_basic(p.get("Cartão SUS", "")), 15),
        "apa_cnsres": medico_ref.get("apa_cnsres", formatar_num(0, 15)),
        "apa_cnsdir": AUTORIZADOR_REF["apa cnsdir"],
        "apa_cnsexec": medico_ref.get("apa_cnsres", formatar_num(0, 15)),
        "apa_nomeresp": medico_ref.get("nome_completo", "")
    }

    linhas = []
    linhas.append(montar_corpo(dados))
    linhas.append(montar_laudo_geral(dados["apa_cmp"], apac_num, dados["cid_paciente"]))
    linhas.extend(gerar_bloco_procedimentos(idade, dados["apa_cmp"], apac_num, cnes_terc))

    return linhas


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":

    FP_PACIENTES = "PEDRO.csv"
    FP_MEDICOS = "medicos.csv"
    FP_ESTABELECIMENTOS = "estabelecimentos.csv"

    COMPETENCIA = "202510"
    OUTPUT_FILE = "remessa_final_simulacao.txt"

    print(f"Iniciando simulação para competência {COMPETENCIA}...")
    inicializar_manager()

    try:
        df_p = ler_csv_pacientes(FP_PACIENTES)
    except FileNotFoundError:
        print(f"Arquivo de pacientes não encontrado: {FP_PACIENTES}")
        raise

    df_m = pd.read_csv(FP_MEDICOS, delimiter=";")
    df_e = pd.read_csv(FP_ESTABELECIMENTOS, delimiter=";")

    linhas = []
    primeira = None
    ultima = None
    total = 0

    for idx, paciente in df_p.iterrows():
        apac_num, rest = consumir_apac()
        if not apac_num:
            print("Numerações esgotadas.")
            break

        if primeira is None:
            primeira = apac_num
        ultima = apac_num

        med_ref = lookup_medico_cns(sanitize_basic(paciente.get("Nome_Medico_Solicitante", "")), df_m)
        cnes_ref = lookup_cnes_data(sanitize_basic(paciente.get("Nome_Unidade_Solicitante", "")), df_e)

        try:
            blocos = gerar_blocos_paciente(paciente.to_dict(), apac_num, med_ref, cnes_ref)
            linhas.extend(blocos)
            total += 1
        except Exception as e:
            print(f"\n❌ ERRO ao gerar APAC {apac_num}")
            print(f"Paciente: {sanitize_basic(paciente.get('Nome','(sem nome)'))}")
            print(f"Index linha source: {idx}")
            print(f"Erro: {type(e).__name__}: {e}\n")
            continue

    # Monta header final
    header_final = montar_cabecalho(COMPETENCIA, cnes_ref, total, [], ultima)
    linhas.insert(0, header_final)

    # Antes de salvar: remover acentos e garantir ASCII
    def linha_para_ascii(linha: str) -> str:
        # Montagem final: remover caracteres Unicode que possam quebrar a escrita
        # mantém CRLF que já está dentro de cada registro
        return remover_acentos_para_ascii(linha)

    try:
        with open(OUTPUT_FILE, "wb") as f:
            for l in linhas:
                l_ascii = linha_para_ascii(l)
                f.write(l_ascii.encode("ascii"))
    except Exception as e:
        print(f"ERRO ao salvar arquivo de remessa '{OUTPUT_FILE}': {type(e).__name__}: {e}")
        raise

    salvar_numeracoes()
    salvar_relatorio_intervalo_apac(OUTPUT_FILE, primeira, ultima)

    print("Processamento finalizado.")
    print(f"Arquivo gerado: {OUTPUT_FILE}")
    print(f"Primeira APAC: {primeira}")
    print(f"Última APAC: {ultima}")
