# RFC-3: Enhanced Equilibrium Solver

**Status:** Implemented
**Author:** TaoCore Team
**Created:** 2026-01-11
**Version:** 0.1.0
**Depends On:** RFC-1

## Abstract

RFC-3 enhances TaoCore's EquilibriumSolver with advanced convergence detection, oscillation handling, and comprehensive diagnostics. These improvements enable robust equilibrium finding for noisy, complex systems where simple tolerance checks are insufficient.

**Key enhancements:**
1. Multiple convergence criteria (tolerance, stability window, oscillation detection)
2. Oscillation detection (2-cycle, 3-cycle, general periodicity)
3. Stability scoring for convergence quality assessment
4. Explicit failure mode reporting via `ConvergenceReason` enum
5. Backward compatibility with RFC-1

## Context & Motivation

### The Problem

RFC-1's EquilibriumSolver used simple single-step convergence:
```python
if residual < tolerance:
    return converged
```

**Limitations:**
- **False convergence**: Single lucky step below tolerance doesn't guarantee stability
- **No oscillation detection**: Cycles run until max_iterations, wasting computation
- **Limited diagnostics**: Only boolean `converged` flag, no failure reason
- **Opaque failures**: Can't distinguish slow convergence from divergence from oscillation

### Real-World Challenges

Systems derived from real data (photos, videos, behavior) often exhibit:
- **Noisy signals**: Transient dips below tolerance that don't indicate true equilibrium
- **Oscillations**: Periodic cycles (2-state, 3-state) that never converge
- **Slow convergence**: Legitimate equilibrium requiring many iterations
- **Divergence**: Amplifying dynamics that explode over time

RFC-3 addresses these by treating equilibrium finding as a **diagnostic process**, not just a yes/no question.

---

## Design Principles

### 1. Equilibrium vs. Optimization

**TaoCore does NOT optimize.**

| Optimization | Equilibrium (TaoCore) |
|--------------|----------------------|
| Minimizes loss | Seeks stability |
| Requires labels/objectives | Requires update rules |
| Learns parameters | Applies deterministic updates |
| Gradient descent | Fixed-point iteration |

**RFC-3 philosophy:** Equilibrium is **descriptive** (what does the system settle into?) not **prescriptive** (what should it become?).

### 2. Failure as Signal

Non-convergence is **information**, not error:
- Oscillation → conflicting signals in the system
- Slow convergence → weak attractor
- Divergence → unstable dynamics

RFC-3 exposes these as first-class diagnostics via `ConvergenceReason`.

### 3. Inspectable Diagnostics

All solver behavior is observable:
- `residuals`: Full history of ||S_{t+1} - S_t||
- `stability_score`: Quality metric [0, 1]
- `convergence_reason`: Why solver stopped
- `oscillation_detected`: Whether periodic behavior found

Diagnostics enable **trust calibration** and **debugging**.

### 4. Backward Compatibility

RFC-1 code continues to work:
```python
# RFC-1 style (still works)
solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6)
result = solver.solve(initial, update_rule)
if result.converged:
    # ...
```

Default `stability_window=1` preserves original single-step behavior.

---

## Implementation Specifications

### 1. ConvergenceReason Enum

**File:** `src/taocore/solvers/equilibrium.py`

```python
class ConvergenceReason(Enum):
    TOLERANCE = "tolerance"       # Residual < tolerance (RFC-1 behavior)
    STABILITY = "stability"       # Stable for N consecutive steps (RFC-3)
    OSCILLATION = "oscillation"   # Periodic cycle detected (RFC-3)
    MAX_ITERATIONS = "max_iterations"  # Hit iteration limit
```

**Purpose:** Explicit failure mode reporting. Users can distinguish:
- **TOLERANCE**: Quick convergence (backward compatible)
- **STABILITY**: Sustained convergence (more robust)
- **OSCILLATION**: System is cycling, won't converge
- **MAX_ITERATIONS**: Need more iterations or different dynamics

---

### 2. Enhanced EquilibriumResult

