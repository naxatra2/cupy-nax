import unittest
import functools

import numpy

import cupy
from cupy import testing
from cupyx import fallback_mode
from cupyx.fallback_mode import ndarray


def numpy_fallback_equal(name='xp'):
    """
    Decorator that checks fallback_mode results are equal to NumPy ones.
    Checks results that are non-ndarray.

    Args:
        name(str): Argument name whose value is either
        ``numpy`` or ``cupy`` module.
    """
    def decorator(impl):
        @functools.wraps(impl)
        def test_func(self, *args, **kwargs):

            kwargs[name] = fallback_mode.numpy
            fallback_result = impl(self, *args, **kwargs)

            kwargs[name] = numpy
            numpy_result = impl(self, *args, **kwargs)

            assert numpy_result == fallback_result

        return test_func
    return decorator


def numpy_fallback_array_equal(name='xp'):
    """
    Decorator that checks fallback_mode results are equal to NumPy ones.
    Checks ndarrays.

    Args:
        name(str): Argument name whose value is either
        ``numpy`` or ``cupy`` module.
    """
    def decorator(impl):
        @functools.wraps(impl)
        def test_func(self, *args, **kwargs):

            kwargs[name] = fallback_mode.numpy
            fallback_result = impl(self, *args, **kwargs)

            kwargs[name] = numpy
            numpy_result = impl(self, *args, **kwargs)

            if isinstance(numpy_result, numpy.ndarray):
                # if numpy returns ndarray, cupy must return ndarray
                assert isinstance(fallback_result, ndarray.ndarray)
                assert fallback_result.dtype is numpy_result.dtype
                testing.assert_array_equal(
                    numpy_result, fallback_result._array)

            elif isinstance(numpy_result, numpy.ScalarType):
                # if numpy returns scalar
                # cupy may return 0-dim array
                assert numpy_result == fallback_result._array.item()

        return test_func
    return decorator


@testing.gpu
class TestFallbackMode(unittest.TestCase):

    @numpy_fallback_array_equal()
    def test_argmin(self, xp):

        a = xp.array([
            [13, 5, 45, 23, 9],
            [-5, 41, 0, 22, 4],
            [2, 6, 43, 11, -1]
        ])

        return xp.argmin(a, axis=1)

    @numpy_fallback_array_equal()
    def test_argmin_zero_dim_array_vs_scalar(self, xp):

        a = xp.array([
            [13, 5, 45, 23, 9],
            [-5, 41, 0, 22, 4],
            [2, 6, 43, 11, -1]
        ])

        return xp.argmin(a)

    # cupy.argmin raises error if list passed, numpy does not
    def test_argmin_list(self):

        a = [
            [13, 5, 45, 23, 9],
            [-5, 41, 0, 22, 4],
            [2, 6, 43, 11, -1]
        ]

        with self.assertRaises(AttributeError):
            fallback_mode.numpy.argmin(a)

        assert numpy.argmin([1, 0, 3]) == 1

    # Non-existing function
    @numpy_fallback_equal()
    def test_array_equal(self, xp):

        a = xp.array([1, 2])
        b = xp.array([1, 2])

        return xp.array_equal(a, b)

    # Both cupy and numpy return 0-d array
    @numpy_fallback_array_equal()
    def test_convolve_zero_dim_array(self, xp):

        a = xp.array([1, 2, 3])
        b = xp.array([0, 1, 0.5])

        return xp.convolve(a, b, 'valid')

    def test_vectorize(self):

        def function(a, b):
            if a > b:
                return a - b
            return a + b

        actual = numpy.vectorize(function)([1, 2, 3, 4], 2)
        expected = fallback_mode.numpy.vectorize(function)([1, 2, 3, 4], 2)

        assert isinstance(actual, numpy.ndarray)

        # ([1,2,3,4], 2) are arguments to
        # numpy.vectorize(function), not numpy.vectorize
        # So, it returns numpy.ndarray
        assert isinstance(expected, numpy.ndarray)

        testing.assert_array_equal(expected, actual)

    def test_module_not_callable(self):

        self.assertRaises(TypeError, fallback_mode.numpy)

        self.assertRaises(TypeError, fallback_mode.numpy.linalg)

    def test_numpy_scalars(self):

        assert fallback_mode.numpy.inf is numpy.inf

        assert fallback_mode.numpy.pi is numpy.pi

        # True, because 'is' checks for reference
        # fallback_mode.numpy.nan and numpy.nan both have same reference
        assert fallback_mode.numpy.nan is numpy.nan

    def test_cupy_specific_func(self):

        with self.assertRaises(AttributeError):
            func = fallback_mode.numpy.ElementwiseKernel  # NOQA

    def test_func_not_in_numpy(self):

        with self.assertRaises(AttributeError):
            func = fallback_mode.numpy.dummy  # NOQA

    def test_same_reference(self):

        assert fallback_mode.numpy.int64 is numpy.int64

        assert fallback_mode.numpy.float32 is numpy.float32


@testing.parameterize(
    {'object': fallback_mode.numpy.ndarray},
    {'object': fallback_mode.numpy.ndarray.__add__},
    {'object': fallback_mode.numpy.vectorize},
    {'object': fallback_mode.numpy.linalg.eig},
)
@testing.gpu
class TestDocs(unittest.TestCase):

    @numpy_fallback_equal()
    def test_docs(self, xp):
        return getattr(self.object, '__doc__')


