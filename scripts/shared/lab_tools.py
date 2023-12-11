import os
import re
import time
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from inspect import signature
from pathlib import Path
from typing import Any, Callable, List, Union, Optional

import pandas as pd
from requests import request
from tabulate import tabulate


def separated_print(*args: Any) -> None:
    print(*args, end='\n\n')


def ds_view(_ds: pd.DataFrame, _viewer: Callable = separated_print) -> None:
    _viewer(tabulate(_ds, headers='keys'))


def fix_kwargs(obj: object, kwargs: dict):
    return {k: v for k, v in kwargs.items() if k in signature(obj).parameters}


class AttemptException(Exception):
    def __str__(self):
        return 'Количество попыток достигло нуля'


def polling_decorator(func: Callable):
    @wraps(func)
    def _wrapper(*args, __st=0, __at=100, __log=False, **kwargs, ):
        if not __at:
            raise AttemptException()
        try:
            return func(*args, **fix_kwargs(func, kwargs))
        except Exception as e:
            if __log:
                print(e, __st)
            time.sleep(__st)
            return _wrapper(*args, __at=__at - 1, __st=__st + 1, **kwargs)

    return _wrapper


def google_link(_id: str) -> str:
    return f'https://drive.google.com/uc?export=download&confirm=yes&id={_id}'


def groupy_date(
        df: pd.DataFrame,
        date_cols: List[str],
        st: int, end: int,
        filter_attr: str = 'month',
        gr_attr: str = 'year',
        **aggr_funcs,
) -> pd.DataFrame:
    return filter_by_date(df, date_cols, st, end, filter_attr).groupby(
        getattr(df[date_cols].dt, gr_attr),
    ).aggregate(aggr_funcs).rename(
        columns={k: f'{k}_between_{st}_{end}_{filter_attr}s' for k in aggr_funcs.keys()},
    )


def filter_by_date(
        df: pd.DataFrame,
        date_cols: List[str],
        st: int,
        end: int,
        filter_attr: str,
) -> pd.DataFrame:
    return df.loc[
        (getattr(df[date_cols].dt, filter_attr) >= st) & (getattr(df[date_cols].dt, filter_attr) <= end)
        ]


@dataclass
class PandasTable:
    id: str = None
    path_io: Union[str, Path, os.PathLike] = None
    index_cols: List[str] = None
    date_cols: List[str] = None
    data: Optional[pd.DataFrame] = None

    def load(self):
        if self.path_io is not None:
            self.data = pd.read_csv(self.path_io)
            with suppress(Exception):
                self.data = self.data.drop(['Unnamed: 0'], axis=1)
            if self.date_cols is not None:
                for col in self.date_cols:
                    self.data[col] = pd.to_datetime(self.data[col])
            if self.index_cols is not None:
                self.data = self.data.set_index(self.index_cols)
        else:
            self.data = pd.read_csv(self.google_link)
            self.save()

    def drop_cols(self, *cols: str):
        self.data = self.data.drop(list(cols), index=1)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, item):
        return self.data[item]

    def save(self, *args, **kwargs):
        self.data.to_csv(self.path_io)

    @property
    def google_link(self):
        return google_link(self.id)

    def view(self, n=5):
        ds_view(self.data.sample(n))


@dataclass
class DateRepr:
    part: str = 0
    month: int = 0
    year: int = 0

    def __repr__(self):
        return f'{self.part}/{self.month}/{self.year}'

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return hash(self.__repr__())


def get_decade_of_month(date: datetime) -> int:
    day = date.day
    if day <= 10:
        return 1
    elif 11 <= day <= 20:
        return 2
    else:
        return 3


def create_decade(date) -> int:
    return DateRepr(get_decade_of_month(date), date.month, date.year)


class Dictable:
    _resource: str = ''
    _base_url: str = ''

    @property
    def headers(self):
        return {}

    @property
    def dict(self):
        return {k: v for k, v in self.__dict__.items() if not (k.startswith('_') or callable(v))}

    def send(self, method: str = 'post', tpe: str = 'data'):
        return request(method, f"{self._base_url}{self._resource}", **{tpe: self.dict}, headers=self.headers)


def remove_single_letter_word(_s: str) -> str:
    return re.sub(r'\b\w\b', '', _s)


def replace_not_russian(_s: str) -> str:
    return re.sub('[^а-яА-Я ]', '', _s)


def replace_double_space(_s: str) -> str:
    return re.sub(r'\s+', ' ', _s)


def split_into_parts(sentence: str, words_per_part: int = 4) -> List[str]:
    words = sentence.split()
    parts = [words[i:i + words_per_part] for i in range(0, len(words), words_per_part)]
    return [' '.join(part) for part in parts]