**Fields:**
```python
@dataclass
class EquilibriumResult:
    state: StateVector              # Final state (or best approximation)
    converged: bool                 # Whether equilibrium reached
    iterations: int                 # Number of update steps
    residuals: List[float]          # ||S_{t+1} - S_t|| history
    convergence_reason: ConvergenceReason  # Why solver stopped (RFC-3)
    stability_score: Optional[float]  # Quality metric [0, 1] (RFC-3)
    oscillation_detected: bool      # Periodic behavior found (RFC-3)
```

**Backward compatibility:** RFC-1 code reading `converged` and `iterations` continues to work.

---

### 3. Convergence Criteria

#### Tolerance Convergence (RFC-1)

**Trigger:** Single step with `residual < tolerance`

**Use case:** Fast, clean convergence

**Backward compatible:** `stability_window=1` (default)

```python
solver = EquilibriumSolver(tolerance=1e-6)  # RFC-1 behavior
```

#### Stability Window (RFC-3)

**Trigger:** `N` consecutive steps with `residual < tolerance`

**Use case:** Noisy systems where transient dips don't indicate equilibrium

**Example:**
```python
solver = EquilibriumSolver(
    tolerance=1e-6,
    stability_window=5  # Require 5 stable steps
)
```

**Reason:** `ConvergenceReason.STABILITY`

#### Oscillation Detection (RFC-3)

**Trigger:** Periodic state repetition detected

**Algorithms:**
- **2-cycle detection**: `S_t ≈ S_{t-2}` for consecutive pairs
- **3-cycle detection**: `[S_t, S_{t-1}, S_{t-2}] ≈ [S_{t-3}, S_{t-4}, S_{t-5}]`
- **General detection**: Any state repeating within `oscillation_window`

**Example:**
```python
solver = EquilibriumSolver(
    tolerance=1e-6,
    oscillation_window=10,  # Check last 10 states
    detect_oscillation=True  # Enable (default)
)
```

**Reason:** `ConvergenceReason.OSCILLATION`

**Benefits:**
- Early termination (saves 90%+ iterations on oscillating systems)
- Explicit failure signal
- Distinguishes oscillation from slow convergence

#### Max Iterations (RFC-1 + RFC-3)

**Trigger:** Iteration count reaches `max_iterations`

**Use case:** Safety cap on computation

**Example:**
```python
solver = EquilibriumSolver(max_iterations=100)
```

**Reason:** `ConvergenceReason.MAX_ITERATIONS`

**Interpretation:** Could be slow convergence, divergence, or complex dynamics.

---

### 4. Stability Score

**Purpose:** Quantify convergence quality [0, 1]

**Calculation:**
```python
# Use recent residuals (last 10 steps)
mean_residual = np.mean(recent_residuals)
std_residual = np.std(recent_residuals)

# Log-scale scoring relative to tolerance
if mean_residual < tolerance:
    mean_score = 1.0
else:
    mean_score = max(0, 1 - log10(mean_residual / tolerance))

# Similar for variance
variance_score = ...

# Combined score (geometric mean)
stability_score = sqrt(mean_score * variance_score)
```

**Interpretation:**
- **1.0**: Perfect convergence (residual → 0)
- **0.8-1.0**: Very stable
- **0.5-0.8**: Moderate stability
- **0-0.5**: Weak convergence or unstable
- **0.0**: No convergence

**Use case:** Trust calibration - decide whether to use result based on quality.

---

### 5. Oscillation Detection Implementation

**Algorithm:**

```python
def _detect_oscillation(state_history: List[StateVector]) -> bool:
    # 2-cycle: check if [S_{t-3}, S_{t-2}] ≈ [S_{t-1}, S_t]
    if len(state_history) >= 4:
        if distance(S_{t-3}, S_{t-1}) < tol and distance(S_{t-2}, S_t) < tol:
            return True

    # 3-cycle: check if recent 3 states match earlier 3
    if len(state_history) >= 6:
        recent = state_history[-3:]
        earlier = state_history[-6:-3]
        if all(distance(recent[i], earlier[i]) < tol for i in range(3)):
            return True

    # General: check if any recent state appeared before
    if len(state_history) >= oscillation_window:
        latest = state_history[-1]
        for earlier_state in state_history[:-2]:
            if distance(latest, earlier_state) < tol:
                return True

    return False
```

