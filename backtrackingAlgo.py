class CspProblem:
    def __init__(self, variables, domains, constraints):
        self.variables = variables
        self.domains = domains
        self.constraints = constraints  # list of (tuple_of_vars, constraint_function)

def call_constraint(assignment, neighbors, constraint):
    values = [assignment[n] for n in neighbors]
    return constraint(neighbors, values)

def find_conflicts(problem, assignment, variable=None, value=None):
    conflicts = []
    for neighbors, constraint in problem.constraints:
        if all(v in assignment for v in neighbors):
            if not call_constraint(assignment, neighbors, constraint):
                conflicts.append((neighbors, constraint))
    return conflicts

def count_conflicts(problem, assignment, variable=None, value=None):
    return len(find_conflicts(problem, assignment, variable, value))

def select_unassigned_variable(problem, assignment, domains):
    # MRV + Degree heuristic
    unassigned = [v for v in problem.variables if v not in assignment]
    if not unassigned:
        return None
    min_size = min(len(domains[v]) for v in unassigned)
    mrv_vars = [v for v in unassigned if len(domains[v]) == min_size]
    if len(mrv_vars) == 1:
        return mrv_vars[0]
    def degree(v):
        return sum(1 for neighbors, _ in problem.constraints if v in neighbors and any(n not in assignment and n != v for n in neighbors))
    return max(mrv_vars, key=degree)

def order_domain_values(problem, variable, assignment, domains):
    # LCV heuristic
    def count_ruled_out(value):
        count = 0
        temp_assignment = assignment.copy()
        temp_assignment[variable] = value
        for neighbors, constraint in problem.constraints:
            if variable in neighbors:
                other_vars = [v for v in neighbors if v != variable]
                for ov in other_vars:
                    if ov not in assignment:
                        for val in domains[ov]:
                            temp_assignment[ov] = val
                            if not call_constraint(temp_assignment, neighbors, constraint):
                                count += 1
                        temp_assignment.pop(ov, None)
        return count

    return sorted(domains[variable], key=count_ruled_out)

def forward_check(problem, variable, value, domains, assignment):
    for neighbors, constraint in problem.constraints:
        if variable in neighbors:
            other_vars = [v for v in neighbors if v != variable]
            for ov in other_vars:
                if ov not in assignment:
                    to_remove = []
                    for val in domains[ov]:
                        temp_assignment = assignment.copy()
                        temp_assignment[variable] = value
                        temp_assignment[ov] = val
                        if not call_constraint(temp_assignment, neighbors, constraint):
                            to_remove.append(val)
                    for val in to_remove:
                        if val in domains[ov]:
                            domains[ov].remove(val)
                    if not domains[ov]:
                        return False
    return True

def recursive_backtrack(problem, assignment, domains):
    if len(assignment) == len(problem.variables):
        return assignment

    var = select_unassigned_variable(problem, assignment, domains)
    if var is None:
        return None

    for value in order_domain_values(problem, var, assignment, domains):
        assignment[var] = value
        domains_copy = {v: list(d) for v, d in domains.items()}

        if forward_check(problem, var, value, domains, assignment):
            result = recursive_backtrack(problem, assignment, domains)
            if result is not None:
                return result

        assignment.pop(var)
        domains = domains_copy

    return None

def backtrack(problem):
    domains_copy = {v: list(d) for v, d in problem.domains.items()}
    return recursive_backtrack(problem, {}, domains_copy)