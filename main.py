import csv
import numpy as np
import random

from pathlib import Path

from scipy.io import wavfile
from flask import Flask, render_template, send_file, flash, request, redirect
import os
import tempfile
import shutil


WAV_EXTENSION = ".wav"

from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'csv'}

FILE_NAME_COL = 'Name'
FILE_DURATION_COL = "Duration"

def parse_validate_and_clean(csv_name, file_name_column, file_length_column, debug):
    error_message=''
    is_valid = True
    rows = []
    with open(csv_name) as csvfile:
        reader = csv.DictReader(
            csvfile,
        )
        row_number = 1
        seen_file_names = set()
        for row in reader:
            row_number += 1
            if not file_name_column in row:
                error_message+=f'A column named {FILE_NAME_COL} does not exist. Please enter a different column name and try again'
                is_valid = False
                break
            if not file_length_column in row:
                error_message+=f'A column named {FILE_DURATION_COL} does not exist. Please enter a different column name and try again'
                is_valid = False
                break
            clean_file_name = row[file_name_column].strip()
            if not clean_file_name.endswith(WAV_EXTENSION):
                if debug:
                    print(f"Adding {WAV_EXTENSION} to {clean_file_name}")
                clean_file_name = f"{clean_file_name}{WAV_EXTENSION}"
            if clean_file_name in seen_file_names:
                error_message+=f"Row number {row_number} has a duplicate filename, {clean_file_name}. Please rename and try again"
                is_valid = False
                break
            seen_file_names.add(clean_file_name)
            row[file_name_column] = clean_file_name

            try:
                row[file_length_column] = float(row[file_length_column])
                rows.append(row)
            except:
                error_message+=f"Row number {row_number} has an invalid value. Duration column contains {row[file_length_column]}. Please enter a number and try again"
                is_valid = False
                break
    return is_valid, error_message, rows



def write_beeps(result_folder, rows, file_name_column, file_length_column, debug):
    for row in rows:
        file_name = os.path.join(result_folder, row[file_name_column])
        duration = row[file_length_column]
        if debug:
            print(f"Creating {file_name} with {duration} second duration")
        # write_sine(file_name=file_name, duration=duration)
        write_beep(file_name=file_name, duration=duration)


def write_beep(
    file_name: Path,
    duration=5.0,
):
    # https://www.colincrawley.com/audio-file-size-calculator/
    f = 80  # sine frequency, Hz, may be float
    sample_rate_hz = 100
    samples = (
        np.sin(2 * np.pi * np.arange(sample_rate_hz * duration) * f / sample_rate_hz)
    ).astype(np.uint8)
    wavfile.write(file_name, sample_rate_hz, samples)

def make_a_lot(dir, count):
    assert count > 0, "count must be > 0"
    while count > 0:
        print(count)
        write_beep(f"{dir}/{count}.wav", 15)
        count -= 1


app = Flask(  # Create a flask app
	__name__,
	template_folder='templates',  # Name of html file folder
	static_folder='static'  # Name of directory for static files
)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')  
def render_form():
  return render_template('form.html')



@app.route('/submit', methods=['POST'])  
def submit():
  with tempfile.TemporaryDirectory() as tmpdirname:
    print('created temporary directory', tmpdirname)
  # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        csv_path = os.path.join(tmpdirname, filename)
        file.save(csv_path)
        return business_logic(tmpdirname, csv_path)


def business_logic(tmpdirname, csv_path):
    print('created temporary directory', tmpdirname)
    result_folder = os.path.join(tmpdirname, 'result')
    print(f"result folder: {result_folder}")
    os.mkdir(result_folder)
    is_valid, error_message, rows = parse_validate_and_clean(csv_path, FILE_NAME_COL, FILE_DURATION_COL, True)
    write_beeps(result_folder, rows, FILE_NAME_COL, FILE_DURATION_COL, True)
    
    if not is_valid:
      return render_template('form.html', error_message=error_message)

    print(shutil.make_archive(result_folder, 'zip', result_folder))

    return send_file(f"{result_folder}.zip", as_attachment=True)

if __name__ == "__main__":  # Makes sure this is the main process
	app.run( # Starts the site
		host='0.0.0.0',  # EStablishes the host, required for repl to detect the site
		port=random.randint(2000, 9000)  # Randomly select the port the machine hosts on.
	)