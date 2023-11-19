from enum import Enum


class CsvTypes(str, Enum):
    input_data = 'input_data'
    proceed_data_Ky = 'proceed_data_Ky'
    proceed_data_Em = 'proceed_data_Em'
