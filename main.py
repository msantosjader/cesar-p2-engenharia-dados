from src.extract import Extract
from src.load import Load


extractor = Extract()
data = extractor.get_pnad()

load = Load()
load.load_json("pnad", data)