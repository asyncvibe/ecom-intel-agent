import asyncio
from playwright.async_api import async_playwright
from googletrans import Translator
import pandas as pd
from datetime import datetime
import re
import random
from time import sleep

async def scrape_product_amazon(product_name, max_products=1):
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
            search_url = f"https://www.amazon.com/s?k={product_name.replace(' ', '+')}"
            print(f"Navigating to: {search_url}")
            
            await page.goto(search_url, timeout=60000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(3)  # Let the page settle
            
            # Take a screenshot for debugging if needed
            # await page.screenshot(path="screenshot.png")
            # print("Saved screenshot to screenshot.png for debugging")
            
            # Get multiple product links
            print("Looking for product links...")
            product_selectors = [
                "h2 a.a-link-normal",
                "div.s-result-item h2 a.a-link-normal",
                "div[data-component-type='s-search-result'] h2 a.a-link-normal",
                "h2 .a-link-normal[href*='/dp/']",
                ".s-result-item .a-link-normal[href*='/dp/']"
            ]
            
            product_urls = []
            for selector in product_selectors:
                if len(product_urls) >= max_products:
                    break
                    
                try:
                    print(f"Trying selector: {selector}")
                    product_links = await page.locator(selector).all()
                    
                    for link in product_links:
                        if len(product_urls) >= max_products:
                            break
                            
                        href = await link.get_attribute("href")
                        if href and ("/dp/" in href or "/gp/" in href):
                            url = f"https://www.amazon.com{href}" if not href.startswith("http") else href
                            if url not in product_urls:
                                product_urls.append(url)
                                print(f"Found product URL ({len(product_urls)} of {max_products}): {url}")
                                # Add a small random delay between finding products
                                await asyncio.sleep(random.uniform(0.5, 1.5))
                                
                except Exception as e:
                    print(f"Selector {selector} failed: {str(e)}")
                    continue
            
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
                    
                    # Get product details
                    title = "N/A"
                    try:
                        title_elem = page.locator("span#productTitle.a-size-large")
                        if await title_elem.count() > 0:
                            title = await title_elem.inner_text()
                        else:
                            title_input = page.locator("input#productTitle[type='hidden']")
                            if await title_input.count() > 0:
                                title = await title_input.get_attribute("value")
                    except Exception as e:
                        print(f"Error getting title: {e}")
                    
                    # Get brand
                    brand = "N/A"
                    brand_selectors = [
                        "#bylineInfo",
                        "#bylineInfo_feature_div .a-link-normal",
                        "#brand",
                        ".po-brand .a-span9"
                    ]
                    
                    for selector in brand_selectors:
                        try:
                            brand_elem = page.locator(selector).first
                            if await brand_elem.count() > 0:
                                brand_text = await brand_elem.inner_text()
                                if brand_text:
                                    brand = re.sub(r'^Visit the |^Brand: |^by |^From ', '', brand_text.strip())
                                    break
                        except Exception as e:
                            continue
                    
                    # Get price
                    price = "N/A"
                    try:
                        price_whole = page.locator(".a-price .a-price-whole").first
                        if await price_whole.count() > 0:
                            whole = await price_whole.inner_text()
                            try:
                                fraction = await page.locator(".a-price .a-price-fraction").first.inner_text()
                                price = f"${whole}{fraction}"
                            except:
                                price = f"${whole}"
                    except Exception as e:
                        print(f"Error getting price: {e}")
                    
                    # Get rating
                    rating = "N/A"
                    try:
                        # Try multiple selectors for rating
                        rating_selectors = [
                            "span.a-icon-alt",  # Main rating selector
                            "#acrPopover",      # Alternative rating location
                            "i.a-icon-star span.a-icon-alt",  # Another common location
                            "#averageCustomerReviews .a-icon-alt"  # Product page rating
                        ]
                        
                        for selector in rating_selectors:
                            rating_elem = page.locator(selector).first
                            if await rating_elem.count() > 0:
                                rating_text = await rating_elem.inner_text()
                                if rating_text and "out of 5" in rating_text.lower():
                                    rating = rating_text.split(" out")[0].strip()
                                    print(f"Found rating: {rating}")
                                    break
                                
                        if rating == "N/A":
                            print("Could not find rating")
                    except Exception as e:
                        print(f"Error getting rating: {e}")
                        pass
                    
                    # Get reviews
                    reviews = []
                    print("Collecting reviews...")
                    
                    review_selectors = [
                        "div[data-hook='review'] span[data-hook='review-body']",
                        "div.review-text-content span",
                        "#cm-cr-dp-review-list div.review-data span.review-text",
                        "div[data-hook='review-collapsed'] span"
                    ]
                    
                    for selector in review_selectors:
                        try:
                            review_elements = await page.locator(selector).all()
                            for elem in review_elements:
                                try:
                                    review_text = await elem.inner_text()
                                    if review_text:
                                        review_text = review_text.strip()
                                        if review_text:
                                            reviews.append(review_text)
                                except Exception as e:
                                    continue
                                    
                            if reviews:
                                break
                        except Exception as e:
                            continue
                    
                    # Get product specifications
                    specifications = {}
                    try:
                        # Wait for specifications table to load
                        await page.wait_for_selector("table#productDetails_detailBullets_sections1", timeout=10000)
                        
                        # Get all specification rows
                        spec_rows = await page.locator("table#productDetails_detailBullets_sections1 tr").all()
                        
                        for row in spec_rows:
                            try:
                                # Get the specification name (th) and value (td)
                                name_elem = row.locator("th.a-color-secondary")
                                value_elem = row.locator("td.a-size-base")
                                
                                if await name_elem.count() > 0 and await value_elem.count() > 0:
                                    name = await name_elem.inner_text()
                                    value = await value_elem.inner_text()
                                    
                                    if name and value:
                                        # Clean up the name and value
                                        name = name.strip().replace(':', '')
                                        value = value.strip()
                                        
                                        # Add to specifications dictionary
                                        specifications[name] = value
                                        print(f"Found specification: {name} = {value}")
                            except Exception as e:
                                print(f"Error processing specification row: {e}")
                                continue
                    except Exception as e:
                        print(f"Error getting specifications: {e}")

                    # Store product data
                    product_data = {
                        'url': url,
                        'title': title.strip() if title else "N/A",
                        'brand': brand.strip() if brand else "N/A",
                        'price': price.strip() if price else "N/A",
                        'rating': rating.strip() if rating else "N/A",
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
    # summary_file = f'amazon_products_summary_{timestamp}.csv'
    # products_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    
    # # Save reviews to CSV
    # reviews_file = f'amazon_products_reviews_{timestamp}.csv'
    # reviews_df.to_csv(reviews_file, index=False, encoding='utf-8-sig')
    
    # print(f"\nFiles saved:")
    # print(f"1. Summary: {summary_file}")
    # print(f"   - Contains {len(products_list)} products")
    # print(f"2. Reviews: {reviews_file}")
    # print(f"   - Contains {len(reviews_list)} reviews")
    
    # # Print summary of the scraping
    # print("\nScraping Summary:")
    # print(f"Search Query: {search_query}")
    # print(f"Search Date: {search_date}")
    # print(f"Products Found: {len(products_list)}")
    # print(f"Total Reviews Collected: {len(reviews_list)}")
    # print(f"Average Reviews per Product: {len(reviews_list)/len(products_list):.1f}")

# Run the script
# if __name__ == "__main__":
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