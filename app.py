import os
from flask import Flask, redirect, render_template, request, url_for
import shutil
from zipfile import ZipFile
from algorithm import calculate_similarity
from scrape_code import get_code
from scrape_subjective import get_data
from codediff import codediff
from flask_bcrypt import Bcrypt
from selenium1 import ai_detection

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    return render_template("educator.html")

def clear_submissions_directory():
    submissions_folder = os.path.join(os.getcwd(), 'submissions')
    for filename in os.listdir(submissions_folder):
        file_path = os.path.join(submissions_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

@app.route("/extract", methods=['POST'])
def extract():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file and file.filename.endswith('.zip'):
        assignment_aim = request.form['assignment_aim']
        prog_lang = request.form['prog_lang']

        submissions_folder = os.path.join(os.getcwd(), 'submissions')
        if not os.path.exists(submissions_folder):
            os.makedirs(submissions_folder, exist_ok=True)

        clear_submissions_directory()

        zip_path = os.path.join(submissions_folder, file.filename)
        file.save(zip_path)

        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(submissions_folder)

        os.remove(zip_path)

        p = zip_path.replace('.zip', '')

        if assignment_aim:
            ai_detection(assignment_aim, p)

        data, stmts, plag_highest, top_lang = calculate_similarity(p)

        sorted_data = sorted(data, key=lambda x: x[2], reverse=True)

        return redirect(url_for("result", path_to_files=p, data=sorted_data, plag_highest=plag_highest, top_lang=top_lang))
    else:
        return "Uploaded file is not a ZIP file."

@app.route("/result")
def result():
    data = request.args.get('data')
    plag_highest = request.args.get('plag_highest')
    top_lang = request.args.get('top_lang')

    if not data:
        return "Data not found. Please sort first."
    return render_template("report.html", data=data, plag_highest=plag_highest, top_lang=top_lang)

@app.route("/list")
def list():
    data = request.args.get('data')
    return render_template("list.html", data=data)

@app.route("/heatmap")
def heatmap():
    return render_template("heatmap.html")

@app.route("/cluster")
def cluster():
    return render_template("cluster.html")

@app.route("/topwords")
def topwords():
    return render_template("topwords.html")

@app.route("/singlecomparison", methods=['POST'])
def single_comparison():
    data = request.args.get('data')
    student = request.form['student']
    newdata = []

    for i in data:
        if i[0] == student or i[1] == student:
            newdata.append([student, i[1], i[2]] if i[0] == student else [student, i[0], i[2]])

    return render_template("singlecomparison.html", data=newdata)

@app.route("/compare", methods=['POST'])
def compare():
    student1 = request.form['student1']
    student2 = request.form['student2']
    path = request.args.get('path_to_files')

    full_path1 = os.path.join(path, student1)
    full_path2 = os.path.join(path, student2)

    texts = codediff(full_path1, full_path2)
    text1, text2 = texts
    l = min(len(text1), len(text2))

    remaining = 1 if len(text1) > len(text2) else -1

    return render_template("codecompare.html", text1=text1, text2=text2, student1=student1, student2=student2, l=l, remaining=remaining)

@app.route("/chatgpt")
def chatgpt():
    assignment_aim = "taylor swift"  # Placeholder
    filepath = request.args.get('path_to_files')

    ai_detection(assignment_aim, filepath)