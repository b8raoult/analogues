
import os

DATASETS = {}


class Dataset:

    def __init__(self, name):
        self.name = name

    @classmethod
    def lookup(cls, name):
        return DATASETS[name]


class ERA5Dataset(Dataset):

    def to_mars(self, request):
        request['class'] = 'ea'
        request['dataset'] = 'reanalysis'
        request['expect'] = 'any'


for n in ('era5', 'ea'):
    DATASETS[n] = ERA5Dataset('era5')


class ERAInterimDataset(Dataset):
    pass


for n in ('interim', 'ei'):
    DATASETS[n] = ERAInterimDataset('interim')

DEFAULT_DATASET = os.environ.get('DATASET', 'era5')
