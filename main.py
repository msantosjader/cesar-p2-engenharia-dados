from src.extract import Extract
from src.load import Load


extractor = Extract()
data = extractor.get_pnadc()

load = Load()
load.load_json("pnad", data)