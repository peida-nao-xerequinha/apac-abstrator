import os
import sys
import unicodedata
import threading
import locale
import pandas as pd
from datetime import datetime
from PySide6 import QtCore, QtWidgets, QtGui

if getattr(sys, 'frozen', False):
    APPLICATION_PATH = os.path.dirname(sys.executable)
else:
    APPLICATION_PATH = os.path.dirname(os.path.abspath(__file__))

BASE_DIR    = APPLICATION_PATH
DATA_DIR    = os.path.join(BASE_DIR, "data")
INPUT_DIR   = os.path.join(BASE_DIR, "input")
OUTPUT_DIR  = os.path.join(BASE_DIR, "output")
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

if getattr(sys, 'frozen', False):
    qt_plugins = os.path.join(BASE_DIR, "PySide6", "plugins")
    if os.path.isdir(qt_plugins):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_plugins

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
    salvar_relatorio_intervalo_apac,
    get_numeracoes_disponiveis,
    devolver_apac,
    NUMERACOES_APAC_MEMORIA
)

from header import montar_cabecalho
from corpo import montar_corpo
from variavel import montar_laudo_geral
from procedimentos import gerar_bloco_procedimentos

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

COR_BG = "#0b0b0b"
COR_CARD = "#0f0f12"
COR_ACCENT = "#00e0ff"
COR_TEXT = "#e6eef6"
FONT = "Segoe UI"
COR_PRINCIPAL = "#101015"

def _converter_data_para_apac(data_str):
    if isinstance(data_str, (datetime, pd.Timestamp)):
        return data_str.strftime('%Y%m%d')
    try:
        base = str(data_str).split(" ")[0]
        obj = datetime.strptime(base, "%d/%m/%Y")
        return obj.strftime("%Y%m%d")
    except Exception:
        return "00000000"

def remover_acentos_para_ascii(s: str) -> str:
    if s is None:
        return ""
    return unicodedata.normalize('NFKD', str(s)).encode('ASCII', 'ignore').decode("ASCII")

def ler_csv_pacientes(fp):
    try:
        df = pd.read_csv(fp, delimiter=";", encoding="latin1")
    except UnicodeDecodeError:
        df = pd.read_csv(fp, delimiter=";", encoding="cp1252")
    except Exception:
        df = pd.read_csv(fp, delimiter=";")
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
    base = {
        'apa_coduf': "35",
        'cbc-cgccpf': "47970769000104",
        'cbc-rsp': "PEDRO TRIES",
        'cbc-sgl': "SECRET",
        'cbc-dst': "SMS",
        'cbc-dst-in': "M",
        'cod_mun_ibge': "351620 ",
        'cnes_solicitante': "5778204"
    }
    if not nome:
        return base
    try:
        match = df[df["desc_solicitante"].str.upper().str.contains(nome, na=False)]
        if not match.empty:
            cnes = sanitize_basic(match.iloc[0]["cod_solicitante"])
            base["cnes_solicitante"] = formatar_num(cnes, 7)
            return base
    except Exception:
        pass
    return base

