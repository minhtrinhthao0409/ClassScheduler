try:
    from flask import Flask, render_template, request
except ImportError:
    import os
    os.system("pip install flask")
    from flask import Flask, render_template, request

from scheduler import generate_schedule, format_schedule_table

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    schedule_html = None
    error_message = None
    
    # Khởi tạo các giá trị mặc định
    form_data = {
        'num_classes': '',
        'num_teachers': '',
        'num_rooms': '',
        'num_labs': '',
        'subjects': '',
        'lab_subjects': ''
    }
    
    if request.method == "POST":
        # Lưu lại dữ liệu form để hiển thị lại
        form_data = {
            'num_classes': request.form.get("num_classes", ''),
            'num_teachers': request.form.get("num_teachers", ''),
            'num_rooms': request.form.get("num_rooms", ''),
            'num_labs': request.form.get("num_labs", ''),
            'subjects': request.form.get("subjects", ''),
            'lab_subjects': request.form.get("lab_subjects", '')
        }
        
        try:
            # Get form data
            num_classes = int(request.form.get("num_classes"))
            num_teachers = int(request.form.get("num_teachers"))
            num_rooms = int(request.form.get("num_rooms"))
            num_labs = int(request.form.get("num_labs"))
            subjects_input = request.form.get("subjects", "")
            subjects = [s.strip() for s in subjects_input.split(",") if s.strip()]
            
            # Validate inputs
            if not subjects:
                error_message = "Vui lòng nhập ít nhất một môn học."
            elif len(subjects) > num_teachers:
                error_message = "Số lượng môn học không được vượt quá số lượng giáo viên."
            elif num_classes <= 0 or num_teachers <= 0 or num_rooms <= 0:
                error_message = "Số lượng lớp, giáo viên và phòng học phải lớn hơn 0."
            else:
                # Process subjects
                subject_map = {s.lower(): s for s in subjects}
                lab_input = request.form.get("lab_subjects", "")
                lab_subjects = set()
                invalid_labs = []
                
                if lab_input.strip():
                    for s in lab_input.split(","):
                        s_norm = s.strip().lower()
                        if s_norm in subject_map:
                            lab_subjects.add(s_norm)
                        else:
                            invalid_labs.append(s.strip())

                if invalid_labs:
                    error_message = f"Môn học lab không hợp lệ: {', '.join(invalid_labs)}. Vui lòng chỉ nhập các môn: {', '.join(subjects)}"
                else:
                # Generate schedule
                    schedule_data = generate_schedule(
                        num_classes=num_classes,
                        num_teachers=num_teachers,
                        subject_map=subject_map,
                        num_classrooms=num_rooms,
                        num_labs=num_labs,
                        lab_subjects=lab_subjects
                    )

                    if schedule_data:
                        schedule_html = format_schedule_table(schedule_data)
                    else:
                        error_message = "Không tìm được lịch phù hợp. Hãy kiểm tra lại số phòng, môn học hoặc giáo viên."

        except ValueError as e:
            error_message = "Vui lòng nhập số hợp lệ cho các trường số lượng."
        except Exception as e:
            error_message = f"Lỗi xử lý: {str(e)}"
    
    return render_template("index.html", 
                         schedule_html=schedule_html, 
                         error_message=error_message, 
                         form_data=form_data)

if __name__ == "__main__":
    app.run(debug=True)
