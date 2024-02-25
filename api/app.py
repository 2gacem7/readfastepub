from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from ebooklib import epub
import os
import re
from html import unescape
from bs4 import BeautifulSoup
app = FastAPI()
import html

import re


def bold_inside_p_tags(text):
    # Decode HTML entities
    text = unescape(text)
    # Pattern to match <p> tags and their content
    pattern = r'<p(?:\s+class="[^"]*")?>(.*?)</p>|<img(?:\s+[^>]+)?/>'
    
    def replace(match):
        if match.group().startswith('<p'):  # If it's a <p> tag
            content = match.group(1)
            words = re.split(r'(\W+)', content)  # Split words with punctuation preserved
            bolded_words = []  # To store bolded words
            for word in words:
                # Bold 50% of each word
                half_length = len(word) // 2
                bolded_word = f'<b>{word[:half_length]}</b><span style="font-weight: normal">{word[half_length:]}</span>'
                bolded_words.append(bolded_word)
            return f"<p>{''.join(bolded_words)}</p>"
        else:
            return match.group()  # If it's not a <p> tag, return unchanged
    
    # Replace content inside <p> tags
    return re.sub(pattern, replace, text)
# Example usage
html_text = '<p>This is a test sentence.</p>'
result = bold_inside_p_tags(html_text)
print(result)


def clean_html_content(html_content):
    # Retirer la déclaration XML
    cleaned_content = re.sub(r'<\?xml.*?\?>', '', html_content)
    # Retirer les balises HTML vides ou avec du contenu non significatif
    cleaned_content = re.sub(r'<(?!\/?b\b)(?!\/?p\b)(?!\/?h1\b)(?!\/?img\b)[^>]*>[^<]*<\/[^>]+>', '', cleaned_content)
    return cleaned_content


def modify_epub(input_epub_file, output_epub_file):
    book = epub.read_epub(input_epub_file)

    for item in book.get_items():
         if isinstance(item, epub.EpubHtml):
            html_content = item.get_content().decode('utf-8')
            cleaned_html_content = clean_html_content(html_content)
            modified_html_content = bold_inside_p_tags(cleaned_html_content)
            item.content = modified_html_content.encode('utf-8')

    epub.write_epub(output_epub_file, book)


@app.post("/bold_first_half_in_epub/")
async def process_epub_file(input_file: UploadFile = File(...)):
    if not input_file.filename.endswith(".epub"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an EPUB file")
        
    output_file_path = "output.epub"
    with open(output_file_path, "wb") as output_file:
        output_file.write(input_file.file.read())
    
    try:
        modify_epub(output_file_path, output_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing EPUB file: {str(e)}")
    
    return FileResponse(output_file_path, filename=output_file_path, media_type='application/epub+zip')
