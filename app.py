import os
import sys
import subprocess
import threading
import uuid
from flask import Flask, request, render_template, jsonify, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key

# Global dictionary to store job status
jobs = {}

def run_domain_checker(job_id, flags):
    domain_checker_path = os.path.abspath('domain_checker.py')
    command = [sys.executable, domain_checker_path] + flags
    jobs[job_id]['status'] = 'running'
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['output'] = result.stdout
    except subprocess.CalledProcessError as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['output'] = e.stderr

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Scheduling logic (unchanged)
        if request.form.get('action') == 'schedule':
            flags = []
            if request.form.get('ignore_ssl'):
                flags.append('--ignore-ssl')
            if request.form.get('check_subdomains'):
                flags.append('--check-subdomains')
            if request.form.get('follow_redirects'):
                flags.append('--follow-redirects')
            if request.form.get('webhook_url_enabled'):
                webhook_url = request.form.get('webhook_url')
                if webhook_url:
                    flags.extend(['--webhook-url', webhook_url])
                    
            cron_schedule = request.form.get('schedule')
            if not cron_schedule:
                flash("Please provide a valid cron schedule.", 'warning')
            else:
                cron_command = " ".join([sys.executable, os.path.abspath('domain_checker.py')] + flags)
                cron_line = f"{cron_schedule} {cron_command}"
                try:
                    try:
                        current_crontab = subprocess.check_output(['crontab', '-l'], text=True)
                    except subprocess.CalledProcessError:
                        current_crontab = ""
                    new_crontab = (current_crontab.strip() + "\n" + cron_line + "\n").strip() + "\n"
                    tmp_cron_file = 'mycron.tmp'
                    with open(tmp_cron_file, 'w') as f:
                        f.write(new_crontab)
                    subprocess.run(['crontab', tmp_cron_file], check=True)
                    os.remove(tmp_cron_file)
                    flash("Scheduled job added to crontab.", 'success')
                except Exception as e:
                    flash(f"Error scheduling job: {str(e)}", 'danger')
            return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/run_script', methods=['POST'])
def run_script():
    # Parse JSON payload from the client
    data = request.get_json()
    flags = []
    if data.get('ignore_ssl'):
        flags.append('--ignore-ssl')
    if data.get('check_subdomains'):
        flags.append('--check-subdomains')
    if data.get('follow_redirects'):
        flags.append('--follow-redirects')
    if data.get('webhook_url_enabled'):
        webhook_url = data.get('webhook_url', '')
        if webhook_url:
            flags.extend(['--webhook-url', webhook_url])
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {'status': 'pending', 'output': ''}
    
    # Start the domain checker in a background thread
    thread = threading.Thread(target=run_domain_checker, args=(job_id, flags))
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/job_status/<job_id>')
def job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'status': 'not found'}), 404
    return jsonify(job)

if __name__ == '__main__':
    app.run(debug=True)