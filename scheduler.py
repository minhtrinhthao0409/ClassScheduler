import random
from collections import defaultdict
from copy import deepcopy

def normalize(text):
    return text.strip().lower()

def time_sort_key(time_str):
    parts = time_str.split()
    shift = parts[0]
    day = f"{parts[1]} {parts[2]}"
    day_order = {'thứ 2': 0, 'thứ 3': 1, 'thứ 4': 2, 'thứ 5': 3, 'thứ 6': 4, 'thứ 7': 5}
    shift_order = {'Sáng': 0, 'Chiều': 1}
    return (day_order[day], shift_order[shift])

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

def generate_schedule(num_classes, num_teachers, subject_map, num_classrooms, num_labs, lab_subjects):
    subjects = list(subject_map.keys())
    if not subjects or len(subjects) > num_teachers:
        return None

    rooms = [f'Phòng {i}' for i in range(1, num_classrooms + 1)]
    lab_rooms = [f'Lab {i}' for i in range(1, num_labs + 1)]
    days = ['thứ 2', 'thứ 3', 'thứ 4', 'thứ 5', 'thứ 6', 'thứ 7']
    times = [f'{part} {day}' for day in days for part in ['Sáng', 'Chiều']]
    random.seed()
    random.shuffle(times)

    classes = [f'Lớp {i}' for i in range(1, num_classes + 1)]
    teachers = [f'GV{i}' for i in range(1, num_teachers + 1)]
    teacher_subjects = {teacher: subjects[i % len(subjects)] for i, teacher in enumerate(teachers)}

    variables = []
    class_info = {}
    for cls in classes:
        for sub in subjects:
            var = f"{cls}_{sub}"
            variables.append(var)
            valid_teachers = [t for t in teachers if teacher_subjects[t] == sub]
            class_info[var] = {
                'class': cls,
                'subject': sub,
                'teacher': random.choice(valid_teachers)
            }

    domains = {}
    for var in variables:
        subject = class_info[var]['subject']
        if subject in lab_subjects:
            domains[var] = [(t, r) for t in times for r in lab_rooms]
        else:
            domains[var] = [(t, r) for t in times for r in rooms]

    constraints = []

    def constraint_diff_time_room(vars, vals):
        return vals[0] != vals[1]

    def constraint_teacher_time(vars, vals):
        v1, v2 = vars
        t1, _ = vals[0]
        t2, _ = vals[1]
        return class_info[v1]['teacher'] != class_info[v2]['teacher'] or t1 != t2

    def constraint_class_time(vars, vals):
        v1, v2 = vars
        t1, _ = vals[0]
        t2, _ = vals[1]
        return class_info[v1]['class'] != class_info[v2]['class'] or t1 != t2

    for i in range(len(variables)):
        for j in range(i + 1, len(variables)):
            v1, v2 = variables[i], variables[j]
            # Ràng buộc phòng không trùng thời gian
            def diff_time_room_closure(v1_, v2_):
                return lambda vars, vals: vals[0] != vals[1]
            constraints.append(((v1, v2), diff_time_room_closure(v1, v2)))

            # Ràng buộc giáo viên không dạy 2 lớp cùng lúc
            if class_info[v1]['teacher'] == class_info[v2]['teacher']:
                def teacher_time_closure(v1_, v2_):
                    return lambda vars, vals: class_info[v1_]['teacher'] != class_info[v2_]['teacher'] or vals[0][0] != vals[1][0]
                constraints.append(((v1, v2), teacher_time_closure(v1, v2)))

            # Ràng buộc lớp không học 2 môn cùng lúc
            if class_info[v1]['class'] == class_info[v2]['class']:
                def class_time_closure(v1_, v2_):
                    return lambda vars, vals: class_info[v1_]['class'] != class_info[v2_]['class'] or vals[0][0] != vals[1][0]
                constraints.append(((v1, v2), class_time_closure(v1, v2)))

    problem = CspProblem(variables, domains, constraints)
    solution = backtrack(problem)

    if solution:
        results = []
        for var, (time, room) in solution.items():
            subject_key = class_info[var]['subject']
            subject_label = subject_map[subject_key].upper()
            results.append({
                'class': class_info[var]['class'],
                'subject': subject_label,
                'teacher': class_info[var]['teacher'],
                'time': time,
                'room': room
            })
        return results
    else:
        return None

def format_schedule_table(schedule_data):
    if not schedule_data:
        return "<p style='color:red;'>Không có dữ liệu lịch học.</p>"
    
    # Sort data by class and time
    sorted_data = sorted(schedule_data, key=lambda x: (x['class'], time_sort_key(x['time'])))
    
    html = """
    <div class="table-container">
        <table class="schedule-table">
            <thead>
                <tr>
                    <th>Lớp</th>
                    <th>Môn học</th>
                    <th>Giáo viên</th>
                    <th>Thời gian</th>
                    <th>Phòng</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for item in sorted_data:
        html += f"""
                <tr>
                    <td>{item['class']}</td>
                    <td>{item['subject']}</td>
                    <td>{item['teacher']}</td>
                    <td>{item['time']}</td>
                    <td>{item['room']}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html
