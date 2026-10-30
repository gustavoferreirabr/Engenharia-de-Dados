#!/usr/bin/env python3
"""
run_pipeline.py
───────────────────────────────────────────────────────────────────
Orquestrador do pipeline Engenharia de Dados.

Executa todos os notebooks em sequência, exibe progresso em tempo
real, registra logs em arquivo e para imediatamente se qualquer
etapa falhar.

Uso:
    python run_pipeline.py              # roda etapas 1-7
    python run_pipeline.py --full       # inclui etapa 8 (Google Sheets)
    python run_pipeline.py --from 3     # começa a partir do notebook 03
    python run_pipeline.py --only 7     # roda apenas o notebook 07
"""

import subprocess
import sys
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DE CAMINHOS
# ─────────────────────────────────────────────────────────────────────────────
RAIZ       = Path(__file__).parent
NOTEBOOKS  = RAIZ / "notebooks"
LOGS_DIR   = RAIZ / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# DEFINIÇÃO DO PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
PIPELINE = [
    {
        "id":       1,
        "notebook": "01_tratamento_clientes.ipynb",
        "descricao": "Tratamento de Clientes",
        "obrigatorio": True,
    },
    {
        "id":       2,
        "notebook": "02_tratamento_assinaturas.ipynb",
        "descricao": "Tratamento de Assinaturas",
        "obrigatorio": True,
    },
    {
        "id":       3,
        "notebook": "03_tratamento_interacoes.ipynb",
        "descricao": "Tratamento de Interações",
        "obrigatorio": True,
    },
    {
        "id":       4,
        "notebook": "04_tratamento_pagamento.ipynb",
        "descricao": "Tratamento de Pagamentos",
        "obrigatorio": True,
    },
    {
        "id":       5,
        "notebook": "05_tratamento_planos.ipynb",
        "descricao": "Tratamento de Planos",
        "obrigatorio": True,
    },
    {
        "id":       6,
        "notebook": "06_validacao_integridade.ipynb",
        "descricao": "Validação de Integridade (Silver)",
        "obrigatorio": True,
    },
    {
        "id":       7,
        "notebook": "07_camada_gold.ipynb",
        "descricao": "Geração da Camada Gold",
        "obrigatorio": True,
    },
    {
        "id":       8,
        "notebook": "08_publicacao_planilhas.ipynb",
        "descricao": "Publicação no Google Sheets",
        "obrigatorio": False,   # Requer credenciais Google — opt-in via --full
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────
def configurar_logging(run_id: str) -> logging.Logger:
    log_file = LOGS_DIR / f"pipeline_{run_id}.log"

    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.DEBUG)

    # Handler para arquivo (nível DEBUG — guarda tudo)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Handler para console (nível INFO — só o essencial)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger, log_file


# ─────────────────────────────────────────────────────────────────────────────
# UTILITÁRIOS VISUAIS
# ─────────────────────────────────────────────────────────────────────────────
SEP  = "═" * 65
SEP2 = "─" * 65

def fmt_tempo(segundos: float) -> str:
    if segundos < 60:
        return f"{segundos:.1f}s"
    m, s = divmod(int(segundos), 60)
    return f"{m}m {s:02d}s"

def barra_progresso(atual: int, total: int, largura: int = 30) -> str:
    filled = int(largura * atual / total)
    bar    = "█" * filled + "░" * (largura - filled)
    pct    = atual / total * 100
    return f"[{bar}] {pct:.0f}%"


# ─────────────────────────────────────────────────────────────────────────────
# EXECUÇÃO DE UM NOTEBOOK
# ─────────────────────────────────────────────────────────────────────────────
def executar_notebook(etapa: dict, logger: logging.Logger, timeout: int = 600) -> dict:
    """
    Executa um notebook via jupyter nbconvert e retorna um dict com resultado.

    Args:
        etapa:   Dicionário com metadados da etapa do pipeline.
        logger:  Logger configurado.
        timeout: Tempo máximo em segundos (padrão: 10 minutos).

    Returns:
        Dict com chaves: sucesso (bool), duracao (float), erro (str | None).
    """
    nb_path = NOTEBOOKS / etapa["notebook"]

    if not nb_path.exists():
        return {
            "sucesso": False,
            "duracao": 0.0,
            "erro":    f"Arquivo não encontrado: {nb_path}",
        }

    cmd = [
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to",        "notebook",
        "--execute",
        "--inplace",                        # sobrescreve o próprio notebook com outputs
        "--ExecutePreprocessor.timeout=" + str(timeout),
        "--ExecutePreprocessor.kernel_name=python3",
        str(nb_path),
    ]

    logger.debug("CMD: %s", " ".join(cmd))

    inicio = time.time()
    try:
        resultado = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 30,           # margem extra para o processo terminar
        )
        duracao = time.time() - inicio

        if resultado.returncode != 0:
            erro = resultado.stderr.strip() or resultado.stdout.strip()
            logger.debug("STDERR: %s", erro)
            return {"sucesso": False, "duracao": duracao, "erro": erro[-800:]}

        return {"sucesso": True, "duracao": duracao, "erro": None}

    except subprocess.TimeoutExpired:
        duracao = time.time() - inicio
        return {"sucesso": False, "duracao": duracao, "erro": f"Timeout após {fmt_tempo(duracao)}"}

    except Exception as exc:
        duracao = time.time() - inicio
        return {"sucesso": False, "duracao": duracao, "erro": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# RUNNER PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def rodar_pipeline(etapas: list[dict], logger: logging.Logger, log_file: Path) -> bool:
    """
    Executa a lista de etapas em sequência. Para na primeira falha obrigatória.

    Returns:
        True se todas as etapas concluíram com sucesso, False caso contrário.
    """
    total        = len(etapas)
    resultados   = []
    inicio_total = time.time()

    logger.info(SEP)
    logger.info("  PIPELINE ENGENHARIA DE DADOS — INICIANDO")
    logger.info(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  |  {total} etapa(s) agendada(s)")
    logger.info(f"  Log completo: {log_file}")
    logger.info(SEP)

    for i, etapa in enumerate(etapas, start=1):
        progresso = barra_progresso(i - 1, total)
        logger.info("")
        logger.info(f"  {progresso}  Etapa {i}/{total}")
        logger.info(f"  Notebook : {etapa['notebook']}")
        logger.info(f"  Descrição: {etapa['descricao']}")
        logger.info(SEP2)

        resultado = executar_notebook(etapa, logger)
        resultado["etapa"] = etapa
        resultados.append(resultado)

        if resultado["sucesso"]:
            logger.info(f"  ✅ CONCLUÍDO em {fmt_tempo(resultado['duracao'])}")
        else:
            logger.info(f"  ❌ FALHOU em {fmt_tempo(resultado['duracao'])}")
            logger.info(f"  Erro: {resultado['erro']}")

            if etapa["obrigatorio"]:
                logger.info("")
                logger.info("  ⛔ Etapa obrigatória falhou — pipeline interrompido.")
                logger.info("  As etapas seguintes NÃO foram executadas.")
                _imprimir_resumo(resultados, etapas, inicio_total, logger)
                return False
            else:
                logger.info("  ⚠️  Etapa opcional — continuando pipeline.")

    _imprimir_resumo(resultados, etapas, inicio_total, logger)
    return all(r["sucesso"] for r in resultados)


def _imprimir_resumo(resultados: list, etapas: list, inicio: float, logger: logging.Logger):
    duracao_total = time.time() - inicio
    executadas    = len(resultados)
    pendentes     = len(etapas) - executadas
    sucessos      = sum(1 for r in resultados if r["sucesso"])
    falhas        = executadas - sucessos

    logger.info("")
    logger.info(SEP)
    logger.info("  RESUMO DA EXECUÇÃO")
    logger.info(SEP)
    logger.info(f"  Tempo total   : {fmt_tempo(duracao_total)}")
    logger.info(f"  Executadas    : {executadas}")
    logger.info(f"  ✅ Sucesso    : {sucessos}")
    logger.info(f"  ❌ Falhas     : {falhas}")
    if pendentes:
        logger.info(f"  ⏭️  Puladas    : {pendentes}")
    logger.info(SEP2)

    for r in resultados:
        icone  = "✅" if r["sucesso"] else "❌"
        status = "OK" if r["sucesso"] else "FALHOU"
        logger.info(f"  {icone} [{status:6s}] [{fmt_tempo(r['duracao']):>7s}]  {r['etapa']['notebook']}")

    logger.info(SEP)

    if falhas == 0 and pendentes == 0:
        logger.info("  🎉 Pipeline concluído com sucesso!")
    elif falhas > 0:
        logger.info("  🔴 Pipeline encerrado com falha(s). Verifique o log para detalhes.")

    logger.info(SEP)


# ─────────────────────────────────────────────────────────────────────────────
# ARGUMENTOS DE LINHA DE COMANDO
# ─────────────────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Orquestrador do Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python run_pipeline.py                # etapas 1-7
  python run_pipeline.py --full         # etapas 1-8 (inclui Google Sheets)
  python run_pipeline.py --from 3       # começa do notebook 03
  python run_pipeline.py --only 7       # roda somente o notebook 07
  python run_pipeline.py --from 5 --full  # etapas 5-8
        """
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Inclui etapa 08 (publicação no Google Sheets). Requer credenciais."
    )
    parser.add_argument(
        "--from", dest="from_id", type=int, default=1, metavar="N",
        help="Inicia a partir da etapa N (padrão: 1)"
    )
    parser.add_argument(
        "--only", dest="only_id", type=int, default=None, metavar="N",
        help="Executa somente a etapa N"
    )
    parser.add_argument(
        "--timeout", type=int, default=600, metavar="SEGUNDOS",
        help="Timeout por notebook em segundos (padrão: 600)"
    )
    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def main():
    args    = parse_args()
    run_id  = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger, log_file = configurar_logging(run_id)

    # Filtra etapas conforme argumentos
    etapas = [e for e in PIPELINE if e["obrigatorio"] or args.full]

    if args.only_id is not None:
        etapas = [e for e in etapas if e["id"] == args.only_id]
        if not etapas:
            logger.error(f"Etapa {args.only_id} não encontrada ou não incluída.")
            sys.exit(1)
    else:
        etapas = [e for e in etapas if e["id"] >= args.from_id]

    if not etapas:
        logger.error("Nenhuma etapa selecionada. Verifique os argumentos.")
        sys.exit(1)

    sucesso = rodar_pipeline(etapas, logger, log_file)
    sys.exit(0 if sucesso else 1)


if __name__ == "__main__":
    main()
