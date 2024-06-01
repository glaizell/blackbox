from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from fake_useragent import UserAgent
import pandas as pd

ua = UserAgent(os='windows', browsers=['edge', 'chrome'], min_percentage=1.3)
random_user_agent = ua.random

options = Options()
options.add_experimental_option("detach", True)
options.add_argument(f"user-agent={random_user_agent}")

prefs = {
    "profile.default_content_setting_values.notifications": 2
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.maximize_window()

wait = WebDriverWait(driver, 20)

categories_urls = ["https://blackbox.com.sa/en/smartphones-tablets.html", "https://blackbox.com.sa/en/tv.html",
                   "https://blackbox.com.sa/en/air-conditioners-accessories.html",
                   "https://blackbox.com.sa/en/large-appliances.html",
                   "https://blackbox.com.sa/en/kitchen-appliances/small-appliances.html",
                   "https://blackbox.com.sa/en/computer-accessories.html", "https://blackbox.com.sa/en/gaming.html",
                   "https://blackbox.com.sa/en/personal-care.html"]
scraped_data = []
product_count_per_category = {}


def save_data(scraped_data):
    print("Saving data................................")
    column_headers = ["Category", "Name", "Image URL", "Old Price", "Special Price", "Product URL", "Brand",
                      "Product ID"]
    scraped_df = pd.DataFrame(scraped_data, columns=column_headers)
    file_exists = os.path.exists("scraped_data4.csv")
    if file_exists:
        print("File exists, appending data.............................")
        scraped_df.to_csv("scraped_data4.csv", mode='a', header=False, index=False)
    else:
        print("File does not exist, creating new file...")
        scraped_df.to_csv("scraped_data4.csv", mode='w', header=True, index=False)
    print("Data saved to scraped_data.csv................................")


def click_no_button_if_visible():
    try:
        no_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.wpc_w_f_c_b.wpc_w_f_c_b-n")))
        if no_button.is_displayed():
            no_button.click()
            print("No button clicked")
    except TimeoutException:
        print("No button not found or not visible")
    except NoSuchElementException:
        print("No button not found")


try:
    for url in categories_urls:
        if url == "":
            continue  # Skip empty URLs

        driver.get(url)

        # Check for and click the "No" button if the popup appears
        click_no_button_if_visible()

        retry_attempts_sidebar = 3
        while retry_attempts_sidebar > 0:
            try:
                sidebar_container = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#narrow-by-list > dd:nth-child(2) > form > ul"))
                )
                break  # Break out of the retry loop if successful
            except TimeoutException:
                print("Timed out waiting for sidebar to be present. Retrying...")
                retry_attempts_sidebar -= 1
            except NoSuchElementException:
                print("Sidebar not found.")
                retry_attempts_sidebar -= 1
            except Exception as e:
                print(f"An error occurred: {e}")
                retry_attempts_sidebar -= 1
        if retry_attempts_sidebar == 0:
            print("Failed to locate the sidebar after retries. Skipping this URL.")
            continue

        filter_parents = sidebar_container.find_elements(By.CSS_SELECTOR,
                                                         "li.item.-is-collapsible.-filter-parent > "
                                                         "a.amshopby-filter-parent > span.label")
        for index in range(len(filter_parents)):
            time.sleep(5)

            retry_attempts_sidebar = 3
            while retry_attempts_sidebar > 0:
                try:
                    sidebar_container = wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "#narrow-by-list > dd:nth-child(2) > form > ul"))
                    )
                    filter_parents = sidebar_container.find_elements(By.CSS_SELECTOR,
                                                                     "li.item.-is-collapsible.-filter-parent > "
                                                                     "a.amshopby-filter-parent > span.label")
                    break  # Break out of the retry loop if successful
                except TimeoutException:
                    print("Timed out waiting for sidebar to be present. Retrying...")
                    retry_attempts_sidebar -= 1
                except NoSuchElementException:
                    print("Sidebar not found.")
                    retry_attempts_sidebar -= 1
                except Exception as e:
                    print(f"An error occurred: {e}")
                    retry_attempts_sidebar -= 1
            if retry_attempts_sidebar == 0:
                print("Failed to locate the sidebar after retries. Skipping this filter.")
                continue

            label = filter_parents[index]
            parent_li = label.find_element(By.XPATH,
                                           "./ancestor::li[contains(@class, '-is-collapsible') and contains(@class, "
                                           "'-filter-parent')]")

            data_label = parent_li.get_attribute("data-label")
            print("Category:", data_label)

            checkbox_category = parent_li.find_element(By.CSS_SELECTOR, "input[type='checkbox']")

            WebDriverWait(parent_li, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='checkbox']")))

            checkbox_category.click()
            print("***Checkbox Clicked***")
            time.sleep(5)

            retry_attempts = 3
            while True:  # Loop to go through each page
                try:
                    main_container = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR,
                                                        "#amasty-shopby-product-list > div.category-product.products.wrapper.grid.products-grid > ol"))
                    )
                    product_items = main_container.find_elements(By.CSS_SELECTOR, "li.item.product.product-item")

                    for i in range(len(product_items)):
                        main_container = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR,
                                                            "#amasty-shopby-product-list > div.category-product.products.wrapper.grid.products-grid > ol"))
                        )
                        product_items = main_container.find_elements(By.CSS_SELECTOR, "li.item.product.product-item")
                        item = product_items[i]

                        product_data = {"Category": data_label}

                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", item)

                        product_link = item.find_element(By.CSS_SELECTOR, "a.product-item-photo")
                        driver.execute_script("arguments[0].click();", product_link)

                        time.sleep(2)

                        try:
                            product_title = driver.find_element(By.CSS_SELECTOR,
                                                                "div.page-title-wrapper.product h1.page-title")
                            product_name = product_title.text
                            product_data['Name'] = product_name
                            print("Name:", product_name)
                        except NoSuchElementException:
                            product_data['Name'] = "Name information not available"
                            print("Name information not available")

                        try:
                            product_old_price = driver.find_element(By.CSS_SELECTOR,
                                                                    "div.price-box.price-final_price span.old-price "
                                                                    "span.price-wrapper span.price")
                            product_data['Old Price'] = product_old_price.text
                            print("Old Price:", product_old_price.text)
                        except NoSuchElementException:
                            product_data['Old Price'] = "Old Price information not available"
                            print("Old Price information not available")

                        try:
                            product_special_price = driver.find_element(By.CSS_SELECTOR,
                                                                        "div.price-box.price-final_price span.special-price "
                                                                        "span.price-wrapper span.price")
                            product_data['Special Price'] = product_special_price.text
                            print("Special Price:", product_special_price.text)
                        except NoSuchElementException:
                            product_data['Special Price'] = "Special Price information not available"
                            print("Special Price information not available")

                        try:
                            WebDriverWait(driver, 20).until(
                                lambda d: d.execute_script("return document.readyState") == "complete"
                            )
                            product_image_element = WebDriverWait(driver, 20).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "img.fotorama__img.magnify-opaque"))
                            )
                            product_image_src = product_image_element.get_attribute("src")
                            product_data['Image URL'] = product_image_src
                            print("Image URL:", product_image_src)
                        except TimeoutException:
                            product_data['Image URL'] = "Image URL not available"
                            print("Timed out waiting for page to load or element to be present.")
                        except NoSuchElementException:
                            product_data['Image URL'] = "Image URL not available"
                            print("Image URL not available")

                        more_info_container = wait.until(
                            EC.presence_of_element_located((By.XPATH, "//div[@class='product info detailed']"))
                        )

                        more_info_btn = more_info_container.find_element(By.CSS_SELECTOR, "#tab-label-additional-title")

                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
                                              more_info_btn)

                        more_info_btn.click()
                        time.sleep(1)

                        try:
                            product_url = driver.current_url
                            product_data['Product URL'] = product_url
                            print("Product URL:", product_url)
                        except NoSuchElementException:
                            product_data['Product URL'] = "Product URL not available"
                            print("Product URL not available")

                        more_info_container = wait.until(
                            EC.presence_of_element_located((By.XPATH, "//div[@class='product info detailed']"))
                        )

                        try:
                            product_brand = more_info_container.find_element(By.CSS_SELECTOR,
                                                                             "td.col.data[data-th='Brand']")
                            product_data['Brand'] = product_brand.text
                            print("Brand:", product_brand.text)
                        except NoSuchElementException:
                            product_data['Brand'] = "Brand information not available"
                            print("Brand information not available")

                        try:
                            product_id = more_info_container.find_element(By.CSS_SELECTOR,
                                                                          "td.col.data[data-th='Model Number']")
                            product_data['Product ID'] = product_id.text
                            print("Product ID:", product_id.text)
                        except NoSuchElementException:
                            product_data['Product ID'] = "Product ID not available"
                            print("Product ID not available")

                        print("")
                        scraped_data.append(product_data)
                        save_data(scraped_data)  # Save data after each page
                        scraped_data.clear()
                        print("")

                        if data_label in product_count_per_category:
                            product_count_per_category[data_label] += 1
                        else:
                            product_count_per_category[data_label] = 1

                        print(
                            f"Extracted {product_count_per_category[data_label]} product(s) from category {data_label}")
                        print("=================================================")
                        print("")
                        driver.back()
                        time.sleep(2)

                    # Retry attempts for clicking the next button
                    retry_attempts_next = 3
                    while retry_attempts_next > 0:
                        try:
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(2)  # Wait for the scroll to complete

                            next_button = WebDriverWait(driver, 20).until(
                                EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, "div.pages li.pages-item-next a.action.next"))
                            )
                            print("Next button found")

                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
                                                  next_button)
                            time.sleep(1)  # Give some time for the scroll to complete

                            driver.execute_script("arguments[0].click();", next_button)
                            print("Next button clicked ************************")

                            time.sleep(5)

                            main_container = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                "#amasty-shopby-product-list > div.category-product.products.wrapper.grid.products-grid > ol"))
                            )
                            break  # Break out of the retry loop if successful
                        except TimeoutException:
                            print("Timed out waiting for 'Next' button to be present. Retrying...")
                            retry_attempts_next -= 1
                        except NoSuchElementException:
                            print("No 'Next' button found or it's not clickable.")
                            retry_attempts_next -= 1
                        except Exception as e:
                            print(f"An error occurred: {e}")
                            retry_attempts_next -= 1
                    if retry_attempts_next == 0:
                        print("Failed to click the 'Next' button after retries. Exiting loop.")
                        break

                except TimeoutException as e:
                    print(f"TimeoutException: {e}. Retrying {retry_attempts} more times.")
                    if retry_attempts > 0:
                        retry_attempts -= 1
                        driver.refresh()
                        continue
                    else:
                        break
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    break

            sidebar_container = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#narrow-by-list > dd:nth-child(2) > form > ul"))
            )
            filter_parents = sidebar_container.find_elements(By.CSS_SELECTOR,
                                                             "li.item.-is-collapsible.-filter-parent > "
                                                             "a.amshopby-filter-parent > span.label")

            label = filter_parents[index]
            parent_li = label.find_element(By.XPATH,
                                           "./ancestor::li[contains(@class, '-is-collapsible') and contains(@class, "
                                           "'-filter-parent')]")

            checkbox = parent_li.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            if checkbox.is_selected():
                checkbox.click()
                print("*** Unchecked Checkbox ***")
                time.sleep(2)

finally:
    driver.quit()

# Print the counts for each category
print("\nProduct counts per category:")
for category, count in product_count_per_category.items():
    print(f"{category}: {count} products")
