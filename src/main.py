import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def login(driver, username, password):
    
    # Wait for log-in form.
    driver.get("https://vle.exeter.ac.uk/auth/saml2/login.php")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.visibility_of_element_located((By.NAME, 'Login')))
    
    # Log in.
    e = driver.find_element(By.NAME, "IDToken1")
    e.send_keys(username)
    e = driver.find_element(By.NAME, "IDToken2")
    e.send_keys(password)
    e = driver.find_element(By.NAME, "Login.Submit")
    e.click()


def get_course_resources(driver, course_id):
    
    # Get page.
    url = "https://vle.exeter.ac.uk/course/view.php?id=" + str(course_id)
    driver.get(url)
    
    # Collect resources.
    resources = []
    activities = driver.find_elements_by_class_name("activityinstance")
    for activity in activities:
        name = activity.find_element_by_class_name("instancename").text.replace("\nFile", "")
        link = activity.find_element_by_tag_name("a").get_attribute("href")
        if "Lecture" in name:
            resources.append({'name': name, 'link': link})
    
    return resources


def get_resource(driver, resource):
    
    # Get the PDF link from the resource's link.
    driver.get(resource['link'])
    link = driver.find_element_by_class_name("resourceworkaround").find_element_by_tag_name("a").get_attribute("href")
    
    # Opening the URL will save the file, if it's a resource (i.e. PDF).
    driver.get(link)
    
    
def create_driver(course_id):
    
    # Set options and create driver.
    base_dir = r"C:\Users\Lewis Lloyd\downloads\ele-scraper"
    course_dir = course_id
    download_dir = os.path.join(base_dir, course_dir)
    
    profile = {
        "plugins.always_open_pdf_externally": True, # Disable Chrome's PDF Viewer
        "download.default_directory": download_dir, 
        "download.extensions_to_open": "applications/pdf",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", profile)
    
    driver = Chrome("webdriver/chromedriver.exe", options=options)
    
    return driver


if __name__ == "__main__":   
    
    # Log in.
    username = input('Enter username: ')
    password = input('Enter password: ')
    course_id = input('Enter course id: ') # 2890
    
    # Driver will use download directory of course_id.
    driver = create_driver(course_id)
    
    login(driver, username, password)
    resources = get_course_resources(driver, course_id)
    
    # Get files.
    for resource in resources:
        get_resource(driver, resource)
    
    # Prompt to close browser.
    input('Close browser? ')
    
    driver.close()