**Complexity:** O(window_size) per iteration

**False positives:** Minimized by requiring exact state repetition within tolerance.

---

## Usage Examples

### Example 1: Basic Tolerance (RFC-1 Compatible)

```python
from taocore import EquilibriumSolver, StateVector
import numpy as np

def damping_rule(state):
    return StateVector(state.array * 0.5)

solver = EquilibriumSolver(tolerance=1e-6)
initial = StateVector(np.array([10.0, 5.0]))

result = solver.solve(initial, damping_rule)

if result.converged:
    print(f"Equilibrium: {result.state}")
    print(f"Iterations: {result.iterations}")
```

### Example 2: Stability Window (Noisy Systems)

```python
def noisy_damping(state):
    # Add small noise to simulate real-world signals
    noise = np.random.randn(*state.array.shape) * 0.001
    return StateVector(state.array * 0.8 + noise)

solver = EquilibriumSolver(
    tolerance=1e-5,
    stability_window=10,  # Require 10 consecutive stable steps
    max_iterations=200
)

result = solver.solve(initial, noisy_damping)

if result.convergence_reason == ConvergenceReason.STABILITY:
    print(f"Sustained convergence after {result.iterations} iterations")
    print(f"Stability score: {result.stability_score:.3f}")
```

### Example 3: Oscillation Detection

```python
def conflicting_signals(state):
    # Simulate conflicting update rules that oscillate
    return StateVector(-state.array)  # Sign flip

solver = EquilibriumSolver(
    tolerance=1e-6,
    oscillation_window=10,
    detect_oscillation=True
)

result = solver.solve(initial, conflicting_signals)

if result.oscillation_detected:
    print(f"Oscillation detected after {result.iterations} iterations")
    print(f"Reason: {result.convergence_reason}")
    print("System has conflicting dynamics - won't converge")
```

### Example 4: Comprehensive Diagnostics

```python
result = solver.solve(initial, update_rule)

print(f"Converged: {result.converged}")
print(f"Reason: {result.convergence_reason.value}")
print(f"Iterations: {result.iterations}")
print(f"Stability score: {result.stability_score:.3f}")
print(f"Oscillation: {result.oscillation_detected}")
print(f"Final residual: {result.residuals[-1]:.2e}")
print(f"Residual reduction: {result.residuals[0] / result.residuals[-1]:.1e}x")

# Decide whether to use result
if result.stability_score > 0.8:
    use_result(result.state)
else:
    warn("Low stability - result may be unreliable")
```

### Example 5: Graph Neighbor Averaging

```python
# Simulate node updating based on neighbors
neighbors = {
    "n1": ["n2", "n3"],
    "n2": ["n1", "n3"],
    "n3": ["n1", "n2"]
}
node_states = {
    "n1": np.array([1.0]),
    "n2": np.array([10.0]),
    "n3": np.array([5.0])
}

def neighbor_average(node_id):
    def update(state):
        neighbor_vals = [node_states[nid] for nid in neighbors[node_id]]
        avg = np.mean(neighbor_vals, axis=0)
        # Move 50% toward average
        new_val = 0.5 * state.array + 0.5 * avg
        return StateVector(new_val)
    return update

# Find equilibrium for each node
solver = EquilibriumSolver(tolerance=1e-5)
for node_id in node_states:
    initial = StateVector(node_states[node_id])
    result = solver.solve(initial, neighbor_average(node_id))
    node_states[node_id] = result.state.array
```

---

## Testing Strategy

### Test Coverage

**115 total tests** (15 new for RFC-3)

**New tests in `tests/test_solvers.py`:**

**Convergence Criteria:**
- `test_stability_window_convergence` - N-step stability requirement
- `test_oscillation_detection_2cycle` - Sign-flip oscillation
- `test_oscillation_detection_3cycle` - 3-state cycle
- `test_max_iterations_reached` - Timeout termination
- `test_oscillation_disabled` - Optional oscillation detection

