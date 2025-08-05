import os
import time
import threading
import pandas as pd
import pyperclip
from flask import Flask, request, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

driver = None  # Global driver

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    global driver
    options = webdriver.ChromeOptions()

    # Use existing user profile to persist login
    options.add_argument('--user-data-dir=C:/Temp/WhatsAppProfile')
    options.add_argument('--profile-directory=Default')

    # Stability options
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Optional: headless mode (remove if you want visible browser)
    # options.add_argument('--headless=new')

    # Auto-manage ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://web.whatsapp.com")

    return '<h2>✅ Chrome opened! Scan the QR Code.<br>Once done, <a href="/send">Click Here to Send Messages</a></h2>'

def send_whatsapp_messages(contacts_path, image_path, message):
    global driver
    wait = WebDriverWait(driver, 30)
    success = 0
    fail = 0

    contacts = pd.read_csv(contacts_path)
    contacts.columns = ['PhoneNumber']
    contacts['PhoneNumber'] = contacts['PhoneNumber'].astype(str).str.replace(r'\D', '', regex=True).str.strip()
    contacts['PhoneNumber'] = contacts['PhoneNumber'].apply(lambda x: '+91' + x if not x.startswith('+91') else x)

    for phone in contacts['PhoneNumber']:
        try:
            print(f"📤 Sending to {phone}")
            driver.get(f"https://web.whatsapp.com/send?phone={phone}&text&app_absent=0")
            time.sleep(6)

            # Attach image
            attach_btn_xpath = '//footer//button[@title="Attach"]'
            wait.until(EC.element_to_be_clickable((By.XPATH, attach_btn_xpath))).click()
            time.sleep(1)

            image_input_xpath = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
            image_input = wait.until(EC.presence_of_element_located((By.XPATH, image_input_xpath)))
            image_input.send_keys(image_path)
            print("🖼 Image selected.")
            time.sleep(3)

            img_send_btn_xpath = '//div[@aria-label="Send" or @data-icon="send"]'
            wait.until(EC.element_to_be_clickable((By.XPATH, img_send_btn_xpath))).click()
            print("🖼 Image sent.")
            time.sleep(5)

            # Message input box
            msg_box_xpath = '//footer//div[@role="textbox" and @contenteditable="true"]'
            chat_box = wait.until(EC.presence_of_element_located((By.XPATH, msg_box_xpath)))
            pyperclip.copy(message)
            chat_box.click()
            time.sleep(0.5)
            chat_box.send_keys(Keys.CONTROL, 'v')
            time.sleep(1)

            send_btn_xpath = '//footer//button[@aria-label="Send"]'
            wait.until(EC.element_to_be_clickable((By.XPATH, send_btn_xpath))).click()
            print("💬 Message sent.")
            success += 1
            time.sleep(5)

        except Exception as e:
            print(f"❌ Failed to send to {phone}: {e}")
            fail += 1
            continue

    print(f"✅ Total Sent: {success} | ❌ Failed: {fail}")

@app.route('/send', methods=['GET', 'POST'])
def send():
    if request.method == 'POST':
        try:
            contacts_file = request.files['contacts']
            image_file = request.files['image']
            message = request.form['message']

            # Save uploaded files
            contacts_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, contacts_file.filename))
            image_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, image_file.filename))
            contacts_file.save(contacts_path)
            image_file.save(image_path)

            # Run the send function in a new thread
            thread = threading.Thread(target=send_whatsapp_messages, args=(contacts_path, image_path, message))
            thread.start()

            return '<h2>✅ Message sending started in background.<br>Check terminal for progress logs.</h2><a href="/">Back to Home</a>'

        except Exception as e:
            return f"<h2>Error occurred: {e}</h2><a href='/send'>Back</a>"

    return render_template('send.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
