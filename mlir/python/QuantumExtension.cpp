// Copyright 2022-2023 Xanadu Quantum Technologies Inc.

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//     http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "Quantum-c/Dialects.h"
#include "mlir/Bindings/Python/PybindAdaptors.h"

namespace py = pybind11;
using namespace mlir::python::adaptors;

PYBIND11_MODULE(_quantumDialects, m)
{
    //===--------------------------------------------------------------------===//
    // quantum dialect
    //===--------------------------------------------------------------------===//
    auto quantum_m = m.def_submodule("quantum");

    quantum_m.def(
        "register_dialect",
        [](MlirContext context, bool load) {
            MlirDialectHandle handle = mlirGetDialectHandle__quantum__();
            mlirDialectHandleRegisterDialect(handle, context);
            if (load) {
                mlirDialectHandleLoadDialect(handle, context);
            }
        },
        py::arg("context") = py::none(), py::arg("load") = true);

    auto gradient_m = m.def_submodule("gradient");

    gradient_m.def(
        "register_dialect",
        [](MlirContext context, bool load) {
            MlirDialectHandle handle = mlirGetDialectHandle__gradient__();
            mlirDialectHandleRegisterDialect(handle, context);
            if (load) {
                mlirDialectHandleLoadDialect(handle, context);
            }
        },
        py::arg("context") = py::none(), py::arg("load") = true);

    quantum_m.def(
        "compile_asm",
        [](const char *source, bool keep_intermediate) {
            CatalystCReturnCode code = QuantumDriverMain(source, keep_intermediate);
            if (code != ReturnOk) {
                throw std::runtime_error("Compilation failed");
            }
        },
        py::arg("source"), py::arg("keep_intermediate") = false);

    quantum_m.def(
        "mlir_run_pipeline",
        [](const char *source, const char *pipeline) {
            char *dest = nullptr;
            CatalystCReturnCode code = RunPassPipeline(source, pipeline, &dest);
            if (code != ReturnOk) {
                throw std::runtime_error("Canonicalization failed");
            }
            return dest;
        },
        py::arg("source"), py::arg("pipeline"));
}
