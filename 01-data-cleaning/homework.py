import argparse
import re
import requests
import json
from utils import  read_warc_file, retrieve_bad_words
from datasets import load_dataset
from typing import Set, Dict
# import html2text
import string
from bs4 import BeautifulSoup
import chardet
from warcio.archiveiterator import ArchiveIterator

PUNCTUATION = set(string.punctuation)
ALLOWED_CHARS = set(string.ascii_letters + string.digits + string.punctuation + string.whitespace)





def retrieve_bad_words() -> set[str]:
    """Helper function - that reads a list of bad words from a file and returns them as a set.
    Returns:
        Set[str]: A set containing lowercase bad words.
    """
    with open('./bad_word_list.txt', 'r') as file:
        records = file.read().strip().split('\n')
        bad_words = [record.lower() for record in records]
        return set(bad_words)

def html_to_text(html: str) -> str:
    """Converts HTML content to plain text..
    Args:
        html (bytes): HTML content as bytes.
    Returns:
        str: Plain text extracted from HTML.
    """
    # detected = chardet.detect(html)
    # encoding = detected.get("encoding") or "utf-8"
    # html_decoded = html.decode(encoding, errors="ignore")

    # soup = BeautifulSoup(html_decoded, "html.parser")
    # text = soup.get_text(separator="\n", strip=True)
    # return text

    MIN_LENGTH = 100                 # Minimum total characters
    MAX_SYMBOL_RATIO = 0.3           # Maximum symbol/code ratio
    TERMINAL_PUNCTUATION = (".", "!", "?", '"', "”", "’", "？", "。", "！")  # sentence endings
    MIN_WORDS_PER_LINE = 5           # Keep only lines with ≥5 words
    MIN_CHARS_PER_LINE = 8
    MIN_SENTENCES_PER_DOC = 3        # Discard docs with <3 sentences

    # 1. Detect encoding
    detected = chardet.detect(html)
    encoding = detected.get("encoding") or "utf-8"

    # 2. Decode into string
    html_decoded = html.decode(encoding, errors="ignore")

    # 3. Parse HTML
    soup = BeautifulSoup(html_decoded, "html.parser")

    # 4. Remove scripts/styles
    for tag in soup(["script", "style", "pre", "code", "table", "nav", "footer"]):
        tag.extract()

    # 5. Get plain text
    text = soup.get_text(separator="\n", strip=True)

    # 6. Normalize spaces
    # text = " ".join(text.split())

    # 5. Normalize whitespace in each line
    lines = [" ".join(line.split()) for line in text.split("\n")]

    # 6. Keep only lines ending in terminal punctuation AND with ≥5 words
    lines = [
        line for line in lines
        if len(line) >= MIN_CHARS_PER_LINE
        # if line.endswith(TERMINAL_PUNCTUATION) and len(line.split()) >= MIN_WORDS_PER_LINE
    ]

    # # 7. Discard documents with fewer than MIN_SENTENCES_PER_DOC lines
    if len(lines) < MIN_SENTENCES_PER_DOC:
        return None

    # 8. Re-join into single string
    text = "\n".join(lines)

    # if isinstance(html, bytes):  # convert bytes → str
    #     detected = chardet.detect(html)
    #     encoding = detected["encoding"] or "utf-8"
    #     html = html.decode(encoding, errors="ignore")
    #     # html = html.decode("utf-8", errors="ignore")
    # text_maker = html2text.HTML2Text()
    # text_maker.ignore_links = True
    # text_maker.ignore_images = True
    # text_maker.bypass_tables = False
    # text_maker.ignore_tables = True
    # text_maker.ignore_emphasis = True
    # text_maker.body_width = 0
    # text = text_maker.handle(html)
    # # text = html2text.html2text(html)
    # soup = BeautifulSoup(html, "html.parser")
    # text = soup.get_text(separator="\n", strip=True)
    return text

def replace_pii(text: str) -> str:
    """Masks personally identifiable information (PII) from text with the specified masking formats.
    Args: 
        text (str): Candidate text.
    Returns:
        str: Text with PII obfuscated.
    """
    if text != None:
        PHONE_PATTERN = r'\+1\s*(\d{10})'
        SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'
        text = re.sub(PHONE_PATTERN, lambda match: re.sub(r'\d', 'X', match.group()), text)
        text = re.sub(SSN_PATTERN, lambda match: re.sub(r'\d', 'X', match.group()), text)
        return text
    else:
        return None

def clean_text(text: str) -> str:
    """Removes substrings identified as low-quality according to alphanumeric, whitespace and valid document checks.  
    Args:
        text (str): document to process.
    Returns:
        str: cleaned document
    """
    return text

def heuristic_quality_filter(text: str) -> bool:
    """Rejects documents based on the presence of bad words and punctuation.
    Args:
        text (str): document to check
    Returns:
        bool: returns True if the document passes the filters, False otherwise.
    """

    if text == None:
        return False
    
    # 1. Test whether contain non-white-spacce characters
    contains_non_whitespace_characters = bool(text.strip())
    if not contains_non_whitespace_characters:
        return False
    
    # 2. Test whether contain bad words
    bad_words = retrieve_bad_words()
    text_lower = text.lower()
    contains_bad_words = any(bad_word in text_lower for bad_word in bad_words)
    if contains_bad_words:
        return False
    
    # 3. Test whether contain punctuation
    contains_punctuation = any(char in PUNCTUATION for char in text)
    if not contains_punctuation:
        return False

    # 4. Test whether at least 80% of characters in the document are one of: alphanumeric, punctuation, whitespace
    allowed_count = sum(1 for c in text if c in ALLOWED_CHARS)
    char_ratio = allowed_count / len(text)
    if char_ratio < 0.8:
        return False
    
    # If passes all filters, return True.
    return True



if __name__ == '__main__' :
    parser = argparse.ArgumentParser()
    parser.add_argument('--fname', type = str,  default = '', help = 'Specify the path for your warc file.')
    parser.add_argument('--num_records', type = int,  default=30, help = 'Specify the number of records you want to parse (only used for debugging with smaller sets)')
    args = parser.parse_args()
    
    # count number of records
    # count = 0
    # with open(args.fname, 'rb') as stream:
    #     for record in ArchiveIterator(stream):
    #         if (record.rec_type == 'response') and (record.http_headers.get_header('Content-Type') == 'text/html'):
    #             count += 1
    # print(count)

    str = replace_pii("My phone No is +1 1893749534, and SSN is 172-47-4823")
    print(str)

    if args.fname:
        for url, html_text in read_warc_file(args.fname, args.num_records):
            text = html_to_text(html_text)
            cleaned_text = clean_text(text)
            cleaned_nopii_text = replace_pii(cleaned_text)
            passes_check = heuristic_quality_filter(cleaned_nopii_text)
            
            print(url)
            print("Passes heuristic quality filter:", passes_check)
            print(cleaned_nopii_text)
            print("\n\n\n")
        
    else:
        print("Usage: python homework.py --fname data.warc")

    