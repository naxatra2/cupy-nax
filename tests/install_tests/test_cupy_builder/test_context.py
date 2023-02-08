import os

from cupy_builder._context import (
    _get_env_bool, _get_env_path, Context, parse_args)


class TestGetEnvBool:
    def test_true(self):
        assert _get_env_bool('V', True, {})
        assert _get_env_bool('V', True, {'V': '1'})
        assert _get_env_bool('V', False, {'V': '1'})

    def test_false(self):
        assert not _get_env_bool('V', False, {})
        assert not _get_env_bool('V', False, {'V': '0'})
        assert not _get_env_bool('V', True, {'V': '0'})


class TestGetEnvPath:
    def test(self):
        assert _get_env_path('P', {}) == []
        assert _get_env_path('P', {'P': f'1{os.pathsep}'}) == ['1']
        assert _get_env_path('P', {'P': f'1{os.pathsep}2'}) == ['1', '2']


class TestContext:
    def test_default(self):
        ctx = Context('.', _env={}, _argv=[])

        assert ctx.source_root == '.'

        assert not ctx.use_cuda_python
        assert not ctx.use_hip
        assert ctx.include_dirs == []
        assert ctx.library_dirs == []

        assert ctx.package_name == 'cupy'
        assert ctx.long_description_path is None
        assert ctx.wheel_libs == []
        assert ctx.wheel_includes == []
        assert ctx.wheel_metadata_path is None
        assert not ctx.no_rpath
        assert not ctx.profile
        assert not ctx.linetrace
        assert not ctx.annotate
        assert not ctx.use_stub

    def test_env(self):
        ctx = Context('.', _env={
            'CUPY_USE_CUDA_PYTHON': '1',
            'CUPY_INSTALL_USE_HIP': '1',
            'CUPY_INCLUDE_PATH': f'/tmp/include{os.pathsep}/tmp2/include',
            'CUPY_LIBRARY_PATH': f'/tmp/lib{os.pathsep}/tmp2/lib',
        }, _argv=[])

        assert ctx.use_cuda_python
        assert ctx.use_hip
        assert ctx.include_dirs == ['/tmp/include', '/tmp2/include']
        assert ctx.library_dirs == ['/tmp/lib', '/tmp2/lib']


class TestParseArgs:
    def test_args(self):
        args = [
            'python', 'setup.py', 'develop',
            '--cupy-package-name', 'cupy-cudaXXX',
            '--cupy-long-description', 'foo.rst',
            '--cupy-wheel-lib', 'lib1',
            '--cupy-wheel-lib', 'lib2',
            '--cupy-wheel-metadata', '_wheel.json',
            '--cupy-no-rpath',
            '--cupy-profile',
            '--cupy-coverage',
            '--cupy-no-cuda',
            '--extra-option',
        ]
        options, remaining = parse_args(args)
        assert options.cupy_package_name == 'cupy-cudaXXX'
        assert options.cupy_long_description == 'foo.rst'
        assert options.cupy_wheel_lib == ['lib1', 'lib2']
        assert options.cupy_wheel_metadata == '_wheel.json'
        assert options.cupy_no_rpath
        assert options.cupy_profile
        assert options.cupy_coverage
        assert options.cupy_no_cuda
        assert remaining == ['python', 'setup.py', 'develop', '--extra-option']
