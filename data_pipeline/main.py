from core.processor import DataProcessor

dp = DataProcessor()
#data = dp.read_file('data_pipeline/test_data/test_data.xlsx', sheet_name=None)
data = dp.read_file('data_pipeline/test_data/csvs/test_simple.csv')
data = dp.normalize_columns(data.dataframe)
print(data)