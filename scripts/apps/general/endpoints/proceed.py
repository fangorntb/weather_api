import dataclasses
from contextlib import suppress
from datetime import datetime
from functools import cached_property

import pandas as pd
from fastapi import HTTPException

from scripts.shared import lab_tools
from scripts.shared.lab_tools import PandasTable, groupy_date


class WeatherTable(PandasTable):

    @cached_property
    def need_cols(self):
        return 'YEAR,MO,DY,T2M,PRECTOTCORR,RH2M'.split(',')

    @cached_property
    def need_cols_len(self):
        return len(self.need_cols)

    @cached_property
    def ord_normal(self):
        ord_df = lab_tools.PandasTable(
            data=self.data.copy()
        )
        ord_df.data['DATE'] = ord_df.data['YEAR,MO,DY'.split(',')].apply(
            lambda x: pd.to_datetime(f"{x['YEAR']}/{x['MO']}/{x['DY']}", yearfirst=True, ), axis=1)
        ord_df.data = ord_df.data.drop('YEAR,MO,DY'.split(','), axis=1)
        return ord_df.data

    @cached_property
    def decades(self):
        ord_df = lab_tools.PandasTable(
            data=self.ord_normal.copy(),
        )
        ord_df.data['DECADE'] = ord_df['DATE'].apply(lambda x: lab_tools.create_decade(x), )
        return ord_df.data

    @cached_property
    def decades_grouped(self):
        ord_df = lab_tools.PandasTable(
            data=self.decades.copy()
        )
        return ord_df.data.groupby(['DECADE']).aggregate({'T2M': 'mean', 'PRECTOTCORR': 'mean', 'RH2M': 'mean'})

    def validate(self):
        passed = self.data.columns
        if len(frozenset(passed) & frozenset(self.need_cols)) < self.need_cols_len:
            raise HTTPException(406, f'incorect columns, passed: {passed}, need: {self.need_cols}')

    @cached_property
    def mean_t_months(self):
        ord_df = lab_tools.PandasTable(
            data=self.ord_normal.copy(),
        )
        with suppress(Exception):
            ord_df.data['DATE'] = ord_df.data['DATE'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'), )
        ord_df['DATE'] = ord_df.data['DATE'].apply(
            lambda x: f'{x.year}/{x.month if x.month > 9 else "0" + str(x.month)}/01'
        )
        ord_df.data = ord_df.data.groupby(['DATE']).aggregate(
            {'T2M': 'mean', 'PRECTOTCORR': 'sum', 'RH2M': 'sum'})
        return ord_df.data

    @cached_property
    def active_months(self):
        ord_df = PandasTable(
            data=self.ord_normal.copy(),
        )

        groups = PandasTable(data=pd.DataFrame(), )

        for _st, _end in (
                (5, 6),
                (5, 7),
                (5, 8),
                (1, 12),
        ):
            gr = groupy_date(
                ord_df.data,
                date_cols='DATE',
                st=_st,
                end=_end,
                T2M='sum',
                PRECTOTCORR='sum',
                RH2M='mean',
            )
            groups.data[gr.columns] = gr
        return groups.data

    @cached_property
    def gtk(self):
        df = self.active_months.copy()
        df['GTK_5_6'] = df['PRECTOTCORR_between_5_6_months'] / (0.1 * df['T2M_between_5_6_months'])
        df['GTK_5_7'] = df['PRECTOTCORR_between_5_7_months'] / (0.1 * df['T2M_between_5_7_months'])
        df['GTK_5_8'] = df['PRECTOTCORR_between_5_8_months'] / (0.1 * df['T2M_between_5_8_months'])
        df['GTK_1_12'] = df['PRECTOTCORR_between_1_12_months'] / (0.1 * df['T2M_between_1_12_months'])
        return df

    @cached_property
    def ed(self):
        df = self.decades_grouped.copy()
        df = df[['T2M', 'PRECTOTCORR', 'RH2M']]
        df['Ед'] = 0.061 * (25 + df.T2M) / (1 - 0.01 * df.RH2M)
        return df

    @cached_property
    def em(self):
        df = self.mean_t_months.copy()
        df = df[['T2M', 'PRECTOTCORR', 'RH2M']]
        df['Em'] = 0.018 * (25 + df.T2M) ** 2 / (100 - df.RH2M)
        return df

    @cached_property
    def em_active_months(self):
        em_df = PandasTable(
            data=self.em.reset_index(),
        )
        em_df.data['DATE'] = em_df.data['DATE'].apply(lambda x: datetime.strptime(x, '%Y/%m/%d'), )
        groups = PandasTable(data=pd.DataFrame(), )
        lab_tools.ds_view(em_df.data.head(1000))

        for _st, _end in (
                (5, 6),
                (5, 7),
                (5, 8),
                (1, 12),
        ):
            gr = groupy_date(
                em_df.data.loc[em_df['T2M'] > 10],
                date_cols='DATE',
                st=_st,
                end=_end,
                # T2M='sum',
                # RH2M='mean',
                Em='mean',
                PRECTOTCORR='sum',
            )
            groups.data[gr.columns] = gr
        return groups.data

    @cached_property
    def ky(self):
        df = self.em_active_months.copy()
        df_pr = self.active_months
        df['Ky_5_6'] = df_pr['PRECTOTCORR_between_5_6_months'] / df['Em_between_5_6_months']
        df['Ky_5_7'] = df_pr['PRECTOTCORR_between_5_7_months'] / df['Em_between_5_7_months']
        df['Ky_5_8'] = df_pr['PRECTOTCORR_between_5_8_months'] / df['Em_between_5_8_months']
        df['Ky_1_12'] = df_pr['PRECTOTCORR_between_1_12_months'] / df['Em_between_1_12_months']
        return df


if __name__ == '__main__':
    weather = WeatherTable(path_io='/home/urumchi/py/analytics/ORD.csv')
    weather.load()
    print(weather.ky)
