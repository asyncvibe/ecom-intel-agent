import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import re
import random
import os
import glob
from time import sleep

def delete_previous_csv_files():
    """Delete all previous CSV files before starting new scrape."""
    for file in glob.glob('ebay_products_*.csv'):
        try:
            os.remove(file)
            print(f"Deleted previous file: {file}")
        except Exception as e:
            print(f"Error deleting {file}: {e}")

async def scrape_product_ebay(product_name, max_products=1, max_retries=3):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-dev-shm-usage', '--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            bypass_csp=True,
            ignore_https_errors=True
        )
        page = await context.new_page()
        all_products_data = []
        
        try:
            # Navigate directly to eBay search results with retries
            print(f"Searching for {product_name} on eBay...")
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={product_name.replace(' ', '+')}"
            print(f"Navigating to: {search_url}")
            
            for attempt in range(max_retries):
                try:
                    await page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
                    await page.wait_for_load_state("domcontentloaded", timeout=30000)
                    await asyncio.sleep(3)  # Let the page settle
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"Attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(2)
            
            # Take a screenshot for debugging if needed
            await page.screenshot(path="screenshot.png")
            print("Saved screenshot to screenshot.png for debugging")
            
            # Get multiple product links (eBay)
            print("Looking for product links...")
            
            # Wait for the search results to load
            await page.wait_for_selector("li.s-item", timeout=30000)
            await asyncio.sleep(2)  # Give extra time for dynamic content
            
            # Try different selectors for product links
            selectors = [
                "li.s-item a.s-item__link",
                "li.s-item a[href*='itm']",
                "div.s-item__info a[href*='itm']"
            ]
            
            # First collect all potential URLs
            potential_urls = []
            for selector in selectors:
                try:
                    print(f"Trying selector: {selector}")
                    links = await page.query_selector_all(selector)
                    
                    # Skip first 4 products (ads)
                    for link in links[4:]:
                        try:
                            href = await link.get_attribute("href")
                            if not href or 'itm' not in href:
                                continue
                                
                            # Extract item ID from the URL
                            item_id = None
                            if 'itm/' in href:
                                item_id = href.split('itm/')[-1].split('/')[0].split('?')[0]
                            
                            # Validate item ID format
                            if not item_id or not item_id.isdigit() or len(item_id) < 8:
                                continue
                                
                            normalized_url = f"https://www.ebay.com/itm/{item_id}"
                            if normalized_url not in potential_urls:
                                potential_urls.append(normalized_url)
                                
                        except Exception as e:
                            print(f"Error processing link: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue
            
            print(f"Found {len(potential_urls)} potential product URLs (excluding first 4 ad listings)")
            
            # Now validate and collect the required number of URLs
            product_urls = []
            validation_page = await context.new_page()
            
            try:
                # Only try to validate up to 3 times the requested number of products
                max_validation_attempts = min(max_products * 3, len(potential_urls))
                
                for i, url in enumerate(potential_urls[:max_validation_attempts]):
                    if len(product_urls) >= max_products:
                        break
                        
                    try:
                        print(f"Validating URL {i+1}/{max_validation_attempts}: {url}")
                        
                        # Navigate to the page and wait for it to load
                        await validation_page.goto(url, timeout=30000, wait_until='networkidle')
                        await asyncio.sleep(2)  # Give extra time for dynamic content
                        
                        # Try multiple selectors for product title
                        title_selectors = [
                            "h1.x-item-title__mainTitle",
                            "h1[itemprop='name']",
                            "div.ux-layout-section__content h1",
                            "div.ux-layout-section__content span.ux-textspans--BOLD",
                            "div.ux-layout-section__content span.ux-textspans"
                        ]
                        
                        title_found = False
                        for selector in title_selectors:
                            try:
                                title_elem = validation_page.locator(selector)
                                if await title_elem.count() > 0:
                                    title_text = await title_elem.first.inner_text()
                                    if title_text and len(title_text.strip()) > 0:
                                        title_found = True
                                        product_urls.append(url)
                                        print(f"Found valid product URL ({len(product_urls)} of {max_products}): {url}")
                                        print(f"Product title: {title_text[:50]}...")
                                        if len(product_urls) >= max_products:
                                            print("Found all required products, stopping validation.")
                                            break
                                        break
                            except Exception as e:
                                continue
                        
                        if not title_found:
                            print(f"Skipping URL - no product title found: {url}")
                            
                    except Exception as e:
                        print(f"Error validating URL {url}: {e}")
                        continue
                    
                    # Clear the page before next validation
                    try:
                        await validation_page.goto('about:blank')
                        await asyncio.sleep(1)
                    except Exception:
                        # If clearing fails, create a new page
                        await validation_page.close()
                        validation_page = await context.new_page()
            finally:
                await validation_page.close()
            
            if not product_urls:
                print("Could not find any valid product URLs.")
                return None
                
            print(f"Found {len(product_urls)} valid product URLs")
            
            # Process each product
            for index, url in enumerate(product_urls, 1):
                print(f"\nProcessing product {index} of {len(product_urls)}...")
                try:
                    # Random delay between products (3-7 seconds)
                    delay = random.uniform(3, 7)
                    print(f"Waiting for {delay:.1f} seconds before processing next product...")
                    await asyncio.sleep(delay)
                    
                    # Verify URL is accessible
                    for attempt in range(max_retries):
                        try:
                            response = await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                            if response.status == 404:
                                print(f"Product page not found (404): {url}")
                                continue
                            
                            await page.wait_for_load_state("domcontentloaded", timeout=30000)
                            await asyncio.sleep(random.uniform(2, 3))
                            
                            # Verify we're on a valid product page
                            title = await page.title()
                            if not title or title == '':
                                raise Exception("Empty page loaded")
                            
                            # Check if we're on a valid product page
                            if "Page Not Found" in title or "Error" in title:
                                print(f"Invalid product page: {url}")
                                continue
                            
                            # Additional validation - check for product title element
                            title_elem = page.locator("h1.x-item-title__mainTitle, h1[itemprop='name']")
                            if await title_elem.count() == 0:
                                print(f"No product title found on page: {url}")
                                continue
                                
                            break
                        except Exception as e:
                            if attempt == max_retries - 1:
                                print(f"Failed to load product page after {max_retries} attempts: {url}")
                                continue
                            print(f"Attempt {attempt + 1} failed for {url}, retrying...")
                            await asyncio.sleep(2)
                    
                    # Get product details
                    title = "N/A"
                    try:
                        title_elem = page.locator("h1.x-item-title__mainTitle, h1[itemprop='name']")
                        if await title_elem.count() > 0:
                            title = await title_elem.first.inner_text()
                    except Exception as e:
                        print(f"Error getting title: {e}")
                    
                    # Get brand
                    brand = "N/A"
                    try:
                        brand_elem = page.locator("span.ux-textspans--BOLD")
                        if await brand_elem.count() > 0:
                            brand = await brand_elem.first.inner_text()
                        else:
                            # Try in item specifics
                            brand_elem2 = page.locator("span.ux-textspans.ux-textspans--BOLD")
                            if await brand_elem2.count() > 0:
                                brand = await brand_elem2.first.inner_text()
                    except Exception as e:
                        print(f"Error getting brand: {e}")
                    
                    # Get price
                    price = "N/A"
                    try:
                        price_elem = page.locator("[data-testid='x-price-primary'] span.ux-textspans")
                        if await price_elem.count() > 0:
                            price = await price_elem.first.inner_text()
                    except Exception as e:
                        print(f"Error getting price: {e}")
                    
                    # Get seller rating
                    seller_rating = "N/A"
                    try:
                        # Get seller rating from the store information highlights
                        rating_elem = page.locator("h4.x-store-information__highlights span.ux-textspans")
                        if await rating_elem.count() > 0:
                            rating_text = await rating_elem.first.inner_text()
                            if rating_text:
                                # Extract numeric rating (e.g., "98.5% positive feedback" -> "98.5")
                                rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                                if rating_match:
                                    seller_rating = rating_match.group(1)
                                    print(f"Found seller rating: {seller_rating}%")
                    except Exception as e:
                        print(f"Error getting seller rating: {e}")
                    
                    # Get product specifications
                    specifications = {}
                    try:
                        # Wait for specifications section to load
                        await page.wait_for_selector("div.ux-layout-section-module-evo", timeout=10000)
                        
                        # Get all specification rows
                        spec_rows = await page.locator("dl.ux-labels-values").all()
                        
                        for row in spec_rows:
                            try:
                                # Get specification name and value
                                name_elem = row.locator("dt.ux-labels-values__labels span.ux-textspans")
                                value_elem = row.locator("dd.ux-labels-values__values span.ux-textspans")
                                
                                if await name_elem.count() > 0 and await value_elem.count() > 0:
                                    name = await name_elem.first.inner_text()
                                    value = await value_elem.first.inner_text()
                                    
                                    if name and value:
                                        # Clean up the name and value
                                        name = name.strip()
                                        value = value.strip()
                                        
                                        # Add to specifications dictionary
                                        specifications[name] = value
                                        print(f"Found specification: {name} = {value}")
                            except Exception as e:
                                print(f"Error processing specification row: {e}")
                                continue
                    except Exception as e:
                        print(f"Error getting specifications: {e}")
                    
                    # Get product reviews from the detail page
                    reviews = []
                    print("Collecting product reviews from product detail page...")
                    
                    try:
                        # First try to find and click the "See all feedback" button
                        feedback_button = page.locator("a.fdbk-detail-list__btn-container__btn").first
                        if await feedback_button.count() > 0:
                            print("Found 'See all feedback' button, clicking it...")
                            # Get the href attribute
                            href = await feedback_button.get_attribute("href")
                            if href:
                                print(f"Opening feedback page: {href}")
                                # Open the feedback page in a new tab
                                feedback_page = await context.new_page()
                                try:
                                    await feedback_page.goto(href, wait_until='networkidle')
                                    await asyncio.sleep(3)  # Wait for the feedback page to load
                                    
                                    # Get reviews from feedback page
                                    review_elements = await feedback_page.locator("div.fdbk-container__details__comment span").all()
                                    for element in review_elements:
                                        try:
                                            text = await element.inner_text()
                                            if text and text.strip() and len(text.strip()) > 10:
                                                reviews.append(text.strip())
                                        except Exception as e:
                                            print(f"Error extracting review text: {e}")
                                            continue
                                    
                                except Exception as e:
                                    print(f"Error loading feedback page: {e}")
                                finally:
                                    await feedback_page.close()
                        else:
                            print("No 'See all feedback' button found, trying to collect reviews from product page...")
                            # Try to get reviews directly from product page
                            review_elements = await page.locator("div.fdbk-container__details__comment span").all()
                            for element in review_elements:
                                try:
                                    text = await element.inner_text()
                                    if text and text.strip() and len(text.strip()) > 10:
                                        reviews.append(text.strip())
                                except Exception as e:
                                    print(f"Error extracting review text: {e}")
                                    continue
                    
                    except Exception as e:
                        print(f"Error collecting reviews: {str(e)}")
                    
                    print(f"\nCollected {len(reviews)} reviews in total")

                    # Store product data
                    product_data = {
                        'url': url,
                        'title': title.strip() if title else "N/A",
                        'brand': brand.strip() if brand else "N/A",
                        'price': price.strip() if price else "N/A",
                        'seller_rating': seller_rating,
                        'reviews': reviews,
                        'specifications': specifications  # Add specifications to the product data
                    }
                    all_products_data.append(product_data)
                    print(f"Completed processing product {index}")
                except Exception as e:
                    print(f"Error processing product {index}: {e}")
                    continue
                await asyncio.sleep(2)
            return all_products_data
        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            await browser.close()

def save_to_csv(products_data, search_query):
    if not products_data:
        return
        
    search_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create product details list
    products_list = []
    reviews_list = []
    
    for idx, product_data in enumerate(products_data, 1):
        # Extract product name from title
        title = product_data['title']
        # Try to extract product name before any delimiter
        if ' - ' in title:
            product_name = title.split(' - ')[0].strip()
        elif ',' in title:
            product_name = title.split(',')[0].strip()
        elif '|' in title:
            product_name = title.split('|')[0].strip()
        else:
            # If no delimiter found, use the first few words (up to 8)
            words = title.split()
            product_name = ' '.join(words[:min(8, len(words))])

        # Add product details
        product_info = {
            'product_index': idx,
            'search_query': search_query,
            'search_date': search_date,
            'product_name': product_name,
            'full_title': title,
            'brand': product_data['brand'],
            'price': product_data['price'],
            'seller_rating': product_data['seller_rating'],
            'total_reviews_found': len(product_data['reviews']),
            'url': product_data['url']
        }
        products_list.append(product_info)
        
        # Add reviews with reference to product
        for review_idx, review in enumerate(product_data['reviews'], 1):
            review_info = {
                'product_index': idx,
                'product_name': product_name,
                'review_index': review_idx,
                'review_text': review,
                'search_date': search_date
            }
            reviews_list.append(review_info)
    
    return {"products_list": products_list, "reviews_list": reviews_list}

# Run the script
if __name__ == "__main__":
    # Delete previous CSV files
    delete_previous_csv_files()
    
    product_name = input("Enter product name to search: ").strip()
    if not product_name:
        print("Please enter a product name to search.")
        exit()
    
    while True:
        try:
            num_products = int(input("How many products to scrape (1-20)? "))
            if 1 <= num_products <= 20:
                break
            print("Please enter a number between 1 and 20.")
        except ValueError:
            print("Please enter a valid number.")
    
    print(f"\nStarting search for top {num_products} products...")
    print("Note: Using random delays between requests to avoid detection...")
    
    # Modify the max products in product_urls list
    max_products = num_products
    
    results = asyncio.run(scrape_product_ebay(product_name, max_products))
    if results:
        print(f"\nSuccessfully collected data for {len(results)} products")
        save_to_csv(results, product_name)
        print("\nData collection and saving complete!")
    else:
        print("\nNo data was collected. Please try again.")