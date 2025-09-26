from core.processor import DataProcessor

dp = DataProcessor()
data = dp.process_folder('data_pipeline/test_data', True, ['csv', 'json'], sheet_name=None)
dp.write_file(data, 'C:\\Users\\krjar\\Downloads\\asdf.xlsx')
#data = dp.read_file('data_pipeline/test_data/test_data.xlsx', sheet_name=None)
#data = dp.read_file('data_pipeline/test_data/csvs/test_simple.csv')
#data = dp.normalize_columns(data.dataframe)
#data = dp.read_file('data_pipeline/test_data/test_data.json')
#print(data)