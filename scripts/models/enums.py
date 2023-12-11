from enum import Enum


class CsvTypes(str, Enum):
    input_data = 'input_data'
    proceed_data_Ky = 'proceed_data_Ky'
    proceed_data_Em = 'proceed_data_Em'
    proceed_data_Ed = 'proceed_data_Ed'
    proceed_data_GTK = 'proceed_data_GTK'
    proceed_data_decades_grouped = 'proceed_data_decades_grouped'
    proceed_data_mean_t_months = 'proceed_data_mean_t_months'
    proceed_data_active_months = 'proceed_data_active_months'
    proceed_em_active_months = 'proceed_em_active_months'
    groups_year = 'groups_year'
