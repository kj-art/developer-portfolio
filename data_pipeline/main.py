from core.processor import DataProcessor

dp = DataProcessor()
data = dp.read_file('data_pipeline/test_data/test_data.xlsx', sheet_name=None)
print(data)
print(data.dataframe)