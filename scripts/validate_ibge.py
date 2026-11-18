"""Validação opt-in somente de leitura: python -m scripts.validate_ibge."""

from src.pipeline import extract_project
from src.transform import Transform


def main():
    documents = extract_project("public-validation")
    frame = Transform().transform(documents)
    print(frame.groupby("tabela").size().to_string())
    print(f"Total: {len(frame)} observações; nenhum banco foi acessado.")


if __name__ == "__main__":
    main()
