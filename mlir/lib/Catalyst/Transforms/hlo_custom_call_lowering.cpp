// Copyright 2023 Xanadu Quantum Technologies Inc.

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//     http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#define DEBUG_TYPE "hlocustomcalls"

#include <vector>

#include "llvm/Support/Debug.h"

#include "mhlo/IR/hlo_ops.h"
#include "mhlo/transforms/passes.h"

#include "mlir/Dialect/Index/IR/IndexDialect.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Transforms/GreedyPatternRewriteDriver.h"

#include "Catalyst/Transforms/Patterns.h"

using namespace llvm;
using namespace mlir;
using namespace catalyst;

namespace catalyst {
#define GEN_PASS_DEF_HLOCUSTOMCALLLOWERINGPASS
#include "Catalyst/Transforms/Passes.h.inc"

struct HloCustomCallLoweringPass : impl::HloCustomCallLoweringPassBase<HloCustomCallLoweringPass> {
    using HloCustomCallLoweringPassBase::HloCustomCallLoweringPassBase;

    void runOnOperation() final
    {
        LLVM_DEBUG(dbgs() << "hlo custom call lowering pass"
                          << "\n");

        RewritePatternSet patterns(&getContext());
        populateHloCustomCallPatterns(patterns);
        if (failed(applyPatternsAndFoldGreedily(getOperation(), std::move(patterns)))) {
            return signalPassFailure();
        }
    }
};

std::unique_ptr<Pass> createHloCustomCallLoweringPass()
{
    return std::make_unique<HloCustomCallLoweringPass>();
}
} // namespace catalyst