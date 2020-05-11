"""
ele-scraper will go through a module page and download all resources.

Examples:
    The script is run from the command line without any arguments.

        $ python -u main.py

    You will be prompted to enter a username, password and module ID.
    Selenium will then open a Chrome window so that you can monitor it.

    Make sure you're in the src/ directory, or Selenium will not find the driver.

Todo:
    Currently, the scraper matches resources with "Lecture" in the name.
    This is what I used for my courses, but it may be different for you.
    I'm considering a config file to set this as a different string.
    For now, if you do run into troubles, just edit it in the source code.

Multiple Modules:
    I am not adding the ability to download multiple modules at once.
    I had a working prototype to download multiple modules in parallel.
    This makes abuse way too easy. This tool should be used responsibly.

Tests:
    Getting to it.
"""

import os
import platform

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
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
    print('Navigating to correct log-in page...')
    driver.get("https://vle.exeter.ac.uk/auth/saml2/login.php")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.visibility_of_element_located((By.NAME, 'Login')))
    print('Found log-in page!')
    print()

    # Log in.
    print('Attempting to log in...')
    e = driver.find_element(By.NAME, "IDToken1")
    e.send_keys(username)
    e = driver.find_element(By.NAME, "IDToken2")
    e.send_keys(password)
    e = driver.find_element(By.NAME, "Login.Submit")
    e.click()


def get_module_resources(driver, module_id):
    """
    Get a list of resources found on a module page.

    Args:
        driver: Current Selenium web driver.
        module_id: ID found in URL of module.

    Returns:
        resources: List of dicts containing resource name and link.
    """
    # Get page.
    print('Navigating to module page...')
    url = "https://vle.exeter.ac.uk/course/view.php?id=" + str(module_id)
    driver.get(url)

    # Start collecting resources.
    resources = []

    # Collect activityinstance resources.
    print('Collecting links to activityinstance resources...')
    activities = driver.find_elements_by_class_name("activityinstance")
    for activity in activities:
        try:
            resource_name = activity.find_element_by_class_name("instancename").text
            resource_link = activity.find_element_by_tag_name("a").get_attribute("href")
            if "Lecture" in resource_name:
                print('Found link for:', resource_name)
                resources.append({'name': resource_name, 'link': resource_link})
        except NoSuchElementException:
            print('Could not find one link.')
            print('Assuming activity had no resource and moving on.')
            pass
    print()

    # Collect pluginfile resources.
    print('Collecting links to pluginfile resources...')
    links = driver.find_elements_by_tag_name("a")
    for link in links:
        try:
            if link.text:
                resource_name = link.text
            else:
                resource_name = "Unnamed pluginfile"
            resource_link = link.get_attribute("href")
            if "pluginfile" in resource_link:
                print('Found link for:', resource_name)
                resources.append({'name': resource_name, 'link': resource_link})
        except:
            print('Found pluginfile with no link. Ignoring...')
            pass
    print()

    print('Collected links to', len(resources), 'resources!')
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
    print('Looking for resource:', resource['name'])
    if "pluginfile" in resource['link']:
        # Open a blank page, as getting a download link will use the same tab.
        driver.get("about:blank")
        driver.get(resource['link'])
        print('Pluginfile downloaded!')
    else:
        try:
            driver.get(resource['link'])
            link = driver.find_element_by_class_name("resourceworkaround").find_element_by_tag_name("a").get_attribute("href")
            print('Found resource workaround! Downloading...')
            driver.get(link)
            print('Resource downloaded!')
        except NoSuchElementException:
            print('Page has no resourceworkaround. Is likely not a file. Ignored.')


def create_driver(module_id):
    """
    Create driver with download directory relevant to module ID.

    Args:
        module_id: ID found in URL of module.

    Returns:
        driver: Selenium web driver used for the duration of the script.
    """
    # Get correct web driver file based on OS.
    driver_for_os = {
        'Windows': os.path.join('webdriver', 'win32',   'chromedriver.exe'),
        'Linux':   os.path.join('webdriver', 'linux64', 'chromedriver'),
        'Darwin':  os.path.join('webdriver', 'mac64',   'chromedriver')
    }

    # Get correct download dir for OS.
    dir_for_os = {
        'Windows': os.path.join('C:' + os.sep, 'Users', os.getlogin(), 'Downloads', 'ele-scraper', module_id),
        'Linux': os.path.join(os.path.sep, 'home', os.getlogin(), 'Downloads', 'ele-scraper', module_id),
        'Darwin': os.path.join(os.path.sep, 'home', os.getlogin(), 'Downloads', 'ele-scraper', module_id)
    }

    # Set options and create driver.
    print('Determining directories and file paths...')

    download_dir = dir_for_os[platform.system()]
    print('Saving files to', download_dir)
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

    driver_dir = driver_for_os[platform.system()]
    print('Using web driver at', driver_dir)
    print()

    return Chrome(driver_dir, options=options)


if __name__ == "__main__":
    # Log in.
    username = input('Enter username: ')
    password = input('Enter password: ')
    module_id = input('Enter module id: ')
    print()

    # Driver will use download directory of module_id.
    driver = create_driver(module_id)
    print('Web driver started!')
    print()

    login(driver, username, password)
    print('Log in successful!')
    print()

    resources = get_module_resources(driver, module_id)
    print()

    # Get files.
    resource = resources[0]
    get_resource(driver, resource)
    driver.implicitly_wait(5)
    print()

    # Prompt to close browser.
    input('Finished. Close browser? [y]: ')
    driver.close()
