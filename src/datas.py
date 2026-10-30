"""Funções para trabalhar com datas do projeto."""
import pandas as pd


def converter_data(col: pd.Series) -> pd.Series:
    """Converte texto em data. Aceita 'aaaa-mm-dd' e 'dd/mm/aaaa'."""
    iso = pd.to_datetime(col, format="%Y-%m-%d", errors="coerce")
    br = pd.to_datetime(col, format="%d/%m/%Y", errors="coerce")
    return iso.fillna(br)


def conferir_data(convertida: pd.Series, original: pd.Series) -> bool:
    """Confere se a conversão ficou certa (True) ou não (False)."""
    vazias_novas = (convertida.isna() & original.notna()).sum()
    e_iso = original.str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)
    e_br = original.str.match(r"^\d{2}/\d{2}/\d{4}$", na=False)
    iso_ok = (convertida[e_iso].dt.strftime("%Y-%m-%d") == original[e_iso]).all()
    br_ok = (convertida[e_br].dt.strftime("%d/%m/%Y") == original[e_br]).all()
    return bool(vazias_novas == 0 and iso_ok and br_ok)