def gerar_blocos_paciente(p, apac_num, medico_ref, cnes_ref, competencia):
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
    cod_princ = next(k for k, v in MAPA_PROCEDIMENTOS_OFTALMO.items() if v == proc_sel)
    cod_princ_fmt = cod_princ.replace("-", "")
    raca = mapear_raca_cor(sanitize_basic(p.get("Raca_Cor", "")))
    cid_raw = sanitize_basic(p.get("CID", "")).upper()
    cid = "".join(ch for ch in cid_raw if ch.isalnum())[:4]
    mae = sanitize_basic(p.get("Mae", ""))
    nome_resp = sanitize_basic(p.get("Nome", "")) if idade >= 18 else mae
    dados = {
        "apa_corpo": 14,
        "apa_cmp": formatar_num(competencia, 6),
        "apa_num": apac_num,
        "apa_coduf": cnes_ref.get("apa_coduf", "35"),
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
        "apa_numpcnte": formatar_char(sanitize_basic(p.get("Nro", "")), 5),
        "apa_ceppcnte": formatar_num(sanitize_basic(p.get("CEP", "")), 8),
        "apa_munpcnte": cnes_ref.get("cod_mun_ibge", "351620 "),
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
        "apa_nomediretor": "PABLO DANIEL CHAVEZ LUNA",
        "apa_cnspct": formatar_num(sanitize_basic(p.get("Cartão SUS", "")), 15),
        "apa_cnsres": medico_ref.get("apa_cnsres", formatar_num(0, 15)),
        "apa_cnsdir": "704800067495842",
        "apa_cnsexec": medico_ref.get("apa_cnsres", formatar_num(0, 15)),
        "apa_nomeresp": medico_ref.get("nome_completo", "")
    }
    linhas = []
    linhas.append(montar_corpo(dados))
    linhas.append(montar_laudo_geral(dados["apa_cmp"], apac_num, dados["cid_paciente"]))
    linhas.extend(gerar_bloco_procedimentos(idade, dados["apa_cmp"], apac_num, cnes_terc))
    return linhas

def processar_remessa(fp_pacientes, competencia, versao, atualizar_status=None, fp_num_apac=None, fp_medicos=None, fp_estab=None):
    
    FP_MEDICOS = fp_medicos or os.path.join(DATA_DIR, "medicos.csv")
    FP_ESTAB = fp_estab or os.path.join(DATA_DIR, "estabelecimentos.csv")
    
    inicializar_manager(fp_num_apac)
    
    df_p = ler_csv_pacientes(fp_pacientes)
    df_m = pd.read_csv(FP_MEDICOS, delimiter=";") if os.path.exists(FP_MEDICOS) else pd.DataFrame()
    df_e = pd.read_csv(FP_ESTAB, delimiter=";") if os.path.exists(FP_ESTAB) else pd.DataFrame()
    linhas = []
    primeira = None
    ultima = None
    total = 0
    cnes_ref_header = lookup_cnes_data("", df_e)
    
    for idx, paciente in df_p.iterrows():
        
        apac_num_tentativa, rest = consumir_apac()
        
        if not apac_num_tentativa:
            raise Exception("Numerações APAC esgotadas.")
            
        med_ref = lookup_medico_cns(sanitize_basic(paciente.get("Nome_Medico_Solicitante", "")), df_m)
        cnes_ref = lookup_cnes_data(sanitize_basic(paciente.get("Nome_Unidade_Solicitante", "")), df_e)
        cnes_ref_header = cnes_ref
        
        paciente_nome = sanitize_basic(paciente.get("Nome", f"Linha {idx+1}"))
        
        try:
            blocos = gerar_blocos_paciente(paciente.to_dict(), apac_num_tentativa, med_ref, cnes_ref, competencia)
            
            if primeira is None:
                primeira = apac_num_tentativa
            ultima = apac_num_tentativa
            linhas.extend(blocos)
            total += 1
            
            if atualizar_status:
                atualizar_status(total)
                
        except Exception as e:
            devolver_apac(apac_num_tentativa)
            
            if atualizar_status:
                QtCore.QMetaObject.invokeMethod(MainWindow.instance(), 'adicionar_historico', QtCore.Qt.QueuedConnection, 
                                                QtCore.Q_ARG(str, f"⚠️ ERRO ({apac_num_tentativa}): Falha no paciente '{paciente_nome}': {str(e).splitlines()[0]}"))
            
            continue
            
    header_final = montar_cabecalho(competencia, cnes_ref_header, total, [], ultima, versao)
    linhas.insert(0, header_final)
    OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"oci_oftalmo_{competencia}.txt")
    with open(OUTPUT_FILE, "wb") as f:
        for l in linhas:
            f.write(remover_acentos_para_ascii(l).encode("ascii"))
            
    salvar_numeracoes(fp_num_apac)
    salvar_relatorio_intervalo_apac(OUTPUT_FILE, primeira, ultima)
    
    return OUTPUT_FILE, total, primeira, ultima

