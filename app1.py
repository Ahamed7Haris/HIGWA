from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import pandas as pd
import time
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from io import StringIO
import threading
from webdriver_manager.chrome import ChromeDriverManager

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'csv', 'txt', 'jpg', 'jpeg', 'png'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global status tracking
status_dict = {
    'running': False,
    'statuses': {}  # phone_number: 'Sent' | 'Failed' | 'Pending'
}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('images')
        csv_file = request.files.get('contacts')
        typed_numbers = request.form.get('typed_numbers')
        message_file = request.files.get('message_file')
        typed_message = request.form.get('typed_message')

        image_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_paths.append(filepath)

        # Get contacts
        if csv_file and allowed_file(csv_file.filename):
            contacts = pd.read_csv(csv_file)
        elif typed_numbers.strip():
            numbers_io = StringIO(typed_numbers)
            contacts = pd.read_csv(numbers_io, names=['PhoneNumber'])
        else:
            return redirect('/')

        # Get message
        if message_file and allowed_file(message_file.filename):
            message = message_file.read().decode('utf-8')
        else:
            message = typed_message

        # Reset status
        status_dict['statuses'].clear()
        status_dict['running'] = True

        thread = threading.Thread(target=send_messages, args=(contacts, image_paths, message))
        thread.start()

        return redirect(url_for('status_page'))

    return render_template('index.html')

@app.route('/status')
def status_page():
    statuses = status_dict['statuses']
    if not statuses:
        return render_template('status.html', status=None)

    success = sum(1 for s in statuses.values() if s == 'Sent')
    failed = sum(1 for s in statuses.values() if s == 'Failed')

    return render_template('status.html', status={
        'success': success,
        'failed': failed,
        'running': status_dict['running']
    })

def send_messages(contacts, image_paths, message):
    contacts.columns = ['PhoneNumber']
    contacts['PhoneNumber'] = contacts['PhoneNumber'].astype(str).str.replace(r'\D', '', regex=True)
    contacts['PhoneNumber'] = contacts['PhoneNumber'].apply(lambda x: '+91' + x if not x.startswith('+91') else x)

    for phone in contacts['PhoneNumber']:
        status_dict['statuses'][phone] = 'Pending'

    options = webdriver.ChromeOptions()
    options.add_argument('--user-data-dir=' + os.path.join(os.getcwd(), 'whatsapp_profile'))
    options.add_argument('--start-maximized')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://web.whatsapp.com")

    wait = WebDriverWait(driver, 60)
    try:
        wait.until(EC.presence_of_element_located((By.ID, "side")))
        time.sleep(5)
    except:
        for phone in contacts['PhoneNumber']:
            status_dict['statuses'][phone] = 'Failed'
        status_dict['running'] = False
        driver.quit()
        return

    for phone in contacts['PhoneNumber']:
        try:
            driver.get(f"https://web.whatsapp.com/send?phone={phone}&text&app_absent=0")
            time.sleep(6)

            # Attach image(s)
            for img_path in image_paths:
                attach_btn = '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div/div[1]/button'
                wait.until(EC.element_to_be_clickable((By.XPATH, attach_btn))).click()
                time.sleep(1)

                img_input_xpath = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
                image_input = wait.until(EC.presence_of_element_located((By.XPATH, img_input_xpath)))
                image_input.send_keys(img_path)
                time.sleep(3)

                img_send_btn = '//*[@id="app"]/div/div[3]/div/div[2]/div[2]/span/div/div/div/div[2]/div/div[2]/div[2]/div'
                wait.until(EC.element_to_be_clickable((By.XPATH, img_send_btn))).click()
                time.sleep(4)

            # Send message
            msg_input_xpath = '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div/div[3]/div[1]/p'
            chat_box = wait.until(EC.presence_of_element_located((By.XPATH, msg_input_xpath)))
            pyperclip.copy(message)
            chat_box.click()
            time.sleep(1)
            chat_box.send_keys(Keys.CONTROL, 'v')
            time.sleep(1)

            send_btn = '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div/div[4]/button'
            wait.until(EC.element_to_be_clickable((By.XPATH, send_btn))).click()
            time.sleep(4)

            status_dict['statuses'][phone] = 'Sent'
        except Exception as e:
            print(f"Error with {phone}: {e}")
            status_dict['statuses'][phone] = 'Failed'
            continue

    driver.quit()
    status_dict['running'] = False

if __name__ == '__main__':
    app.run(debug=True)
