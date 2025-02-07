import os

import pytest
import xarray

from intake_esm.source import _get_xarray_open_kwargs, _open_dataset, _update_attrs

here = os.path.abspath(os.path.dirname(__file__))


f1 = os.path.join(
    here,
    'sample_data/cmip/cmip5/output1/NIMR-KMA/HadGEM2-AO/rcp85/mon/atmos/Amon/r1i1p1/v20130815/tasmax/tasmax_Amon_HadGEM2-AO_rcp85_r1i1p1_200511-200512.nc',
)
f2 = os.path.join(
    here,
    'sample_data/cmip/cmip5/output1/NIMR-KMA/HadGEM2-AO/rcp85/mon/atmos/Amon/r1i1p1/v20130815/tasmax/tasmax_Amon_HadGEM2-AO_rcp85_r1i1p1_200601-210012.nc',
)

kerchunk_file = os.path.join(
    here,
    'sample_data/kerchunk-files/noaa-nwm-test-reference.json',
)

multi_path = f'{os.path.dirname(f1)}/*.nc'


def _common_open(fpath, varname='tasmax'):
    _xarray_open_kwargs = _get_xarray_open_kwargs('netcdf')
    return _open_dataset(fpath, varname, xarray_open_kwargs=_xarray_open_kwargs).compute()


@pytest.mark.parametrize('fpath,expected_time_size', [(f1, 2), (f2, 2), (multi_path, 4)])
def test_open_dataset(fpath, expected_time_size):
    ds = _common_open(fpath)
    assert isinstance(ds, xarray.Dataset)
    assert len(ds.time) == expected_time_size


@pytest.mark.parametrize('storage_options', [{'anon': True}, {}])
def test_get_xarray_open_kwargs(storage_options):
    xarray_open_kwargs = _get_xarray_open_kwargs('zarr', storage_options=storage_options)
    assert xarray_open_kwargs['backend_kwargs']['storage_options'] == storage_options


def test_open_dataset_kerchunk(kerchunk_file=kerchunk_file):
    xarray_open_kwargs = _get_xarray_open_kwargs(
        'reference',
        dict(engine='zarr', consolidated=False),
        storage_options={'remote_protocol': 's3', 'remote_options': {'anon': True}},
    )
    ds = _open_dataset(
        data_format='reference',
        urlpath=kerchunk_file,
        varname=None,
        xarray_open_kwargs=xarray_open_kwargs,
    ).compute()
    assert isinstance(ds, xarray.Dataset)


@pytest.mark.parametrize('data_format', ['zarr', 'netcdf'])
@pytest.mark.parametrize('attrs', [{}, {'units': 'K'}, {'variables': ['foo', 'bar']}])
def test_update_attrs(tmp_path, data_format, attrs):
    fpath = tmp_path / 'test.nc' if data_format == 'netcdf' else tmp_path / 'test.zarr'
    fpath = str(fpath)
    ds = _common_open(f1)
    ds = _update_attrs(ds=ds, additional_attrs=attrs)
    if data_format == 'netcdf':
        ds.to_netcdf(fpath)
    else:
        ds.to_zarr(fpath)

    _xarray_open_kwargs = _get_xarray_open_kwargs(data_format=data_format)
    ds_new = _open_dataset(fpath, 'tasmax', xarray_open_kwargs=_xarray_open_kwargs).compute()
    assert ds_new.attrs == ds.attrs