class MainWindow(QtWidgets.QMainWindow):
    historico_signal = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        
        self.FP_NUMERACAO = os.path.join(DATA_DIR, "Numeração OCI.TXT")
        self.FP_MEDICOS = os.path.join(DATA_DIR, "medicos.csv")
        self.FP_ESTAB = os.path.join(DATA_DIR, "estabelecimentos.csv")
        
        num_oci = len(get_numeracoes_disponiveis(self.FP_NUMERACAO))
        
        self.setWindowTitle("Gerador de Remessa APAC")
        icon_path = os.path.join(ASSETS_DIR, "mini.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        self.resize(800, 560)
        self.setStyleSheet(f"background-color: {COR_BG}; color: {COR_TEXT}; font-family: {FONT};")
        
        MainWindow._instance = self 
        
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(8,8,8,8)
        main_layout.setSpacing(8)

        header = QtWidgets.QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"background-color: {COR_CARD}; border-radius:6px;")
        h_layout = QtWidgets.QVBoxLayout(header)
        h_layout.setContentsMargins(8,6,8,6)
        title = QtWidgets.QLabel("Secretaria Municipal de Saúde de Franca/SP")
        title.setStyleSheet(f"color: {COR_TEXT}; font-size:15pt; font-weight:700;")
        subtitle = QtWidgets.QLabel("Gerador de Remessa APAC - OCI Oftalmológica")
        subtitle.setStyleSheet(f"color: {COR_TEXT}; font-size:9pt;")
        h_layout.addWidget(title)
        h_layout.addWidget(subtitle)
        main_layout.addWidget(header)

        content = QtWidgets.QFrame()
        content.setStyleSheet(f"background-color: {COR_CARD}; border-radius:6px;")
        c_layout = QtWidgets.QHBoxLayout(content)
        c_layout.setContentsMargins(8,8,8,8)
        c_layout.setSpacing(8)
        main_layout.addWidget(content, 1)

        left = QtWidgets.QFrame()
        left.setStyleSheet(f"background:{COR_PRINCIPAL}; border-radius:6px;")
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setSpacing(6)
        c_layout.addWidget(left, 1)

        lbl_csv = QtWidgets.QLabel("CSV Pacientes")
        lbl_csv.setStyleSheet(f"color:{COR_TEXT}; font-weight:600;")
        left_layout.addWidget(lbl_csv)
        self.entry_csv = QtWidgets.QLineEdit()
        self.entry_csv.setPlaceholderText("Selecione o arquivo CSV...")
        self.entry_csv.setStyleSheet("background:#0b0b0b; color: #e6eef6; padding:6px;")
        left_layout.addWidget(self.entry_csv)
        btn_select = QtWidgets.QPushButton("Selecionar CSV")
        btn_select.setStyleSheet(f"background:{COR_ACCENT}; color:#001018; padding:6px; border-radius:6px;")
        btn_select.clicked.connect(self.selecionar_csv)
        left_layout.addWidget(btn_select)

        lbl_orientacao = QtWidgets.QLabel(
            "Veja o arquivo modelo de pacientes em /data/modelo_input.csv"
        )
        lbl_orientacao.setWordWrap(True)
        lbl_orientacao.setStyleSheet(f"color:#ffeb3b; font-size:8pt; padding:4px;")
        left_layout.addWidget(lbl_orientacao)
        
        lbl_data_files = QtWidgets.QLabel("Caminhos dos Arquivos de Dados")
        lbl_data_files.setStyleSheet(f"color:{COR_ACCENT}; font-weight:600; margin-top:8px;")
        left_layout.addWidget(lbl_data_files)
        
        lbl_num = QtWidgets.QLabel("Numeração APAC (TXT)")
        lbl_num.setStyleSheet(f"color:{COR_TEXT}; font-size:9pt; margin-top:4px;")
        left_layout.addWidget(lbl_num)
        self.entry_numeracao = QtWidgets.QLineEdit()
        self.entry_numeracao.setText(self.FP_NUMERACAO)
        self.entry_numeracao.setStyleSheet("background:#0b0b0b; color: #e6eef6; padding:4px; font-size:9pt;")
        left_layout.addWidget(self.entry_numeracao)
        
        lbl_med = QtWidgets.QLabel("Médicos (CSV)")
        lbl_med.setStyleSheet(f"color:{COR_TEXT}; font-size:9pt; margin-top:4px;")
        left_layout.addWidget(lbl_med)
        self.entry_medicos = QtWidgets.QLineEdit()
        self.entry_medicos.setText(self.FP_MEDICOS)
        self.entry_medicos.setStyleSheet("background:#0b0b0b; color: #e6eef6; padding:4px; font-size:9pt;")
        left_layout.addWidget(self.entry_medicos)
        
        lbl_est = QtWidgets.QLabel("Estabelecimentos (CSV)")
        lbl_est.setStyleSheet(f"color:{COR_TEXT}; font-size:9pt; margin-top:4px;")
        left_layout.addWidget(lbl_est)
        self.entry_estab = QtWidgets.QLineEdit()
        self.entry_estab.setText(self.FP_ESTAB)
        self.entry_estab.setStyleSheet("background:#0b0b0b; color: #e6eef6; padding:4px; font-size:9pt;")
        left_layout.addWidget(self.entry_estab)
        
        self.entry_numeracao.textChanged.connect(self.atualizar_contagem_apac)
        
        self.lbl_numeracoes = QtWidgets.QLabel(
        f"Numerações APAC disponíveis: {num_oci}"
        )
        self.lbl_numeracoes.setStyleSheet(
        "color:#9be7ff; font-size:9pt; padding:3px;"
        )
        left_layout.addWidget(self.lbl_numeracoes)
        left_layout.addStretch()

        right = QtWidgets.QFrame()
        right.setStyleSheet(f"background:{COR_PRINCIPAL}; border-radius:6px;")
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setSpacing(6)
        c_layout.addWidget(right, 1)

        lbl_comp = QtWidgets.QLabel("Competência (AAAAMM)")
        lbl_comp.setStyleSheet(f"color:{COR_TEXT}; font-weight:600;")
        right_layout.addWidget(lbl_comp)
        self.entry_comp = QtWidgets.QLineEdit()
        self.entry_comp.setText(datetime.now().strftime("%Y%m"))
        self.entry_comp.setStyleSheet("background:#0b0b0b; color: #e6eef6; padding:6px;")
        self.entry_comp.setInputMask("000000")
        self.entry_comp.setPlaceholderText("AAAAMM")
        right_layout.addWidget(self.entry_comp)

        lbl_vers = QtWidgets.QLabel("Versão do layout (03.XX)")
        lbl_vers.setStyleSheet(f"color:{COR_TEXT}; font-weight:600;")
        right_layout.addWidget(lbl_vers)
        self.entry_vers = QtWidgets.QLineEdit()
        self.entry_vers.setText("03.18")
        self.entry_vers.setStyleSheet("background:#0b0b0b; color: #e6eef6; padding:6px;")
        self.entry_vers.setInputMask("99.99")
        regex = QtCore.QRegularExpression(r"^\d{2}\.\d{2}$")
        validator = QtGui.QRegularExpressionValidator(regex)
        self.entry_vers.setValidator(validator)
        right_layout.addWidget(self.entry_vers)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background: #061718; color: {COR_TEXT}; border-radius:6px; height: 16px; }}
            QProgressBar::chunk {{ background: {COR_ACCENT}; border-radius:6px; }}
        """)
        right_layout.addWidget(self.progress)

        self.status_label = QtWidgets.QLabel("Status: aguardando")
        self.status_label.setStyleSheet(f"color:{COR_TEXT};")
        right_layout.addWidget(self.status_label)

        lbl_hist = QtWidgets.QLabel("Histórico de Processamento:")
        lbl_hist.setStyleSheet(f"color:{COR_TEXT}; margin-top: 6px;")
        right_layout.addWidget(lbl_hist)

        self.historico_text = QtWidgets.QTextEdit()
        self.historico_text.setReadOnly(True)
        self.historico_text.setText(f"Início: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        self.historico_text.setStyleSheet("background:#0b0b0b; color: #e6eef6; border: none; font-size: 8pt;")
        right_layout.addWidget(self.historico_text)

        self.historico_signal.connect(self.adicionar_historico)

        self.btn_gerar = QtWidgets.QPushButton("GERAR REMESSA APAC")
        self.btn_gerar.setStyleSheet(f"background:#05a37a; color:#fff; padding:10px; border-radius:6px; font-weight:700;")
        self.btn_gerar.setFixedHeight(40)
        self.btn_gerar.clicked.connect(self.iniciar_processamento)
        main_layout.addWidget(self.btn_gerar)

        footer = QtWidgets.QFrame()
        footer.setFixedHeight(40)
        footer.setStyleSheet(f"background:{COR_CARD}; border-radius:6px;")
        f_layout = QtWidgets.QHBoxLayout(footer)
        f_layout.setContentsMargins(8,6,8,6)
        self.assinatura = QtWidgets.QLabel("Desenvolvido por PH")
        self.assinatura.setStyleSheet(f"color:{COR_TEXT};")
        f_layout.addWidget(self.assinatura)
        f_layout.addStretch()
        self.relogio = QtWidgets.QLabel("")
        self.relogio.setStyleSheet(f"color:{COR_TEXT};")
        f_layout.addWidget(self.relogio)
        main_layout.addWidget(footer)

        self.update_clock()
        self.btn_gerar.setEnabled(True)

    @staticmethod
    def instance():
        return MainWindow._instance

    @QtCore.Slot(str)
    def adicionar_historico(self, texto):
        self.historico_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {texto}")

    def selecionar_csv(self):
        start_dir = INPUT_DIR if os.path.isdir(INPUT_DIR) else BASE_DIR
        fp, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Selecione o CSV de Pacientes", start_dir, "CSV Files (*.csv)")
        if fp:
            self.entry_csv.setText(fp)
            
    def atualizar_contagem_apac(self):
        fp_num = self.entry_numeracao.text().strip()
        num_oci = 0
        try:
            num_oci = len(get_numeracoes_disponiveis(fp_num))
        except Exception:
            pass
        self.lbl_numeracoes.setText(f"Numerações APAC disponíveis: {num_oci}")


    def validar_campos(self):
        fp = self.entry_csv.text().strip()
        comp = self.entry_comp.text().strip()
        vers = self.entry_vers.text().strip()
        fp_num = self.entry_numeracao.text().strip()
        fp_med = self.entry_medicos.text().strip()
        fp_est = self.entry_estab.text().strip()
        
        if not fp or not os.path.isfile(fp):
            QtWidgets.QMessageBox.critical(self, "Erro", "Selecione um CSV de Pacientes válido.")
            return False
        if not fp_num or not os.path.isfile(fp_num):
            QtWidgets.QMessageBox.critical(self, "Erro", "Caminho do arquivo de Numeração APAC inválido.")
            return False
        if not fp_med or not os.path.isfile(fp_med):
            QtWidgets.QMessageBox.critical(self, "Erro", "Caminho do arquivo de Médicos inválido.")
            return False
        if not fp_est or not os.path.isfile(fp_est):
            QtWidgets.QMessageBox.critical(self, "Erro", "Caminho do arquivo de Estabelecimentos inválido.")
            return False
        if not (len(comp) == 6 and comp.isdigit()):
            QtWidgets.QMessageBox.critical(self, "Erro", "Competência inválida (AAAAMM).")
            return False
        if not (len(vers) == 5 and vers[2] == "." and vers.replace(".", "").isdigit()):
            QtWidgets.QMessageBox.critical(self, "Erro", "Versão inválida (NN.NN).")
            return False
            
        return True

    def update_clock(self):
        self.relogio.setText(datetime.now().strftime("%A, %d/%m/%Y %H:%M:%S"))
        QtCore.QTimer.singleShot(1000, self.update_clock)

    def iniciar_processamento(self):
        if not self.validar_campos():
            return
            
        fp_pacientes = self.entry_csv.text().strip()
        comp = self.entry_comp.text().strip()
        vers = self.entry_vers.text().strip()
        fp_num = self.entry_numeracao.text().strip()
        fp_med = self.entry_medicos.text().strip()
        fp_est = self.entry_estab.text().strip()
        
        self.historico_signal.emit(f"Iniciando processamento para Comp. {comp}...")
        self.historico_signal.emit(f"Numeração lida de: {os.path.basename(fp_num)}")
        
        try:
            df = ler_csv_pacientes(fp_pacientes)
            total = len(df.index)
            self.historico_signal.emit(f"CSV lido: {total} registros encontrados.")
        except Exception as e:
            self.historico_signal.emit(f"ERRO ao ler CSV: {e}")
            total = 1
            
        self.progress.setValue(0)
        self.status_label.setText("Status: iniciando...")
        self.btn_gerar.setEnabled(False)
        
        threading.Thread(target=self._worker, 
                         args=(fp_pacientes, comp, vers, total, fp_num, fp_med, fp_est), 
                         daemon=True).start()

    def _worker(self, fp_pacientes, comp, vers, total, fp_num, fp_med, fp_est):
        def atualizar_status(n):
            try:
                pct = int((n / max(1, total)) * 100)
                QtCore.QMetaObject.invokeMethod(self.progress, "setValue", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(int, pct))
                QtCore.QMetaObject.invokeMethod(self.status_label, "setText", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"Status: geradas {n}/{total}"))
            except Exception:
                QtCore.QMetaObject.invokeMethod(self.status_label, "setText", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"Status: geradas {n}"))
        try:
            arq, total_geradas, primeira, ultima = processar_remessa(
                fp_pacientes, comp, vers, atualizar_status=atualizar_status,
                fp_num_apac=fp_num, fp_medicos=fp_med, fp_estab=fp_est
            )
            
            QtCore.QMetaObject.invokeMethod(self, "_on_finished", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(str, arq), QtCore.Q_ARG(int, total_geradas),
                                            QtCore.Q_ARG(str, str(primeira)), QtCore.Q_ARG(str, str(ultima)))

        except Exception as e:
            QtCore.QMetaObject.invokeMethod(self, "_on_error", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, str(e)))

    @QtCore.Slot(str, int, str, str)
    def _on_finished(self, arq, total_geradas, primeira, ultima): 
        self.progress.setValue(100)
        self.status_label.setText(f"Concluído: {total_geradas} APACs ({primeira} → {ultima})")
        self.historico_signal.emit(f"✅ SUCESSO! Arq.: {arq}, {total_geradas} APACs.")
        
        self.atualizar_contagem_apac()
        
        QtWidgets.QMessageBox.information(self, "Sucesso", f"Arquivo gerado: {arq}\nTotal APACs: {total_geradas}\n{primeira} → {ultima}")
        self.btn_gerar.setEnabled(True)

    @QtCore.Slot(str)
    def _on_error(self, msg):
        self.progress.setValue(0)
        self.status_label.setText("Status: Erro!")
        self.historico_signal.emit(f"❌ ERRO: {msg.splitlines()[0]}")
        
        self.atualizar_contagem_apac()
        
        QtWidgets.QMessageBox.critical(self, "Erro", msg)
        self.btn_gerar.setEnabled(True)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())