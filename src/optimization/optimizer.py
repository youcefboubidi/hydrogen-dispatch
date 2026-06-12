"""pymoo optimizer wrapper — Phase 5 stub, not yet implemented.

Will wrap the single-point pipeline in a pymoo problem (PSO or GA): decision
variable = electrolyzer setpoint (grid import follows as P_elz - P_pv),
objective = min cost/kg or max H2, constraints = network limits from
src.optimization.objective. pymoo is intentionally NOT in requirements.txt
yet; it is added in Phase 5 of PROJECT_PLAN.md (PySwarms is the fallback only
if explicitly requested).
"""
