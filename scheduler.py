import random
from backtrackingAlgo import CspProblem, backtrack
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

    # def constraint_diff_time_room(vars, vals):
    #     return vals[0] != vals[1]

    # def constraint_teacher_time(vars, vals):
    #     v1, v2 = vars
    #     t1, _ = vals[0]
    #     t2, _ = vals[1]
    #     return class_info[v1]['teacher'] != class_info[v2]['teacher'] or t1 != t2

    # def constraint_class_time(vars, vals):
    #     v1, v2 = vars
    #     t1, _ = vals[0]
    #     t2, _ = vals[1]
    #     return class_info[v1]['class'] != class_info[v2]['class'] or t1 != t2

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
