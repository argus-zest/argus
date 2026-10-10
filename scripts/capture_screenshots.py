"""Capture verification screenshots of Argus at different presets.
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options

def capture_all():
    os.makedirs("docs/screenshots", exist_ok=True)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Edge(options=options)
    try:
        driver.get("http://localhost:5173/?demo=1")
        time.sleep(4)  # wait for map basemap and GeoJSON layers to load

        body = driver.find_element(By.TAG_NAME, "body")

        # Click Minto Bridge in the ranked corridor list to populate the inspector
        clickable_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Minto Bridge')]")
        for elem in clickable_elements:
            try:
                driver.execute_script("arguments[0].click();", elem)
                time.sleep(0.5)
                break
            except Exception:
                pass

        # 1. Overview screenshot (Default state with Minto Bridge inspected)
        p_overview = os.path.abspath("docs/screenshots/overview.png")
        driver.save_screenshot(p_overview)
        print("Captured Overview:", p_overview, os.path.getsize(p_overview))

        # 2. Light Preset (Press '1')
        body.send_keys("1")
        time.sleep(1.5)
        p_light = os.path.abspath("docs/screenshots/light_preset.png")
        driver.save_screenshot(p_light)
        print("Captured Light preset:", p_light, os.path.getsize(p_light))

        # 3. Extreme Preset (Press '3')
        body.send_keys("3")
        time.sleep(1.5)
        p_extreme = os.path.abspath("docs/screenshots/extreme_preset.png")
        driver.save_screenshot(p_extreme)
        print("Captured Extreme preset:", p_extreme, os.path.getsize(p_extreme))

        # 4. Hazard Under Water mode (Press 'h')
        body.send_keys("h")
        time.sleep(1.5)
        p_huw = os.path.abspath("docs/screenshots/hazard_under_water.png")
        driver.save_screenshot(p_huw)
        print("Captured Hazard Under Water mode:", p_huw, os.path.getsize(p_huw))

        # 5. Architecture Modal
        buttons = driver.find_elements(By.TAG_NAME, "button")
        arch_btn = None
        for b in buttons:
            if "Architecture" in b.text:
                arch_btn = b
                break

        if arch_btn:
            driver.execute_script("arguments[0].click();", arch_btn)
            time.sleep(1.5)
            p_arch = os.path.abspath("docs/screenshots/architecture_modal.png")
            driver.save_screenshot(p_arch)
            print("Captured Architecture modal:", p_arch, os.path.getsize(p_arch))
            # Close modal with ESC
            body.send_keys(Keys.ESCAPE)
            time.sleep(0.5)

    finally:
        driver.quit()

if __name__ == "__main__":
    capture_all()
