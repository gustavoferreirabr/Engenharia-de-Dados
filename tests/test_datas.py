import pandas as pd
from src.datas import converter_data, conferir_data


def test_iso_nao_troca_dia_e_mes():
    resultado = converter_data(pd.Series(["2024-07-08"])).iloc[0]
    assert resultado == pd.Timestamp(2024, 7, 8)


def test_formato_brasileiro():
    resultado = converter_data(pd.Series(["24/05/2024"])).iloc[0]
    assert resultado == pd.Timestamp(2024, 5, 24)


def test_texto_invalido_vira_vazio():
    resultado = converter_data(pd.Series(["abc"]))
    assert resultado.isna().all()


def test_conferir_data_aprova_conversao_certa():
    original = pd.Series(["2024-07-08", "24/05/2024"])
    assert conferir_data(converter_data(original), original) is True


def test_conferir_data_reprova_o_bug_antigo():
    original = pd.Series(["2024-07-08"])
    com_bug = pd.to_datetime(original, format="mixed", dayfirst=True)
    assert conferir_data(com_bug, original) is False