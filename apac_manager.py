import os
import sys
import shutil
from datetime import datetime
from typing import List, Tuple

def _caminho_data() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "data")
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

PASTA_DATA = _caminho_data()
os.makedirs(PASTA_DATA, exist_ok=True)

NOME_ARQUIVO_NUMERACAO = os.path.join(PASTA_DATA, "Numeração OCI.TXT")

def backup_arquivo_numeracao(fp_num: str) -> None:
    if not os.path.exists(fp_num):
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_original = os.path.basename(fp_num)
    nome_base, ext = os.path.splitext(nome_original)
    nome_backup = f"{nome_base}_BACKUP_{timestamp}{ext}"
    caminho_backup = os.path.join(os.path.dirname(fp_num), nome_backup)

    try:
        shutil.copyfile(fp_num, caminho_backup)
        print(f"Backup criado: {caminho_backup}")
    except Exception as e:
        print(f"Erro ao criar backup: {e}")

NUMERACOES_APAC_MEMORIA: List[str] = []

def _ler_numeracoes_disco(fp_num: str) -> List[str]:
    numeracoes = []
    if not os.path.exists(fp_num):
        return []

    try:
        with open(fp_num, 'r', encoding='latin1') as f:
            f.readline()
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                if '-' in linha and len(linha) >= 14:
                    base, dv = linha.split('-', 1)
                    apac = base + dv[:1]
                    if len(apac) == 13 and apac.isdigit():
                        numeracoes.append(apac)
                elif len(linha) >= 13 and linha.isdigit():
                    numeracoes.append(linha[:13])
    except Exception as e:
        print(f"ERRO ao ler numerações: {e}")

    return numeracoes


def salvar_numeracoes(fp_num: str) -> None:
    global NUMERACOES_APAC_MEMORIA
    try:
        with open(fp_num, 'w', encoding='latin1') as f:
            f.write("NUMERAÇÃO APAC\n")
            for apac in NUMERACOES_APAC_MEMORIA:
                if len(apac) == 13:
                    f.write(f"{apac[:12]}-{apac[12]}\n")
                else:
                    f.write(f"{apac}\n")
        print(f"Numerações salvas em: {fp_num}")
    except Exception as e:
        print(f"ERRO ao salvar numerações: {e}")


def inicializar_manager(fp_num: str) -> None:
    global NUMERACOES_APAC_MEMORIA
    backup_arquivo_numeracao(fp_num)
    NUMERACOES_APAC_MEMORIA = _ler_numeracoes_disco(fp_num)
    print(f"APAC Manager inicializado → {len(NUMERACOES_APAC_MEMORIA)} numerações disponíveis")


def consumir_apac() -> Tuple[str | None, int]:
    global NUMERACOES_APAC_MEMORIA
    if not NUMERACOES_APAC_MEMORIA:
        return None, 0
    apac = NUMERACOES_APAC_MEMORIA.pop(0)
    return apac, len(NUMERACOES_APAC_MEMORIA)


def devolver_apac(apac_num: str) -> None:
    global NUMERACOES_APAC_MEMORIA
    NUMERACOES_APAC_MEMORIA.insert(0, apac_num)


def get_numeracoes_disponiveis(fp_num: str) -> List[str]:
    return _ler_numeracoes_disco(fp_num)


def salvar_relatorio_intervalo_apac(caminho_remessa: str, primeira_apac: str, ultima_apac: str) -> None:
    try:
        pasta = os.path.dirname(caminho_remessa)
        arquivo = os.path.join(pasta, "intervalo_apac.txt")
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(f"PRIMEIRA_APAC={primeira_apac}\n")
            f.write(f"ULTIMA_APAC={ultima_apac}\n")
        print(f"Intervalo salvo: {arquivo}")
    except Exception as e:
        print(f"Erro ao salvar intervalo: {e}")