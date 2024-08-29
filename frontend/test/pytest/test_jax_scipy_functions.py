# Copyright 2023 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Integration tests to check JAX SciPy functionality with qjit
"""
from jax import numpy as jnp
from jax import scipy as jsp
import numpy as np
import pytest

from catalyst import qjit, jacobian

matrix_inputs = [
    jnp.array([[0.1, 0.2], [5.3, 1.2]]),
    jnp.array([[1, 2], [3, 4]]),
    jnp.array([[1.0, -1.0j], [1.0j, -1.0]]),
]


class TestIntegrate:
    """Tests for the jax.scipy.integrate module"""

    @pytest.mark.parametrize(
        "y,x",
        [
            (jnp.array([1, 2, 3, 2, 3, 2, 1]), jnp.array([0, 2, 5, 7, 10, 15, 20])),
            (jnp.sin(jnp.linspace(0, 2 * jnp.pi, 1000)) ** 2, jnp.linspace(0, 2 * jnp.pi, 1000)),
        ],
    )
    def test_trapezoid(self, y, x):
        """Test trapezoidal integration"""

        def f(y, x):
            return jsp.integrate.trapezoid(y, x)

        observed = qjit(f)(y, x)
        expected = f(y, x)
        assert np.allclose(observed, expected)

    @pytest.mark.parametrize(
        "y,dx",
        [
            (jnp.array([1, 2, 3, 2, 3, 2, 1]), 1.0),
            (jnp.sin(jnp.linspace(0, 2 * jnp.pi, 1000)) ** 2, 2 * jnp.pi / 1000),
        ],
    )
    def test_trapezoid_regular_grid(self, y, dx):
        """Test trapezoidal integration"""

        def f(y, dx):
            return jsp.integrate.trapezoid(y, dx=dx)

        observed = qjit(f)(y, dx)
        expected = f(y, dx)
        assert np.allclose(observed, expected)

    @pytest.mark.parametrize(
        "y,x",
        [
            (
                jnp.array([1.0, 2.0, 3.0, 2.0, 3.0, 2.0, 1.0]),
                jnp.array([0.0, 2.0, 5.0, 7.0, 10.0, 15.0, 20.0]),
            ),
            (jnp.sin(jnp.linspace(0, 2 * jnp.pi, 1000)) ** 2, jnp.linspace(0, 2 * jnp.pi, 1000)),
        ],
    )
    def test_trapezoid_gradient(self, y, x):
        """Test trapezoidal integration"""

        def f(y, x):
            return jacobian(jsp.integrate.trapezoid)(y, x)

        observed = qjit(f)(y, x)
        expected = f(y, x)
        assert np.allclose(observed, expected)


class TestLinalg:
    """Tests for the jax.scipy.linalg module"""

    @pytest.mark.parametrize("x", matrix_inputs)
    def test_expm_numerical(self, x):
        """Test basic numerical correctness for jax.scipy.linalg.expm
        for float, int, complex"""

        def f(x):
            return jsp.linalg.expm(x)

        observed = qjit(f)(x)
        expected = f(x)
        assert np.allclose(observed, expected)