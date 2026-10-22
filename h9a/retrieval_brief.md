Task: download the full plain texts of the public-domain ethnographies listed in /root/analysis/h9a/sample.csv (columns include society, society_key, fulltext_url, title, author, year).
- Do not read, summarize or evaluate their content beyond checking completeness.
- Do not open any other file under /root/analysis.
- Never load a whole book into your own context: these texts run to hundreds of thousands of words.

METHOD (the shell cannot reach these sites; use the Chrome browser)
1. Load the tools with ToolSearch query "select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__tabs_close_mcp".
   - Create your OWN tab, never touch other tabs, and close it at the end.
2. For each row:
   a. Navigate your tab to the plain-text URL.
      - Project Gutenberg: https://www.gutenberg.org/cache/epub/<ID>/pg<ID>.txt
      - Internet Archive: https://archive.org/download/<identifier>/<identifier>_djvu.txt, which is plain text; the /stream/ URLs are HTML pages.
   b. Use javascript_tool to return ONLY short facts: document.body.innerText.length, the first 300 characters and the last 300 characters. This is how you check that it is the right, complete book.
   c. Call get_page_text with max_chars 6000000. A result this large is not shown to you. It is saved to a file, and the tool result gives that file's path.
      - Use Bash with python to read that file and write the text to /root/analysis/h9a/texts/<society_key>.txt, using exactly the society_key value from sample.csv.
      - The saved file is usually JSON: a list whose first element has a 'text' field. If it is not JSON, use the raw content.
      - Do NOT use the Read tool on it, and do not print more than 300 characters of it.
      - Check that the saved length is within 2 percent of innerText.length.
   d. Check the text with python:
      - it is the right book (the title words appear in the first 3,000 characters);
      - it is complete (the end is an index, an appendix, a colophon or a licence, not a cut-off);
      - the OCR is mostly words: at least 80 percent of whitespace-separated tokens are alphabetic.
3. Record the result in /root/analysis/h9a/retrieval_log.csv, with columns: society_key, url, chars, words, alpha_share, complete (Y/N), notes.
   - If a URL fails, look for another public-domain full text of the SAME book (another Internet Archive scan, or Gutenberg) and record that.
   - Never substitute a different book.

Final reply: the number of texts saved, and the societies that failed and why.
