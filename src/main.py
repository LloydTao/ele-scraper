"""
ele-scraper will go through a module page and download all resources.

Usage:
    The script is run from the command line without any arguments.

        $ python main.py

    You will be prompted to enter a username, password and module ID.
    Selenium will then open a Chrome window so that you can monitor it.

Multiple Modules:
    I am not adding the ability to download multiple modules at once.
    I had a working prototype to download multiple modules in parallel.
    This makes abuse way too easy. This tool should be used responsibly.

Tests:
    Getting to it.
"""


import os

from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def login(driver, username, password):
    """
    Subroutine to log in to VLE.

    Args:
        driver: Current Selenium web driver.
        username: Student's VLE username.
        password: Student's VLE password.
    """
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
    """
    Get a list of resources found on a module page.

    Args:
        driver: Current Selenium web driver.
        course_id: ID found in URL of module.

    Returns:
        resources: List of dicts containing resource name and link.
    """
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
    """
    Grab the resource for a given link.
    (Links on module page go to a 'landing page' for the actual resource.)

    Args:
        driver: Current Selenium web driver.
        resource: A dictionary containing the resource name and link.
    """
    # Get the PDF link from the resource's link.
    driver.get(resource['link'])
    link = driver.find_element_by_class_name("resourceworkaround").find_element_by_tag_name("a").get_attribute("href")

    # Opening the URL will save the file, if it's a resource (i.e. PDF).
    driver.get(link)


def create_driver(course_id):
    """
    Create driver with download directory relevant to module ID.

    Args:
        course_id: ID found in URL of module.

    Returns:
        driver: Selenium web driver used for the duration of the script.

    """
    # Set options and create driver.
    download_dir = os.path.join('C:' + os.sep, 'Users', os.getlogin(), 'Downloads', 'ele-scraper', course_id)
    profile = {
        "plugins.always_open_pdf_externally": True,  # Disable Chrome's PDF Viewer
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
    course_id = input('Enter course id: ')

    # Driver will use download directory of course_id.
    driver = create_driver(course_id)

    login(driver, username, password)
    resources = get_course_resources(driver, course_id)

    # Get files.
    resource = resources[0]
    get_resource(driver, resource)

    # Prompt to close browser.
    input('Close browser? ')

    driver.close()
