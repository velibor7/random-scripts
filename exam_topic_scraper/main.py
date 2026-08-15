import requests
from bs4 import BeautifulSoup
import time
import re
import json
import os
import random

def scrape_exam_topic(url):
    """
    Scrape data from ExamTopics URL
    
    Args:
        url: URL of the exam topic page
        
    Returns:
        dict: Contains question, answers, and discussion data
    """
    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Make the HTTP request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract question
        question_div = soup.find('div', class_='question-body')
        question_text = question_div.text.strip() if question_div else "Question not found"
        
        # Extract answer choices
        answers = []
        answer_divs = soup.find_all('div', class_='answer-choice-body')
        for answer in answer_divs:
            letter = answer.find('span', class_='alphabet').text.strip() if answer.find('span', class_='alphabet') else ""
            text = answer.text.replace(letter, '', 1).strip() if letter else answer.text.strip()
            answers.append({
                'letter': letter,
                'text': text
            })
        
        # Find correct answer (if available)
        correct_answer = None
        correct_div = soup.find('div', class_='correct-answer')
        if correct_div:
            correct_answer = correct_div.text.replace('Correct Answer:', '').strip()
            
        # Extract discussions - updated selectors for discussion elements
        discussions = []
        
        # Try multiple possible selectors for discussion comments
        discussion_divs = soup.select('.comments-container .comment') or \
                          soup.select('.discussion-container .comment') or \
                          soup.select('.comment-container .comment') or \
                          soup.select('.comments .comment-item') or \
                          soup.select('#discussion .comment')
        
        # If still no comments found, try looking for any elements containing discussion keywords
        if not discussion_divs:
            print("Using fallback method to find discussions...")
            # Look for any divs that might contain discussion comments
            potential_comments = soup.find_all(['div', 'article'], class_=lambda c: c and any(keyword in c for keyword in 
                                                                                         ['comment', 'discussion', 'reply', 'post']))
            discussion_divs = potential_comments
        
        print(f"Found {len(discussion_divs)} discussion elements")
        
        for disc in discussion_divs:
            # Try different patterns to extract author, date, content, and votes
            # For author
            author_elem = disc.select_one('.author-name, .username, .user-name, .commenter, .user')
            author = author_elem.text.strip() if author_elem else "Unknown"
            
            # For date
            date_elem = disc.select_one('.comment-date, .date, .timestamp, .time')
            date = date_elem.text.strip() if date_elem else ""
            
            # For content
            content_elem = disc.select_one('.comment-content, .content, .comment-text, .text')
            content = content_elem.text.strip() if content_elem else disc.text.strip()
            
            # For votes
            vote_elem = disc.select_one('.vote-count, .votes, .score, .rating')
            votes = vote_elem.text.strip() if vote_elem else "0"
            
            discussions.append({
                'author': author,
                'date': date,
                'content': content,
                'votes': votes
            })
            
        # Debug HTML content if no discussions found
        if not discussions:
            print("No discussions found. Saving HTML for debugging...")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Page HTML saved to debug_page.html")
        
        return {
            'question': question_text,
            'answers': answers,
            'correct_answer': correct_answer,
            'discussions': discussions
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the page: {e}")
        return None

def display_results(data):
    """
    Display the scraped data in a readable format
    """
    if not data:
        print("No data to display.")
        return
    
    print("\n" + "="*80)
    print("QUESTION:")
    print(data['question'])
    print("\n" + "-"*40)
    
    print("ANSWER CHOICES:")
    for answer in data['answers']:
        print(f"{answer['letter']}. {answer['text']}")
    
    if data['correct_answer']:
        print("\n" + "-"*40)
        print(f"CORRECT ANSWER: {data['correct_answer']}")
    
    print("\n" + "="*80)
    print(f"DISCUSSIONS ({len(data['discussions'])} comments):")
    
    for i, disc in enumerate(data['discussions'], 1):
        print(f"\n--- Comment #{i} ---")
        print(f"Author: {disc['author']} | Date: {disc['date']} | Votes: {disc['votes']}")
        print(f"{disc['content']}")

def extract_question_number(url):
    """
    Extract the question number from the URL
    
    Args:
        url: URL of the exam topic page
        
    Returns:
        str: Question number
    """
    # Using regex to find the question number pattern
    pattern = r'question-(\d+)'
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    else:
        # Try another pattern that might be in the URL
        pattern = r'/(\d+)-exam'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no pattern matches, return a default name
    return "unknown"

def format_data_as_text(data):
    """
    Format the scraped data as readable text
    
    Args:
        data: Dictionary containing the scraped data
        
    Returns:
        str: Formatted text representation of the data
    """
    if not data:
        return "No data available."
    
    text_output = []
    text_output.append("=" * 80)
    text_output.append("QUESTION:")
    text_output.append(data['question'])
    text_output.append("\n" + "-" * 40)
    
    text_output.append("ANSWER CHOICES:")
    for answer in data['answers']:
        text_output.append(f"{answer['letter']}. {answer['text']}")
    
    if data['correct_answer']:
        text_output.append("\n" + "-" * 40)
        text_output.append(f"CORRECT ANSWER: {data['correct_answer']}")
    
    text_output.append("\n" + "=" * 80)
    text_output.append(f"DISCUSSIONS ({len(data['discussions'])} comments):")
    
    for i, disc in enumerate(data['discussions'], 1):
        text_output.append(f"\n--- Comment #{i} ---")
        text_output.append(f"Author: {disc['author']} | Date: {disc['date']} | Votes: {disc['votes']}")
        text_output.append(f"{disc['content']}")
    
    return "\n".join(text_output)

def save_discussions_to_separate_files(discussions, question_number):
    """
    Save each discussion comment to a separate file
    
    Args:
        discussions: List of discussion dictionaries
        question_number: Question number to use in the filename
    """
    # Create directories if they don't exist
    output_dir = os.path.join("questions", f"question_{question_number}_discussions")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save each discussion to a separate file
    for i, disc in enumerate(discussions, 1):
        # Format the discussion text
        discussion_text = []
        discussion_text.append(f"COMMENT #{i} FOR QUESTION {question_number}")
        discussion_text.append("=" * 60)
        discussion_text.append(f"Author: {disc['author']}")
        discussion_text.append(f"Date: {disc['date']}")
        discussion_text.append(f"Votes: {disc['votes']}")
        discussion_text.append("-" * 40)
        discussion_text.append(disc['content'])
        discussion_text.append("=" * 60)
        
        # Save to file
        filename = os.path.join(output_dir, f"comment_{i}.txt")
        with open(filename, 'w') as f:
            f.write("\n".join(discussion_text))
    
    # Create an index file with all comments
    index_filename = os.path.join(output_dir, "all_comments.txt")
    all_discussions = []
    all_discussions.append(f"ALL COMMENTS FOR QUESTION {question_number}")
    all_discussions.append("=" * 60)
    
    for i, disc in enumerate(discussions, 1):
        all_discussions.append(f"\nCOMMENT #{i}")
        all_discussions.append("-" * 40)
        all_discussions.append(f"Author: {disc['author']} | Date: {disc['date']} | Votes: {disc['votes']}")
        all_discussions.append(disc['content'])
    
    with open(index_filename, 'w') as f:
        f.write("\n".join(all_discussions))
    
    print(f"  - {len(discussions)} individual comments saved to: {output_dir}")
    print(f"  - Combined comments file: {index_filename}")

def save_to_file(data, question_number):
    """
    Save the scraped data to JSON and TXT files
    
    Args:
        data: Dictionary containing the scraped data
        question_number: Question number to use in the filename
    """
    # Create directory if it doesn't exist
    output_dir = "questions"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save as JSON
    json_filename = os.path.join(output_dir, f"question_{question_number}.json")
    with open(json_filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Save as TXT
    txt_filename = os.path.join(output_dir, f"question_{question_number}.txt")
    formatted_text = format_data_as_text(data)
    with open(txt_filename, 'w') as f:
        f.write(formatted_text)
    
    print(f"\nQuestion data saved to:")
    print(f"  - JSON: {json_filename}")
    print(f"  - TXT: {txt_filename}")
    
    # Save discussions to separate files if there are any
    if data and 'discussions' in data and data['discussions']:
        save_discussions_to_separate_files(data['discussions'], question_number)

def process_url_from_csv(url, question_number):
    """
    Process a single URL from the CSV file
    
    Args:
        url: URL to scrape
        question_number: Question number
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nProcessing Question #{question_number}")
    print(f"URL: {url}")
    
    if not url.strip():
        print(f"Skipping question {question_number} - No URL available")
        return False
    
    try:
        # Scrape the data
        data = scrape_exam_topic(url)
        
        if data:
            # Display the results
            print(f"\nFound {len(data['discussions'])} discussion comments")
            display_results(data)
            
            # Save data to file
            save_to_file(data, question_number)
            return True
        else:
            print(f"Failed to scrape data for question {question_number}")
            return False
            
    except Exception as e:
        print(f"Error processing question {question_number}: {e}")
        return False

def add_backoff_delay():
    """
    Adds a random delay between 2 and 8 seconds to avoid rate limiting
    """
    delay = random.uniform(2.0, 8.0)
    print(f"\nAdding backoff delay of {delay:.2f} seconds before next request...")
    time.sleep(delay)
    return delay

def process_all_urls_from_csv(csv_file="urls_manual.csv", start_row=None, end_row=None):
    """
    Process URLs from a CSV file within a specified row range
    
    Args:
        csv_file: CSV file containing URLs
        start_row: First row to process (1-indexed, inclusive)
        end_row: Last row to process (1-indexed, inclusive)
    """
    import csv
    
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found")
        return
    
    # Stats tracking
    total = 0
    successful = 0
    failed = 0
    total_delay = 0
    
    # First, count total rows to validate range and for reporting
    with open(csv_file, 'r') as file:
        total_rows = sum(1 for _ in csv.reader(file)) - 1  # Subtract 1 for header
    
    print(f"CSV file contains {total_rows} data rows")
    
    # Validate and adjust row range
    if start_row is None or start_row < 1:
        start_row = 1
    if end_row is None or end_row > total_rows:
        end_row = total_rows
    
    # Ensure valid range
    if start_row > end_row:
        print(f"Error: Invalid row range ({start_row} > {end_row})")
        return
    
    print(f"Processing rows {start_row} to {end_row} (of {total_rows} total rows)")
    
    # Debug: print CSV file contents to verify structure
    print(f"Debug: CSV file structure check:")
    with open(csv_file, 'r') as file:
        all_rows = list(csv.reader(file))
        sample_rows = all_rows[:min(5, len(all_rows))]
        for i, row in enumerate(sample_rows):
            print(f"  Row {i}: {row}")
    
    # Process each URL in the CSV file
    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_reader = list(csv.reader(file))  # Read all rows into memory
        header = csv_reader[0]  # Get header row
        
        print(f"Debug: CSV header: {header}")
        
        # Process data rows
        for row_idx in range(start_row, min(end_row + 1, len(csv_reader))):
            row = csv_reader[row_idx]
            
            # Determine URL based on CSV format
            url = None
            question_number = None
            
            if len(row) >= 2:  # If the CSV has at least two columns (question_number, url)
                question_number = row[0]
                url = row[1]
            elif len(row) == 1:  # If the CSV only has one column (url only)
                url = row[0]
                # Extract question number from URL
                question_number = extract_question_number(url)
                print(f"Extracted question number from URL: {question_number}")
            else:  # Empty row
                print(f"Warning: Row {row_idx} is empty")
                continue
            
            if not url or not url.strip():
                print(f"Warning: Row {row_idx} has no URL")
                continue
                
            total += 1
            print(f"\n--- Processing row {row_idx}/{end_row} ({row_idx-start_row+1} of {end_row-start_row+1} selected) ---")
            print(f"Debug: URL: {url}")
            
            # Add a backoff delay to avoid rate limiting, but skip the first request
            if total > 1:
                delay = add_backoff_delay()
                total_delay += delay
            
            if process_url_from_csv(url, question_number):
                successful += 1
            else:
                failed += 1
    
    # Print summary
    print("\n" + "="*50)
    print("Processing Summary")
    print("="*50)
    print(f"Rows processed: {total} (from {start_row} to {end_row})")
    
    # Calculate percentages safely
    success_percentage = (successful/total*100) if total > 0 else 0
    failed_percentage = (failed/total*100) if total > 0 else 0
    
    print(f"Successfully processed: {successful} ({success_percentage:.1f}%)")
    print(f"Failed to process: {failed} ({failed_percentage:.1f}%)")
    print(f"Total backoff delay: {total_delay:.2f} seconds ({total_delay/60:.2f} minutes)")

def main():
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Scrape exam topics from ExamTopics website')
    parser.add_argument('--url', help='URL to scrape a single question')
    parser.add_argument('--csv', help='CSV file containing URLs to scrape', default='urls_manual.csv')
    parser.add_argument('--batch', action='store_true', help='Process all URLs from CSV file')
    parser.add_argument('--start-row', type=int, help='First row to process from CSV file (1-indexed)')
    parser.add_argument('--end-row', type=int, help='Last row to process from CSV file (1-indexed)')
    parser.add_argument('--no-backoff', action='store_true', help='Disable backoff delay between requests')
    
    args = parser.parse_args()
    
    # Override backoff behavior if requested
    global add_backoff_delay
    if args.no_backoff:
        print("Warning: Backoff delay disabled. This may increase the risk of being rate-limited.")
        add_backoff_delay = lambda: 0
    
    if args.batch or args.start_row or args.end_row:
        # Process URLs from CSV file with optional row range
        process_all_urls_from_csv(args.csv, args.start_row, args.end_row)
    elif args.url:
        # Process a single URL
        url = args.url
        print(f"Scraping data from: {url}")
        
        # Extract question number from URL
        question_number = extract_question_number(url)
        print(f"Detected question number: {question_number}")
        
        data = scrape_exam_topic(url)
        
        if data:
            # Add debug information about discussions
            print(f"\nFound {len(data['discussions'])} discussion comments")
            
            # Display the results
            display_results(data)
            
            # Save data to file
            save_to_file(data, question_number)
        else:
            print("No data was scraped. Please check the URL or website structure.")
    else:
        # No arguments provided - show help and exit
        parser.print_help()
        print("\nPlease specify an action: --batch to process a CSV file or --url to process a single URL.")
        print("Example: python main.py --batch --csv urls_manual.csv --start-row 1 --end-row 10")

if __name__ == "__main__":
    main()
