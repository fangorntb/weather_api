import io
from functools import cached_property

import requests

BASE_URL = 'http://89.104.68.100:8090'


class Api:

    def __init__(self, username: str, password: str, access_token: str = None):
        self.username = username
        self.password = password
        self._access_token = access_token

    def register(self):
        return requests.post(
            f'{BASE_URL}/api/register',
            data=dict(username=self.username, password=self.password, scopes=['user'])
        )

    def login(self):
        return requests.post(f'{BASE_URL}/api/token', data=dict(username=self.username, password=self.password, ))

    @cached_property
    def access_token(self):
        login = self.login()
        if login.status_code != 200:
            token_resp = self.register()
        else:
            token_resp = login
        return token_resp.json()['access_token']

    def upload_csv(
            self,
            file: io.FileIO,
            name: str = 'test',
            latitude: float = 0,
            longitude: float = 0,
            _type: str = 'input_data',
            description='',
    ):
        return requests.post(
            f'{BASE_URL}/api/csv',
            params=dict(
                name=name,
                latitude=latitude,
                longitude=longitude,
                type=_type,
                description=description,
            ),
            files={'data': file},
            headers={'Authorization': f'Bearer {self.access_token}'}
        ).json()['id']

    def get_csvs(
            self,
    ):
        return requests.get(
            f'{BASE_URL}/api/csvs',
            headers={'Authorization': f'Bearer {self.access_token}'}
        ).json()

    def get_csv_json(
            self,
            _id: str,
    ):
        return requests.get(
            f'{BASE_URL}/api/csv/json',
            params={'id': _id},
            headers={'Authorization': f'Bearer {self.access_token}'},
        ).json()

    def proceed_csv(
            self,
            _id: str
    ):
        return requests.post(
            f'{BASE_URL}/api/csv/proceed',
            params={'id': _id},
            headers={'Authorization': f'Bearer {self.access_token}'},
        ).json()

    def csv_get_zip(
            self,
            _id: str,
            outfile: str = None,
    ):
        if outfile is None:
            outfile = f'csvs_{_id}.zip'
        data = requests.get(
            f'{BASE_URL}/api/csv/proceed-zip',
            params={'id': _id},
            headers={'Authorization': f'Bearer {self.access_token}'},
            stream=True,
        )
        with open(outfile, 'wb') as f:
            for chunk in data:
                f.write(chunk)
        return outfile

    def create_map(self, name: str = '', description: str = ''):
        return requests.post(
            f'{BASE_URL}/api/map',
            json=dict(name=name, description=description),
            headers={'Authorization': f'Bearer {self.access_token}'},
        ).json()['id']

    def get_maps_meta(self, ):
        return [
            i.get('id') for i in requests.get(
                f'{BASE_URL}/api/maps',
                headers={'Authorization': f'Bearer {self.access_token}'},
            ).json()
        ]

    def assign_map(self, map_id, *csvs):
        return requests.post(
            f'{BASE_URL}/api/map/assign',
            params={'map_id': map_id, },
            json=list(csvs),
            headers={'Authorization': f'Bearer {self.access_token}'},
        )

    def maps_get_zip(
            self,
            map_id: str,
            *dfs: str,
            outfile: str = None,
    ):
        if outfile is None:
            outfile = f'maps_{map_id}.zip'
        data = requests.post(
            f'{BASE_URL}/api/map/assign/get',
            params={'map_id': map_id, },
            json=list(dfs),
            headers={'Authorization': f'Bearer {self.access_token}'},
            stream=True,
        )
        with open(outfile, 'wb') as f:
            for chunk in data:
                f.write(chunk)
        return outfile


if __name__ == '__main__':
    API = Api('xxx', 'xxx')
    CSV_ID = API.upload_csv(open('/home/urumchi/Desktop/ord.csv', 'rb'))
    print(CSV_ID)
    print(API.get_csvs())
    print(API.get_csv_json(_id=CSV_ID))
    print(API.proceed_csv(_id=CSV_ID))
    print(API.csv_get_zip(CSV_ID))
    MAP_ID = API.create_map()
    print(MAP_ID)
    print(API.assign_map(MAP_ID, CSV_ID))
    print(API.maps_get_zip(MAP_ID))
