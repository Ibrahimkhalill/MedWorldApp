import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pyvirtualdisplay import Display


import random
import time

def random_sleep(min_time=1, max_time=3):
    time.sleep(random.uniform(min_time, max_time))


proxy_list = [
    '103.96.106.230:1080',
    # '103.49.202.252:80',
    # '103.86.109.38:80'
]



def get_random_proxy():
    return random.choice(proxy_list)

cookie_file_path = 'cookies.pkl'


def extract_posts():
    # display = Display(visible=0, size=(800, 600))
    # display.start()
    # Setup Chrome options
    options = Options()
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # options.add_argument('--headless')  # Runs Chrome in headless mode.
    # options.add_argument('--no-sandbox')  # Bypass OS security model
    # options.add_argument('--disable-dev-shm-usage')
    # proxy = get_random_proxy()
    # print(f"Using proxy: {proxy}")
    # # Set up the proxy in ChromeOptions
    # options.add_argument(f'--proxy-server=http://{proxy}')

    # # # Initialize the ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)














    # LinkedIn login credentials
    # email = 'mailto:pialatbdcalling@gmail.com'
    # password = 'CKKv8(%FWR)748a'
    


    # email = 'mailto:rah559846@gmail.com'
    # password = 'Ppppp@111'
    email = 'mailto:iahmmedfahad@gmail.com'
    password = 'aloneFreddy516'


    # Profile URL to your recent activity page
    profile_url = 'https://www.linkedin.com/in/jvai-bdcalling-8ba646341/recent-activity/comments/'

    # Visit the profile URL
    # driver.get(profile_url)

    # Wait for the page to load fully
    random_sleep(3, 10)
    # # Login to LinkedIn if not already logged in
    # if "login" in driver.current_url:
    #     driver.find_element(By.ID, 'username').send_keys(email)
    #     driver.find_element(By.ID, 'password').send_keys(password)
    #     driver.find_element(By.XPATH, "//button[@type='submit']").click()
    #     random_sleep(2, 8)
    # else:
    driver.get("https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin&no_popup=true")
    print(driver.title)
    
    random_sleep(3, 10)
    driver.find_element(By.ID, 'username').send_keys(email)
    random_sleep(3, 10)
    driver.find_element(By.ID, 'password').send_keys(password)
    random_sleep(2, 5)
    driver.get_screenshot_as_file("screenshot4.png")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    random_sleep(2, 5)
    driver.get_screenshot_as_file("screenshot5.png")
    body = driver.find_element("tag name", "body")
    for _ in range(30):  # Adjust this number if needed
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(2)
    
    random_sleep(2, 10)    
    driver.get(profile_url)
    print(driver.title)
    random_sleep(2, 10)

    


    # Scroll the page to load more posts (increase this number for more scrolling)
    body = driver.find_element("tag name", "body")
    for _ in range(30):  # Adjust this number if needed
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(2)
    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Find all post containers
    posts = driver.find_elements(By.XPATH, "//div[contains(@class, 'feed-shared-update-v2__control-menu-container')]")
    # see_more_buttons = driver.find_elements(By.XPATH, "//button[.//span[contains(text(), 'more')]]")


    # element = driver.find_element(By.CLASS_NAME, "MetfcPuKDDZHyAgpOsuAgLVedaSGKrEupXM")

    # # Find all the <span> elements inside this element
    # span_elements = element.find_elements(By.TAG_NAME, 'span')

    # # Loop through each span element and print its text
    # for span in span_elements:
    #     print(span.text)



    print(f"Total post is ========== {len(posts)}")

    full_list = []
    # Loop through each post container
    for post in posts:
        # Check if the post contains a job link by looking for the job link class
        job_section = post.find_elements(By.XPATH, ".//div[contains(@class, 'update-components-entity feed-shared-update-v2__update-content-wrapper')]")
        
        
        if job_section:  # If a job link is found in this section
            # Try to find the job link inside the job section
            job_link_elements = job_section[0].find_elements(By.XPATH, ".//a[contains(@href, '/jobs/view/')]")
            
            for job_link in job_link_elements:
                job_url = job_link.get_attribute("href")
                
                # print(f"Found job link: {job_url}")
        
        # Now, let's extract the comments from the post and search for the hashtag
        comments_section = post.find_elements(By.XPATH, ".//div[contains(@class, 'update-components-text')]")
        
        print('-------------------------------------------------------------------')
        # If the comments section exists, check for the hashtag
        if comments_section:
            for comment in comments_section:
                # Look for the hashtag in the comment's text
                hashtag_elements = comment.find_elements(By.XPATH, ".//a[contains(@href, 'hashtag/?keywords=gooditjobsineed')]")

                type2hashtag = comment.find_elements(By.XPATH, ".//a[contains(@href, 'hashtag/?keywords=newtypecontent')]")


                if type2hashtag:
                    p = ''
                    try:
                        element = post.find_element(By.XPATH, ".//*[contains(@class, 'feed-shared-inline-show-more-text')]")

                        span_elements = element.find_elements(By.TAG_NAME, 'span')

                        # Loop through each span element and print its text
                        for span in span_elements:
                            p += span.text
                    except:
                        pass
                    full_list.append(
                        {
                            'job_url': '',
                            'other_details': '',
                            'content': p,
                            'type': 'post'
                        }
                    )
                    print(p)
                
                if hashtag_elements:  # If the hashtag is found
                    print(f"Found hashtag '{hashtag_elements[0].text}' in comment")
                    
                    # Now, check if the post has a job link and print it
                    if job_section:  # Job link exists in this post
                        job_link_elements = job_section[0].find_elements(By.XPATH, ".//a[contains(@href, '/jobs/view/')]")
                        for job_link in job_link_elements:
                            job_url = job_link.get_attribute("href")
                            job_details = job_link.get_attribute("aria-label")
                            # full_list.append(job_url)
                            full_list.append(
                                {
                                    'job_url': job_url,
                                    'other_details': job_details,
                                    'content': '',
                                    'type': 'job'
                                }
                            )
                            print(f"Found job link: {job_details}")
        print('-------------------------------------------------------------------')
    # Clean up and close the browser
    driver.quit()

    print(full_list)
    return full_list



print(extract_posts())
