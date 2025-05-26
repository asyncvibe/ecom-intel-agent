import asyncio
from playwright.async_api import async_playwright
from googletrans import Translator
import pandas as pd
from datetime import datetime
import re
import random
from time import sleep
import os
import glob

def cleanup_old_files():
    """Clean up old CSV files and screenshots from previous runs"""
    print("\nCleaning up old files...")
    
    # Define patterns for files to clean
    patterns = [
        'flipkart_products_summary_*.csv',
        'flipkart_products_reviews_*.csv',
        'screenshot.png',
        'price_debug*.png'
    ]
    
    total_removed = 0
    for pattern in patterns:
        try:
            files = glob.glob(pattern)
            for file in files:
                try:
                    os.remove(file)
                    total_removed += 1
                    print(f"Removed: {file}")
                except Exception as e:
                    print(f"Could not remove {file}: {e}")
        except Exception as e:
            print(f"Error while searching for {pattern}: {e}")
    
    print(f"Cleanup complete. Removed {total_removed} files.\n")

async def scrape_product_flipkart(product_name, max_products=1):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        translator = Translator()
        all_products_data = []
        
        try:
            # Navigate directly to search results
            print(f"Searching for {product_name}...")
            search_url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '+')}"
            print(f"Navigating to: {search_url}")
            
            await page.goto(search_url, timeout=60000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(3)  # Let the page settle
            
            # Take a screenshot for debugging if needed
            # await page.screenshot(path="screenshot.png")
            # print("Saved screenshot to screenshot.png for debugging")
            
            # Get multiple product links
            print("Looking for product links...")
            product_urls = []
            # Close login popup if present
            try:
                close_btn = page.locator("button._2KpZ6l._2doB4z")
                if await close_btn.count() > 0:
                    await close_btn.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

            # Try to get all product links from the search result page
            # 1. Try for grid view (most electronics)
            grid_links = await page.locator("a._1fQZEK").all()
            print(f"Found {len(grid_links)} grid view product links")
            for link in grid_links:
                if len(product_urls) >= max_products:
                    break
                href = await link.get_attribute("href")
                if href:
                    full_url = f"https://www.flipkart.com{href}" if not href.startswith('http') else href
                    if full_url not in product_urls:
                        product_urls.append(full_url)
                        print(f"Found product URL ({len(product_urls)} of {max_products}): {full_url}")
                        await asyncio.sleep(random.uniform(0.5, 1.5))

            # 2. Try for list view (fashion, some other categories)
            if len(product_urls) < max_products:
                list_links = await page.locator("a.s1Q9rs").all()
                print(f"Found {len(list_links)} list view product links")
                for link in list_links:
                    if len(product_urls) >= max_products:
                        break
                    href = await link.get_attribute("href")
                    if href:
                        full_url = f"https://www.flipkart.com{href}" if not href.startswith('http') else href
                        if full_url not in product_urls:
                            product_urls.append(full_url)
                            print(f"Found product URL ({len(product_urls)} of {max_products}): {full_url}")
                            await asyncio.sleep(random.uniform(0.5, 1.5))

            # 3. Fallback: any anchor with /p/ in href
            if len(product_urls) < max_products:
                all_links = await page.locator("a[href*='/p/']").all()
                print(f"Found {len(all_links)} fallback product links")
                for link in all_links:
                    if len(product_urls) >= max_products:
                        break
                    href = await link.get_attribute("href")
                    if href:
                        full_url = f"https://www.flipkart.com{href}" if not href.startswith('http') else href
                        if full_url not in product_urls:
                            product_urls.append(full_url)
                            print(f"Found product URL ({len(product_urls)} of {max_products}): {full_url}")
                            await asyncio.sleep(random.uniform(0.5, 1.5))

            if not product_urls:
                print("Could not find any products matching your search.")
                return None
            
            # Process each product
            for index, url in enumerate(product_urls, 1):
                print(f"\nProcessing product {index} of {len(product_urls)}...")
                
                try:
                    # Random delay between products (3-7 seconds)
                    delay = random.uniform(3, 7)
                    print(f"Waiting for {delay:.1f} seconds before processing next product...")
                    await asyncio.sleep(delay)
                    
                    await page.goto(url, timeout=60000)
                    await page.wait_for_load_state("domcontentloaded")
                    # Random delay after page load (2-5 seconds)
                    await asyncio.sleep(random.uniform(2, 5))
                    

                    # Wait for product details to load
                    print("\nExtracting product details...")
                    
                    # More robust waiting strategy
                    try:
                        # Wait for various key product elements
                        await asyncio.gather(
                            page.wait_for_selector("._1YokD2._3Mn1Gg", timeout=10000),
                            page.wait_for_selector("._1AtVbE.col-12-12", timeout=10000),
                            page.wait_for_selector("._30jeq3._16Jk6d", timeout=10000)
                        )
                    except Exception as e:
                        print(f"Warning: Not all elements loaded immediately: {e}")
                        # Add extra wait time for dynamic content
                        await asyncio.sleep(5)
                    
                    # Take a debug screenshot
                    # await page.screenshot(path="price_debug.png")
                    
                    # Get product details
                    title = "N/A"
                    try:
                        title_selectors = [
                            "span.B_NuCI",
                            "._4rR01T",
                            ".yhB1nd",
                            "h1",
                            "._29OxBi h1"
                        ]
                        for selector in title_selectors:
                            try:
                                element = page.locator(selector).first
                                if await element.is_visible():
                                    text = await element.inner_text()
                                    if text and len(text.strip()) > 3:
                                        title = text.strip()
                                        print(f"[DEBUG] Found title with selector {selector}: {title}")
                                        break
                            except Exception:
                                continue
                    except Exception as e:
                        print(f"Error getting title: {e}")

                    # Get product specifications
                    specifications = {}
                    try:
                        # Wait for specifications section to load
                        await page.wait_for_selector("div._3Fm-hO", timeout=10000)
                        
                        # Get all specification rows directly
                        spec_rows = await page.locator("tr.WJdYP6").all()
                        
                        for row in spec_rows:
                            try:
                                # Get specification name and value with escaped selectors
                                name_elem = row.locator("td[class*='+fFi1w']")
                                value_elem = row.locator("td.Izz52n li.HPETK2")
                                
                                if await name_elem.count() > 0 and await value_elem.count() > 0:
                                    name = await name_elem.inner_text()
                                    value = await value_elem.inner_text()
                                    
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

                    # Price extraction with updated selectors
                    price = "N/A"
                    try:
                        price_selectors = [
                            "div.hl05eU div.Nx9bqj.CxhGGd",  # Current price
                            "div._30jeq3._16Jk6d",  # Fallback price selector
                            "div[class*='_30jeq3']"
                        ]
                        for selector in price_selectors:
                            try:
                                element = page.locator(selector).first
                                if await element.is_visible():
                                    text = await element.inner_text()
                                    if text and '₹' in text:
                                        price = text.strip().replace('₹', '').replace(',', '').strip()
                                        print(f"[DEBUG] Found price with selector {selector}: {price}")
                                        break
                            except Exception:
                                continue
                    except Exception as e:
                        print(f"Error getting price: {e}")

                    # Rating extraction with updated selectors
                    rating = "N/A"
                    try:
                        rating_selectors = [
                            "div.XQDdHH",  # New rating selector
                            "._3LWZlK",    # Fallback rating selector
                            "div[class*='rating'] span"
                        ]
                        for selector in rating_selectors:
                            try:
                                element = page.locator(selector).first
                                if await element.is_visible():
                                    text = await element.inner_text()
                                    if text:
                                        # Extract just the number from the rating
                                        rating_match = re.search(r'(\d+(?:\.\d+)?)', text)
                                        if rating_match:
                                            rating = rating_match.group(1)
                                            print(f"[DEBUG] Found rating with selector {selector}: {rating}")
                                            break
                            except Exception:
                                continue
                    except Exception as e:
                        print(f"Error getting rating: {e}")

                    # Brand extraction with updated selectors
                    brand = "N/A"
                    try:
                        brand_selectors = [
                            "span.G6XhRU",  # Primary brand selector
                            "._2J4LW6",     # Alternative brand selector
                            "a._1fGeJ5.PP89tw",  # Another brand location
                            "span[class*='brand']"  # Generic brand class
                        ]
                        for selector in brand_selectors:
                            try:
                                element = page.locator(selector).first
                                if await element.is_visible():
                                    text = await element.inner_text()
                                    if text and len(text.strip()) > 1:
                                        brand = text.strip()
                                        brand = re.sub(r'^(Brand|by|from)\s+', '', brand, flags=re.IGNORECASE)
                                        print(f"[DEBUG] Found brand with selector {selector}: {brand}")
                                        break
                            except Exception:
                                continue
                    except Exception as e:
                        print(f"Error getting brand: {e}")

                    # Total reviews extraction with improved selectors
                    total_reviews = "N/A"
                    try:
                        review_count_selectors = [
                            "._2_R_DZ span",
                            "._3nUwsX span",
                            "span._2_R_DZ span",
                            "[class*='review-count']"
                        ]
                        for selector in review_count_selectors:
                            try:
                                element = page.locator(selector).first
                                if await element.is_visible():
                                    text = await element.inner_text()
                                    if text:
                                        # Try to extract review count using regex
                                        matches = re.search(r'([\d,]+).*reviews?', text, re.IGNORECASE)
                                        if matches:
                                            total_reviews = matches.group(1).replace(',', '')
                                            print(f"[DEBUG] Found total reviews with selector {selector}: {total_reviews}")
                                            break
                            except Exception:
                                continue
                    except Exception as e:
                        print(f"Error getting total reviews: {e}")

                    # Reviews collection with improved navigation and selectors
                    reviews = []
                    print("\nCollecting reviews...")
                    
                    try:
                        current_url = page.url
                        review_url = None
                        
                        # First try to find the review link on the product page
                        review_link_selectors = [
                            "a._1fQZEK[href*='product-reviews']",
                            "a._2_R_DZ[href*='product-reviews']",
                            "._3UAT2v a[href*='product-reviews']",
                            "a[href*='product-reviews']"
                        ]
                        
                        for selector in review_link_selectors:
                            try:
                                element = page.locator(selector).first
                                if await element.count() > 0:
                                    href = await element.get_attribute("href")
                                    if href:
                                        review_url = href if href.startswith('http') else f"https://www.flipkart.com{href}"
                                        print(f"Found review link: {review_url}")
                                        break
                            except Exception:
                                continue
                        
                        # If no review link found, try constructing the URL
                        if not review_url and '/p/' in current_url:
                            review_url = current_url.replace('/p/', '/product-reviews/')
                            if '?' in review_url:
                                review_url = review_url.split('?')[0]
                        
                        if review_url:
                            print(f"Navigating to reviews page: {review_url}")
                            await page.goto(review_url)
                            await page.wait_for_load_state("networkidle")
                            await asyncio.sleep(3)
                            
                            page_num = 1
                            max_pages = 10  # Limit to 10 pages to avoid infinite loops
                            
                            while len(reviews) < 100 and page_num <= max_pages:
                                print(f"\nProcessing reviews page {page_num}...")
                                
                                # Wait for reviews to load
                                try:
                                    await page.wait_for_selector("div.col.EPCmJX", timeout=10000)
                                except Exception as e:
                                    print(f"Warning: Reviews container not found: {e}")
                                    await asyncio.sleep(2)
                                
                                # Get all review elements
                                review_elements = await page.locator("div.col.EPCmJX").all()
                                print(f"Found {len(review_elements)} reviews on current page")
                                
                                # If no reviews found on current page, stop the collection
                                if len(review_elements) == 0:
                                    print("No reviews found on current page. Stopping review collection.")
                                    break
                                
                                reviews_found_on_page = 0
                                for element in review_elements:
                                    try:
                                        # Get review text - try multiple selectors
                                        review_text = None
                                        selectors = [
                                            "div._11pzQk",
                                            "div.t-ZTKy",
                                            "div[class*='review-text']",
                                            "div.row div._11pzQk",
                                            "div.row div.t-ZTKy",
                                            "div.row div[class*='review-text']"
                                        ]
                                        
                                        for selector in selectors:
                                            try:
                                                text_element = element.locator(selector).first
                                                if await text_element.count() > 0:
                                                    review_text = await text_element.inner_text()
                                                    print(f"DEBUG: Found text with selector {selector}: {review_text[:50]}...")
                                                    if review_text and len(review_text.strip()) > 5:
                                                        break
                                            except Exception as e:
                                                print(f"DEBUG: Error with selector {selector}: {str(e)}")
                                                continue
                                        
                                        if not review_text:
                                            # Try getting all text from the review element
                                            try:
                                                review_text = await element.inner_text()
                                                print(f"DEBUG: Got all text from element: {review_text[:50]}...")
                                            except Exception as e:
                                                print(f"DEBUG: Error getting all text: {str(e)}")
                                        
                                        if review_text and len(review_text.strip()) > 5:
                                            cleaned_review = review_text.strip()
                                            if cleaned_review not in reviews:
                                                reviews.append(cleaned_review)
                                                reviews_found_on_page += 1
                                                print(f"Found review #{len(reviews)}: {cleaned_review[:50]}...")
                                                
                                                if len(reviews) >= 100:
                                                    break
                                        else:
                                            print(f"DEBUG: Review text too short or empty: {review_text}")
                                    except Exception as e:
                                        print(f"Error extracting review text: {e}")
                                        continue
                                
                                print(f"Successfully extracted {reviews_found_on_page} reviews from page {page_num}")
                                
                                if len(reviews) >= 100:
                                    break
                                
                                # Try to navigate to next page
                                next_page_found = False
                                
                                # Try URL-based navigation first
                                if 'page=' in page.url:
                                    next_url = re.sub(r'page=\d+', f'page={page_num + 1}', page.url)
                                    if next_url != page.url:
                                        await page.goto(next_url)
                                        await page.wait_for_load_state("networkidle")
                                        await asyncio.sleep(2)
                                        next_page_found = True
                                
                                # If URL navigation didn't work, try clicking next button
                                if not next_page_found:
                                    next_button = page.locator("a._9QVEpD").first
                                    if await next_button.count() > 0:
                                        await next_button.click()
                                        await page.wait_for_load_state("networkidle")
                                        await asyncio.sleep(2)
                                        next_page_found = True
                                
                                if next_page_found:
                                    page_num += 1
                                else:
                                    print("No more review pages available")
                                    break
                                    
                        else:
                            print("Could not find or construct review page URL")
                    
                    except Exception as e:
                        print(f"Error in review collection: {e}")
                    
                    print(f"\nCollected {len(reviews)} reviews in total")

                    # Store product data
                    product_data = {
                        'url': url,
                        'title': title.strip() if title else "N/A",
                        'brand': brand.strip() if brand else "N/A",
                        'price': price.strip() if price else "N/A",
                        'rating': rating.strip() if rating else "N/A",
                        'total_reviews_found': len(reviews) if reviews else 0,
                        'reviews': reviews,
                        'specifications': specifications  # Add specifications to the product data
                    }
                    all_products_data.append(product_data)
                    print(f"Completed processing product {index}")
                    
                except Exception as e:
                    print(f"Error processing product {index}: {e}")
                    continue
                
                # Add a delay between products
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
            'rating': product_data['rating'],
            'total_reviews_found': len(product_data['reviews']),
            'url': product_data['url'],
            'specifications': product_data['specifications']  # Add specifications to the output
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
    # Create DataFrames
    # products_df = pd.DataFrame(products_list)
    # reviews_df = pd.DataFrame(reviews_list)
    
    # # Save summary to CSV
    # summary_file = f'flipkart_products_summary_{timestamp}.csv'
    # products_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    
    # # Save reviews to CSV
    # reviews_file = f'flipkart_products_reviews_{timestamp}.csv'
    # reviews_df.to_csv(reviews_file, index=False, encoding='utf-8-sig')
    
    # print(f"\nFiles saved:")
    # print(f"1. Summary: {summary_file}")
    # print(f"   - Contains {len(products_list)} products")
    # print(f"2. Reviews: {reviews_file}")
    # print(f"   - Contains {len(reviews_list)} reviews")
    
    # Print summary of the scraping
    # print("\nScraping Summary:")
    # print(f"Search Query: {search_query}")
    # print(f"Search Date: {search_date}")
    # print(f"Products Found: {len(products_list)}")
    # print(f"Total Reviews Collected: {len(reviews_list)}")
    # print(f"Average Reviews per Product: {len(reviews_list)/len(products_list):.1f}")

# Run the script
# if __name__ == "__main__":
#     # Clean up old files before starting
#     cleanup_old_files()
    
#     product_name = input("Enter product name to search: ").strip()
#     if not product_name:
#         print("Please enter a product name to search.")
#         exit()
    
#     while True:
#         try:
#             num_products = int(input("How many products to scrape (1-20)? "))
#             if 1 <= num_products <= 20:
#                 break
#             print("Please enter a number between 1 and 20.")
#         except ValueError:
#             print("Please enter a valid number.")
    
#     print(f"\nStarting search for top {num_products} products...")
#     print("Note: Using random delays between requests to avoid detection...")
    
#     # Modify the max products in product_urls list
#     max_products = num_products
    
#     results = asyncio.run(scrape_product_details(product_name, max_products))
#     if results:
#         print(f"\nSuccessfully collected data for {len(results)} products")
#         save_to_csv(results, product_name)
#         print("\nData collection and saving complete!")
#     else:
#         print("\nNo data was collected. Please try again.")