import requests
import csv
import time
import random
import os
from bs4 import BeautifulSoup
from urllib.parse import quote

def search_for_exam_question(question_number, topic_number=1, exam_type="professional-data-engineer"):
    """
    Search for a specific exam question using Google search
    
    Args:
        question_number: Question number to search for
        topic_number: Topic number (default: 1)
        exam_type: Type of exam (default: professional-data-engineer)
        
    Returns:
        str: URL of the first search result, or None if not found
    """
    # Construct the search query
    query = f"examtopics google cloud platform {exam_type} topic {topic_number} question {question_number}"
    encoded_query = quote(query)
    
    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/'
    }
    
    # Search URL
    search_url = f"https://www.google.com/search?q={encoded_query}"
    print(f"  Search URL: {search_url}")
    
    try:
        # Make the HTTP request
        print(f"  Sending request to Google...")
        response = requests.get(search_url, headers=headers)
        
        # Check response status
        print(f"  Response status code: {response.status_code}")
        response.raise_for_status()
        
        # Parse the HTML content
        print(f"  Parsing HTML content...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: Save the HTML for debugging
        debug_dir = "debug"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        with open(f"{debug_dir}/google_search_q{question_number}.html", 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"  Saved HTML to {debug_dir}/google_search_q{question_number}.html")
        
        # Try multiple selector patterns to find search results
        print(f"  Looking for search results with different CSS selectors...")
        
        # First priority: Find examtopics.com links
        all_selector_patterns = [
            '.g .yuRUbf a',           # Common pattern in 2021-2022
            '.rc .r a',               # Older pattern
            '.tF2Cxc .yuRUbf a',      # Another pattern
            '.g a',                   # More generic pattern
            'div.g div > a',          # Very generic pattern
            'a[href*="examtopics.com"]' # Direct search for examtopics links
        ]
        
        examtopics_url = None
        first_url = None
        
        # Try each selector pattern
        for pattern in all_selector_patterns:
            print(f"    Trying selector: {pattern}")
            search_results = soup.select(pattern)
            print(f"    Found {len(search_results)} results with this selector")
            
            if search_results:
                # Found some results with this selector
                for idx, result in enumerate(search_results):
                    url = result.get('href')
                    
                    if not url:
                        continue
                        
                    print(f"      Result #{idx+1}: {url}")
                    
                    # Save the first URL we encounter, regardless of domain
                    if first_url is None:
                        first_url = url
                        print(f"      ℹ️ Saved as first URL: {url}")
                    
                    # Check if the URL is from examtopics
                    if 'examtopics.com' in url:
                        print(f"      ✓ Found ExamTopics URL: {url}")
                        examtopics_url = url
                        # Prefer examtopics URLs, so return immediately
                        return examtopics_url
                
                print(f"    ✗ No ExamTopics URLs found with this selector")
            else:
                print(f"    ✗ No results found with this selector")
        
        # Alternative: try direct search for any link containing examtopics
        print(f"  Trying direct search for any examtopics links...")
        all_links = soup.find_all('a', href=lambda href: href and 'examtopics.com' in href)
        
        if all_links:
            print(f"  Found {len(all_links)} direct examtopics links")
            for idx, link in enumerate(all_links):
                url = link.get('href')
                print(f"    Direct link #{idx+1}: {url}")
                return url
        else:
            print(f"  ✗ No direct examtopics links found")
        
        # Try broader approach: find any link
        if first_url is None:
            print("  Trying to find any link on the page...")
            all_possible_links = soup.find_all('a', href=lambda href: href and (href.startswith('http') or href.startswith('/')))
            
            if all_possible_links:
                for idx, link in enumerate(all_possible_links[:5]):  # Only check first few
                    url = link.get('href')
                    if url and (url.startswith('http') or url.startswith('/')):
                        print(f"    Found general link #{idx+1}: {url}")
                        if idx == 0:  # Just use the very first link
                            first_url = url
                            print(f"    ⚠️ Using first general link as fallback: {first_url}")
                            break
        
        # Check if we're being blocked (CAPTCHA or other anti-bot measures)
        if "captcha" in response.text.lower() or "unusual traffic" in response.text.lower():
            print(f"  ⚠️ WARNING: Possible CAPTCHA or anti-bot measures detected!")
        
        # Return the first URL if an examtopics URL wasn't found
        if first_url:
            print(f"  ℹ️ No ExamTopics URL found. Using first search result: {first_url}")
            return first_url
            
        # If no URL found at all
        print(f"  ✗ No URLs found after trying all methods")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️ Network error searching for question {question_number}: {e}")
        return None
    except Exception as e:
        print(f"  ⚠️ Error parsing search results for question {question_number}: {e}")
        return None

def scrape_urls(start_question=1, end_question=300, topic_number=1, 
                exam_type="professional-data-engineer", output_file="exam_urls.csv"):
    """
    Scrape URLs for a range of exam questions
    
    Args:
        start_question: First question number to search for
        end_question: Last question number to search for
        topic_number: Topic number
        exam_type: Type of exam
        output_file: CSV file to save the URLs
    """
    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Check if we should continue from a previous run
    if os.path.exists(output_file):
        print(f"Found existing file {output_file}")
        resume = input("Do you want to resume from where you left off? (y/n): ").lower()
        
        if resume == 'y':
            # Read existing data
            existing_data = {}
            with open(output_file, 'r') as csvfile:
                csvreader = csv.reader(csvfile)
                next(csvreader)  # Skip header
                for row in csvreader:
                    if len(row) >= 2:
                        existing_data[int(row[0])] = row[1]
            
            # Determine the next question to start from
            processed_questions = [int(q) for q in existing_data.keys()]
            if processed_questions:
                start_question = max(processed_questions) + 1
                print(f"Resuming from question {start_question}")
                
                # Open file in append mode
                mode = 'a'
                write_header = False
        else:
            print("Starting a new scraping session...")
            mode = 'w'
            write_header = True
    else:
        print("Starting a new scraping session...")
        mode = 'w'
        write_header = True
    
    # Open CSV file for writing
    with open(output_file, mode, newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        if write_header:
            csvwriter.writerow(['question_number', 'url', 'is_examtopics'])
        
        # Track progress
        successful = 0
        failed = 0
        examtopics_count = 0
        
        try:
            # Scrape URLs for each question
            for question_number in range(start_question, end_question + 1):
                print(f"\n======= Question {question_number} =======")
                
                url = search_for_exam_question(question_number, topic_number, exam_type)
                
                if url:
                    is_examtopics = 'examtopics.com' in url
                    csvwriter.writerow([question_number, url, is_examtopics])
                    successful += 1
                    
                    if is_examtopics:
                        examtopics_count += 1
                        print(f"✅ Found ExamTopics URL for question {question_number}: {url}")
                    else:
                        print(f"⚠️ Found non-ExamTopics URL for question {question_number}: {url}")
                else:
                    csvwriter.writerow([question_number, '', False])
                    failed += 1
                    print(f"❌ No URL found for question {question_number}")
                
                # Add a delay to avoid rate limiting
                if question_number < end_question:
                    delay = random.uniform(5.0, 10.0)  # Increased delay to avoid blocking
                    print(f"Waiting {delay:.2f} seconds before next request...\n")
                    time.sleep(delay)
        
        except KeyboardInterrupt:
            print("\n\nScraping interrupted by user!")
        finally:
            # Print summary
            total_processed = successful + failed
            success_rate = (successful / total_processed * 100) if total_processed > 0 else 0
            fail_rate = (failed / total_processed * 100) if total_processed > 0 else 0
            examtopics_rate = (examtopics_count / successful * 100) if successful > 0 else 0
            
            print(f"\nScraping session summary:")
            print(f"Questions processed: {total_processed}")
            print(f"Successfully found URLs: {successful} ({success_rate:.1f}%)")
            print(f"  - ExamTopics URLs: {examtopics_count} ({examtopics_rate:.1f}% of successful)")
            print(f"Failed to find URLs: {failed} ({fail_rate:.1f}%)")
            print(f"Results saved to: {output_file}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="ExamTopics URL Scraper")
    parser.add_argument("--start", type=int, default=1, help="Starting question number")
    parser.add_argument("--end", type=int, default=50, help="Ending question number")
    parser.add_argument("--topic", type=int, default=1, help="Topic number")
    parser.add_argument("--exam", type=str, default="professional-data-engineer", help="Exam type")
    parser.add_argument("--output", type=str, default="exam_urls.csv", help="Output CSV file")
    
    args = parser.parse_args()
    
    print("ExamTopics URL Scraper")
    print("======================")
    
    # Run the scraper
    scrape_urls(
        start_question=args.start, 
        end_question=args.end, 
        topic_number=args.topic, 
        exam_type=args.exam, 
        output_file=args.output
    )

if __name__ == "__main__":
    main()