@testing.gpu
class FallbackArray(unittest.TestCase):

    def test_ndarray_creation(self):

        a = fallback_mode.numpy.array([[1, 2], [3, 4]])
        assert isinstance(a, ndarray.ndarray)

        b = fallback_mode.numpy.arange(9)
        assert isinstance(b, ndarray.ndarray)
        assert isinstance(b._array, cupy.ndarray)

    # ndarray fallback method
    @numpy_fallback_equal()
    def test_ndarray_tobytes(self, xp):

        a = xp.array([1, 2, 3])

        return a.tobytes()

    @numpy_fallback_array_equal()
    def test_ndarray_min(self, xp):

        a = xp.array([1, 2, 0, 4])

        return a.min()

    @numpy_fallback_array_equal()
    def test_ndarray_argmin(self, xp):

        a = xp.array([[1, 2, 3], [7, 8, 9]])

        return a.argmin()

    @numpy_fallback_array_equal()
    def test_ndarray_argmin_kwargs(self, xp):

        a = xp.array([[1, 2, 3], [7, 8, 9]])

        return a.argmin(axis=0)

    def test_getitem(self):

        x = fallback_mode.numpy.array([1, 2, 3])

        # single element
        assert int(x[2]) == 3

        # slicing
        res = cupy.array([1, 2, 3])
        testing.assert_array_equal(x[:2]._array, res[:2])

    def test_setitem(self):

        x = fallback_mode.numpy.array([1, 2, 3])

        # single element
        x[2] = 99
        res = cupy.array([1, 2, 99])
        testing.assert_array_equal(x._array, res)

        # slicing
        y = fallback_mode.numpy.array([11, 22])
        x[:2] = y
        res = cupy.array([11, 22, 99])
        testing.assert_array_equal(x._array, res)

    @numpy_fallback_equal()
    def test_ndarray_shape(self, xp):

        x = xp.arange(20)
        x = x.reshape(4, 5)

        return x.shape

    def test_ndarray_shape_creation(self):

        a = fallback_mode.numpy.ndarray((4, 5))

        assert a.shape == (4, 5)

    def test_instancecheck_ndarray(self):

        a = fallback_mode.numpy.array([1, 2, 3])
        assert isinstance(a, fallback_mode.numpy.ndarray)

        b = fallback_mode.numpy.ndarray((2, 3))
        assert isinstance(b, fallback_mode.numpy.ndarray)

    def test_instancecheck_type(self):

        a = fallback_mode.numpy.arange(3)
        assert isinstance(a, type(a))


@testing.parameterize(
    {'func': '__eq__', 'shape': (3, 4)},
    {'func': '__ne__', 'shape': (3, 1)},
    {'func': '__gt__', 'shape': (4,)},
    {'func': '__lt__', 'shape': (1, 1)},
    {'func': '__ge__', 'shape': (1, 2)},
    {'func': '__le__', 'shape': (1,)}
)
@testing.gpu
class TestArrayComparison(unittest.TestCase):

    @numpy_fallback_array_equal()
    def test_ndarray_comparison(self, xp):

        a = testing.shaped_random(self.shape, xp=xp)
        b = testing.shaped_random(self.shape, xp=xp, seed=3)

        return getattr(a, self.func)(b)


@testing.parameterize(
    {'func': '__abs__', 'shape': (3, 4)},
    {'func': '__neg__', 'shape': (2, 2)},
    {'func': '__str__', 'shape': (5, 6)},
    {'func': '__repr__', 'shape': (3, 4)},
    {'func': '__int__', 'shape': (1,)},
    {'func': '__float__', 'shape': (1, 1)},
    {'func': '__len__', 'shape': (3, 3)},
    {'func': '__invert__', 'shape': (4, 5)},
    {'func': '__copy__', 'shape': (4, 4)}
)
@testing.gpu
class TestArrayUnaryMethods(unittest.TestCase):

    @numpy_fallback_array_equal()
    def test_unary_methods(self, xp):

        a = testing.shaped_random(self.shape, xp=xp)

        return getattr(a, self.func)


@testing.parameterize(
    {'func': '__add__', 'shape': (3, 4), 'dtype': numpy.float32},
    {'func': '__sub__', 'shape': (2, 2), 'dtype': numpy.float32},
    {'func': '__mul__', 'shape': (5, 6), 'dtype': numpy.float32},
    {'func': '__mod__', 'shape': (3, 4), 'dtype': numpy.float32},
    {'func': '__iadd__', 'shape': (1,), 'dtype': numpy.float32},
    {'func': '__imul__', 'shape': (1, 1), 'dtype': numpy.float32},
    {'func': '__and__', 'shape': (3, 3), 'dtype': numpy.int32},
    {'func': '__ipow__', 'shape': (4, 5), 'dtype': numpy.int32},
    {'func': '__xor__', 'shape': (4, 4), 'dtype': numpy.int32},
    {'func': '__lshift__', 'shape': (2,), 'dtype': numpy.int32},
    {'func': '__irshift__', 'shape': (3, 2), 'dtype': numpy.int32},
)
@testing.gpu
class TestArrayArithmeticMethods(unittest.TestCase):

    @numpy_fallback_array_equal()
    def test_arithmetic_methods(self, xp):

        a = testing.shaped_random(self.shape, xp=xp, dtype=self.dtype)
        b = testing.shaped_random(self.shape, xp=xp, dtype=self.dtype, seed=5)

        return getattr(a, self.func)(b)