**Diagnostics:**
- `test_stability_score_high` - Well-converged system
- `test_stability_score_low` - Poor convergence
- `test_residuals_history` - Tracking residuals
- `test_convergence_reason_enum` - All enum values

**Edge Cases:**
- `test_immediate_convergence` - Already at equilibrium
- `test_zero_state_equilibrium` - Converge to zero
- `test_large_state_space` - High-dimensional (100D)
- `test_divergent_system` - Amplifying dynamics

**Update Rules:**
- `test_neighbor_averaging_rule` - Graph dynamics
- `test_bounded_update_rule` - Constrained state space

**Updated test in `tests/test_edge_cases.py`:**
- `test_equilibrium_no_convergence` - Now detects oscillation early

**Verification script:**
- `examples/rfc3_verification.py` - Comprehensive feature demonstration

---

## Performance Impact

### Computational Overhead

**Per iteration:**
- Residual calculation: O(state_dim)
- Oscillation detection: O(window_size × state_dim)
- Stability score: O(window_size)

**Overall:** Negligible for typical state dimensions (< 1000).

**Benefits:**
- **Oscillation detection saves 90%+ iterations** on cyclic systems
- Stability window adds ~5-10% iterations but ensures robustness
- Diagnostics enable trust calibration

---

## Acceptance Criteria

RFC-3 is complete when:

- [x] `ConvergenceReason` enum implemented
- [x] Enhanced `EquilibriumResult` with new fields
- [x] Stability window convergence works
- [x] Oscillation detection (2-cycle, 3-cycle) functional
- [x] Stability score computation accurate
- [x] Backward compatible with RFC-1 (default `stability_window=1`)
- [x] Comprehensive tests (≥15 new tests)
- [x] Verification script passes
- [x] Exports updated (`ConvergenceReason` in `__init__.py`)
- [x] Documentation complete

**Status: ✓ All criteria met**

---

## Future Work

### RFC-7: Adaptive Solvers
- Auto-tune tolerance based on residual history
- Dynamic stability window adjustment
- Early stopping heuristics

### RFC-8: Parallel Equilibrium
- Multi-initial-state solving (find multiple attractors)
- Parallel BFS for graph updates
- Basin of attraction analysis

### RFC-9: Stochastic Equilibrium
- Probabilistic convergence criteria
- Uncertainty quantification
- Monte Carlo equilibrium

---

## Comparison with RFC-1

| Feature | RFC-1 | RFC-3 |
|---------|-------|-------|
| Convergence criteria | Tolerance only | Tolerance, stability window, oscillation |
| Diagnostics | `converged`, `iterations`, `residuals` | + `convergence_reason`, `stability_score`, `oscillation_detected` |
| Oscillation handling | Runs to max_iterations | Early detection and termination |
| Failure modes | Boolean `converged` | Explicit `ConvergenceReason` enum |
| Stability assessment | None | `stability_score` [0, 1] |
| Backward compatible | N/A | ✓ Full compatibility |

---

## Conclusion

RFC-3 transforms EquilibriumSolver from a simple fixed-point iterator into a **diagnostic equilibrium analysis tool**.

**Key improvements:**
- ✓ Multiple convergence criteria for robustness
- ✓ Oscillation detection saves computation
- ✓ Stability scoring enables trust calibration
- ✓ Explicit failure modes via `ConvergenceReason`
- ✓ Comprehensive diagnostics as first-class outputs
- ✓ Backward compatible with RFC-1

**Design philosophy preserved:**
- Equilibrium is descriptive, not prescriptive
- No optimization or learning
- Inspectable, deterministic behavior
- Failure modes are signals, not errors

**TaoCore now supports robust equilibrium finding for real-world noisy systems while maintaining domain-agnostic abstraction.**

---

**Implementation:** 3 files modified, 1 enum added, 15 tests added
**Test coverage:** 115 tests passing
**Status:** Implemented and verified ✓

Questions or contributions? See README.md for details.
