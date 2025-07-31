import time
import pandas as pd
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Configs
CHROME_PATH = "C://Users//HIG Ajay//Desktop//Auto//chromedriver.exe"
IMAGE_PATH = "C://Users//HIG Ajay//Desktop//Auto//ABCD.jpg"
CONTACTS_PATH = "C://Users//HIG Ajay//Desktop//Auto//TVL.csv"

# WhatsApp message
message = """🌟 Become a Global Doctor! 🌍
Spot Admission Open – Limited Seats!
Get Instant Discount on College Fees! 💸

🎓 Study M.B.B.S / M.D in the Philippines
✅ WHO & MCI Approved Universities
✅ No Donation – Direct Admission

Exclusive Offer:
💥 Avail Spot Admission Benefits
💥 Fee Discounts for early confirmations
💥 Free Counseling by overseas education experts

📅 Admission Dates:
🗓 26.07.25 (Saturday) & 27.07.25 (Sunday)
📍 Venue: 1/134, NGO Colony, Opposite New Bus Stand, Tirunelveli

📞 Call Now to Book Your Slot: 9626158868
🚀 Your Medical Journey Begins Here – Don't Miss Out"""

# Load contacts
contacts = pd.read_csv(CONTACTS_PATH)
contacts.columns = ['PhoneNumber']  # Rename to consistent column name
contacts['PhoneNumber'] = contacts['PhoneNumber'].astype(str).str.strip().str.replace(r'\D', '', regex=True)
contacts['PhoneNumber'] = contacts['PhoneNumber'].apply(lambda x: '+91' + x if not x.startswith('+91') else x)
contacts['PhoneNumber'] = contacts['PhoneNumber'].astype(str).str[:-1]  # Remove last digit

# Setup Chrome WebDriver
options = webdriver.ChromeOptions()
options.add_argument('--user-data-dir=C:/Temp/WhatsAppProfile')  # Keeps login session
driver = webdriver.Chrome(service=Service(CHROME_PATH), options=options)
driver.get("https://web.whatsapp.com")
input("🔍 Scan the QR code and press ENTER to continue...\n")

wait = WebDriverWait(driver, 30)

# Initialize counters
success_count = 0
fail_count = 0

# Loop through contacts
for index, row in contacts.iterrows():
    phone = str(row['PhoneNumber']).strip()
    print(f"\n📤 Sending to {phone}...")

    try:
        # Open WhatsApp chat
        driver.get(f"https://web.whatsapp.com/send?phone={phone}&text&app_absent=0")
        time.sleep(6)

        # Click the attachment (+) icon
        attach_btn_xpath = '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div/div[1]/button'
        wait.until(EC.element_to_be_clickable((By.XPATH, attach_btn_xpath))).click()
        time.sleep(1)

        # Upload image
        image_input_xpath = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
        image_input = wait.until(EC.presence_of_element_located((By.XPATH, image_input_xpath)))
        image_input.send_keys(IMAGE_PATH)
        print("🖼 Image selected.")
        time.sleep(3)

        # Click image send button
        img_send_btn_xpath = '//*[@id="app"]/div/div[3]/div/div[2]/div[2]/span/div/div/div/div[2]/div/div[2]/div[2]/div'
        wait.until(EC.element_to_be_clickable((By.XPATH, img_send_btn_xpath))).click()
        print("🖼 Image sent.")
        time.sleep(5)

        # Paste the text message
        msg_input_xpath = '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div/div[3]/div[1]/p'
        chat_box = wait.until(EC.presence_of_element_located((By.XPATH, msg_input_xpath)))
        pyperclip.copy(message)
        chat_box.click()
        time.sleep(0.5)
        chat_box.send_keys(Keys.CONTROL, 'v')
        time.sleep(1)

        # Click the send button
        send_btn_xpath = '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div/div[4]/button'
        wait.until(EC.element_to_be_clickable((By.XPATH, send_btn_xpath))).click()
        print("💬 Message sent.")
        success_count += 1
        time.sleep(5)

    except Exception as e:
        print(f"❌ Failed to send to {phone}: {e}")
        fail_count += 1
        continue

driver.quit()

# Final Report
print("\n📊 Summary Report:")
print(f"✅ Messages sent successfully: {success_count}")
print(f"❌ Failed to send (possibly invalid numbers): {fail_count}")
