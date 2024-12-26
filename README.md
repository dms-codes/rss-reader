# RSS Reader

## Overview
The RSS Reader is a desktop application for reading and managing RSS feeds. It is built using Python and the wxPython library for the graphical user interface. The application allows users to:

- Add, edit, and remove RSS feed URLs.
- Organize feeds into categories.
- View feed content and metadata.
- Analyze content sentiment and extract keywords.
- Translate feed content.
- Copy screenshots of feed content to the clipboard.

## Features

- **Tree-Based Feed Organization**: Categorize and manage RSS feeds in a hierarchical structure.
- **Content Viewer**: View and interact with feed content in an HTML panel.
- **Sentiment Analysis**: Automatically analyze the sentiment (positive, negative, or neutral) of feed content.
- **Keyword Extraction**: Identify and display the most relevant keywords from feed content.
- **Translation**: Translate feed titles and content to Indonesian or other languages using Google Translator.
- **Screenshot to Clipboard**: Copy a screenshot of the feed content panel to the clipboard.

## Installation

### Prerequisites
- Python 3.8 or later
- Pip (Python package manager)

### Install Required Libraries
Run the following command to install the necessary libraries:

```bash
pip install wxPython feedparser nltk textblob Sastrawi deep-translator
```

### Download the Application
Clone or download the repository to your local machine:

```bash
git clone https://github.com/dms-codes/rss-reader.git
cd rss-reader
```

### Additional Setup
1. **NLTK Setup**: Download the necessary NLTK data for tokenization and stopwords.
   Run the following Python code:

   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   ```

2. **Feed URLs File**: Create a `feed_urls.txt` file in the project directory to store feed URLs, descriptions, and categories. Each line should be in the format:

   ```
   <feed_url>|<description>|<category>
   ```

## Usage

1. Run the application:
   ```bash
   python rss_reader.py
   ```
2. Add, edit, or remove feed URLs using the tree-based interface.
3. Select a feed to view its content, metadata, and sentiment analysis.
4. Use the toolbar to copy screenshots of feed content to the clipboard.

## Key Components

### Main Application (RSSReaderFrame)
- **Feed URL Panel**: Manage RSS feeds and categories.
- **Title Panel**: Display titles of feed entries.
- **Content Panel**: Show the content of the selected feed entry, including metadata, keywords, sentiment, and translations.

### Utility Functions
- **Keyword Extraction**: Extracts the most common keywords using NLTK and Sastrawi.
- **Sentiment Analysis**: Uses TextBlob to analyze content sentiment.
- **Translation**: Uses GoogleTranslator for content translation.
- **Feed Parsing**: Uses `feedparser` to parse RSS feeds.

## File Structure

```
.
├── rss_reader.py       # Main application script
├── feed_urls.txt       # File storing feed URLs, descriptions, and categories
├── rss_icon.png        # Icon for the application (optional)
└── README.md           # Documentation
```

## Screenshots

### Main Interface
![Main Interface](example_screenshot.png)

## Contributing
Feel free to fork the repository and submit pull requests. For major changes, please open an issue to discuss the changes first.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Author
- **dms-codes**  
GitHub: [github.com/dms-codes](https://github.com/dms-codes)
