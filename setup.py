# Copyright 2022-2023 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import numpy as np
from pybind11.setup_helpers import intree_extensions
from setuptools import (  # pylint: disable=wrong-import-order
    find_namespace_packages,
    setup,
)

# To build the frontend without any other Catalyst components or dependencies:
build_all_modules = not os.getenv("READTHEDOCS")

if build_all_modules:
    import platform
    import shutil
    import subprocess
    from pathlib import Path

    from setuptools import Extension
    from setuptools.command.build_ext import build_ext

    class CMakeExtension(Extension):
        """
        Extension that uses cpp files in place of pyx files derived from ``setuptools.Extension``
        """

        def __init__(self, name, sourcedir=""):
            """The initial method"""
            Extension.__init__(self, name, sources=[])
            self.sourcedir = Path(sourcedir).absolute()

    class BuildExtension(build_ext):
        """Build infrastructure for Catalyst C++ modules."""

        # The set of supported backends at runtime
        BACKENDS = {
            "lightning.qubit": "ENABLE_LIGHTNING",
            "lightning.kokkos": "ENABLE_LIGHTNING_KOKKOS",
            "braket.qubit": "ENABLE_OPENQASM",
        }

        def build_extension(self, ext: CMakeExtension) -> None:
            """Build extension steps."""

            if not hasattr(ext, "sourcedir"):  # e.g., Pybind11Extension
                super().build_extension(ext)
                return

            # Build the runtime
            self.build_ext_catalyst_runtime(ext)

        def build_ext_catalyst_runtime(self, ext: CMakeExtension) -> None:
            """Build Catalyst Runtime"""
            ext_path = self.get_ext_fullpath(ext.name)
            if not ext_path.startswith("build"):
                # editable mode: copy to lib
                extdir = os.path.join(os.path.dirname(__file__), "frontend", "catalyst", "lib")
            else:
                extdir = str(
                    Path(self.get_ext_fullpath(ext.name))
                    .parent.joinpath("catalyst", "lib")
                    .absolute()
                )

            cfg = "Debug" if int(os.environ.get("DEBUG", 0)) else "Release"
            ninja_bin = self.get_executable("ninja")
            configure_args = [
                "-GNinja",
                f"-DCMAKE_MAKE_PROGRAM={ninja_bin}",
                f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}",
                f"-DCMAKE_C_COMPILER={os.environ.get('C_COMPILER', 'clang')}",
                f"-DCMAKE_CXX_COMPILER={os.environ.get('CXX_COMPILER', 'clang++')}",
                f"-DCMAKE_BUILD_TYPE={cfg}",
                f"-DBUILD_QIR_STDLIB_FROM_SRC={os.environ.get('BUILD_QIR_STDLIB_FROM_SRC', 'OFF')}",
            ]

            # additional conf args
            configure_args += [
                "-DCMAKE_CXX_FLAGS=-fno-lto",
                f"-DCMAKE_C_COMPILER_LAUNCHER={os.environ.get('COMPILER_LAUNCHER', 'ccache')}",
                f"-DCMAKE_CXX_COMPILER_LAUNCHER={os.environ.get('COMPILER_LAUNCHER', 'ccache')}",
                f"-DENABLE_OPENMP={os.environ.get('ENABLE_OPENMP', 'ON')}",
                "-DENABLE_WARNINGS=ON",
            ]

            selected_backends = (
                os.getenv("backend").split(";") if os.getenv("backend") else ["lightning.qubit"]
            )
            for key in selected_backends:
                if key in BuildExtension.BACKENDS:
                    configure_args.append(f"-D{BuildExtension.BACKENDS[key]}=ON")
                else:
                    raise RuntimeError(f"Unsupported backend device: {key}'")

            if platform.system() != "Linux":
                raise RuntimeError(f"Unsupported '{platform.system()}' platform")

            for var, opt in zip(["C_COMPILER", "CXX_COMPILER"], ["C", "CXX"]):
                if os.getenv(var):
                    configure_args += [f"-DCMAKE_{opt}_COMPILER={os.getenv(var)}"]
            if not Path(self.build_temp).exists():
                os.makedirs(self.build_temp)

            cmake_bin = self.get_executable("cmake")
            subprocess.check_call([cmake_bin, ext.sourcedir] + configure_args, cwd=self.build_temp)

            subprocess.check_call(
                [cmake_bin, "--build", ".", "--target rt_capi", f"-j{os.cpu_count()}"],
                cwd=self.build_temp,
            )

            if not os.path.isfile(ext_path):
                # editable mode missing temporary ext file
                open(ext_path, "a").close()

        def get_executable(self, name: str) -> str:
            """Get the absolute path of an executable using shutil.which"""

            name_bin = shutil.which(name)
            if not name_bin:
                raise RuntimeError(f"Not found executable: {name}")
            return str(name_bin)


with open(os.path.join("frontend", "catalyst", "_version.py"), encoding="utf-8") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")

with open(".dep-versions", encoding="utf-8") as f:
    jax_version = [line[4:].strip() for line in f.readlines() if "jax=" in line][0]

requirements = [
    "pennylane>=0.31",
    f"jax=={jax_version}",
    f"jaxlib=={jax_version}",
]

classifiers = [
    "Environment :: Console",
    "Natural Language :: English",
    "Intended Audience :: Science/Research",
    "Development Status :: 3 - Alpha",
    "Operating System :: POSIX",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3 :: Only",
]

lib_path_npymath = os.path.join(np.get_include(), "..", "lib")
intree_extension_list = intree_extensions(["frontend/catalyst/utils/wrapper.cpp"])
for iext in intree_extension_list:
    iext._add_ldflags(["-L", lib_path_npymath])  # pylint: disable=protected-access
    iext._add_ldflags(["-lnpymath"])  # pylint: disable=protected-access
    iext._add_cflags(["-I", np.get_include()])  # pylint: disable=protected-access
    iext._add_cflags(["-std=c++17"])  # pylint: disable=protected-access

attrs = {
    "name": "pennylane-catalyst",
    "provides": ["catalyst"],
    "version": version,
    "python_requires": ">=3.8",
    "install_requires": requirements,
    "packages": find_namespace_packages(
        where="frontend", include=["catalyst", "catalyst.*", "mlir_quantum"]
    ),
    "package_dir": {"": "frontend"},
    "include_package_data": True,
    "maintainer": "Xanadu Inc.",
    "maintainer_email": "software@xanadu.ai",
    "url": "https://github.com/PennyLaneAI/catalyst",
    "description": "A JIT compiler for hybrid quantum programs in PennyLane",
    "long_description": open("README.md", encoding="utf-8").read(),
    "long_description_content_type": "text/markdown",
    "license": "Apache License 2.0",
    "ext_modules": [*intree_extension_list],
}

if build_all_modules:
    attrs["ext_modules"].append(CMakeExtension("catalyst", "runtime"))
    attrs["cmdclass"] = {"build_ext": BuildExtension}

setup(classifiers=classifiers, **(attrs))
