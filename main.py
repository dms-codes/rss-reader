import wx
import wx.dataview
import wx.html2
import feedparser
import os
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
from textblob import TextBlob
import re
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from deep_translator import GoogleTranslator
from collections import defaultdict

class RSSReaderFrame(wx.Frame):
    """Main application frame for the RSS Reader."""

    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(800, 600))

        # Set program icon
        self.set_program_icon("rss_icon.png")

        # Load feed URLs, descriptions, and categories from file
        self.feed_urls = self.load_feed_urls()

        # Initialize UI
        self.setup_ui()

        # Populate the feed URL tree with categories
        self.update_feed_url_tree()

        # Bind right-click context menu
        self.feed_url_tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.on_tree_right_click)

        # Finalize window setup
        self.Maximize(True)
        self.Centre()
        self.Show()

    def set_program_icon(self, icon_path):
        """Set the program icon."""
        if os.path.exists(icon_path):
            self.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_PNG))

    def setup_ui(self):
        """Set up the main UI with split panes."""
        # Main splitters
        self.splitter1 = wx.SplitterWindow(self)
        self.splitter2 = wx.SplitterWindow(self.splitter1)

        # Create panels
        self.feed_url_panel = self.create_feed_url_panel(self.splitter1)
        self.title_panel = self.create_title_panel(self.splitter2)
        self.content_panel = self.create_content_panel(self.splitter2)

        # Add Copy to Clipboard button
        self.add_toolbar()

        # Configure splitters
        self.splitter2.SplitVertically(self.title_panel, self.content_panel, sashPosition=300)
        self.splitter1.SplitVertically(self.feed_url_panel, self.splitter2, sashPosition=200)

    def add_toolbar(self):
        """Add a toolbar with a 'Copy Screenshot to Clipboard' button."""
        toolbar = self.CreateToolBar()
        copy_btn = toolbar.AddTool(wx.ID_ANY, "Copy to Clipboard", wx.ArtProvider.GetBitmap(wx.ART_COPY, wx.ART_TOOLBAR))
        toolbar.Realize()

        # Bind the copy button to the copy function
        self.Bind(wx.EVT_TOOL, self.copy_content_panel_to_clipboard, copy_btn)

    def copy_content_panel_to_clipboard(self, event):
        """Capture the content panel and copy it to the clipboard."""
        # Get the size of the content panel
        size = self.content_panel.GetSize()
        bitmap = wx.Bitmap(size.width, size.height)

        # Create a memory device context
        memory_dc = wx.MemoryDC(bitmap)
        memory_dc.Blit(0, 0, size.width, size.height, wx.ClientDC(self.content_panel), 0, 0)
        memory_dc.SelectObject(wx.NullBitmap)

        # Copy bitmap to clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.BitmapDataObject(bitmap))
            wx.TheClipboard.Close()
            wx.MessageBox("Screenshot copied to clipboard!", "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("Failed to open clipboard.", "Error", wx.OK | wx.ICON_ERROR)


    def create_feed_url_panel(self, parent):
        """Create the left panel for managing feed URLs."""
        panel = wx.Panel(parent)

        # TreeCtrl for feed URLs
        self.feed_url_tree = wx.TreeCtrl(panel, style=wx.TR_DEFAULT_STYLE | wx.TR_EDIT_LABELS)
        self.feed_url_tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_feed_selected)

        # Buttons
        buttons = [
            ("Add URL", self.on_add_url),
            ("Remove URL", self.on_remove_url),
            ("Edit URL", self.on_edit_url),
        ]

        button_sizer = wx.BoxSizer(wx.VERTICAL)
        for label, handler in buttons:
            button = wx.Button(panel, label=label)
            button.Bind(wx.EVT_BUTTON, handler)
            button_sizer.Add(button, 0, wx.EXPAND | wx.ALL, 5)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.feed_url_tree, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.EXPAND)
        panel.SetSizer(sizer)

        return panel

    def remove_images_from_content(self, content):
        """Remove <img> tags from the HTML content."""
        # Use regex to remove <img> tags
        content = re.sub(r'<img\b[^>]*>', '', content, flags=re.IGNORECASE)
        return content
    
    def get_thumbnail(self, entry):
        """Retrieve the thumbnail or media content from the feed entry."""
        if 'media_thumbnail' in entry:
            return entry['media_thumbnail'][0].get('url', "")
        if 'media_content' in entry:
            return entry['media_content'][0].get('url', "")
        if 'enclosures' in entry and entry['enclosures']:
            return entry['enclosures'][0].get('href', "")
        return ""

    def update_feed_url_tree(self):
        """Update the feed URL tree with categories, URLs, and descriptions."""
        self.feed_url_tree.DeleteAllItems()
        root = self.feed_url_tree.AddRoot("Feeds")

        # Group URLs by categories
        categories = {}
        for url, description, category in self.feed_urls:
            categories.setdefault(category, []).append((url, description))

        # Populate the tree
        for category, feeds in categories.items():
            category_item = self.feed_url_tree.AppendItem(root, category)
            for url, description in feeds:
                feed_item = self.feed_url_tree.AppendItem(category_item, description)
                self.feed_url_tree.SetItemData(feed_item, url)

        self.feed_url_tree.Expand(root)


    @staticmethod
    def get_keywords(text):
        """Extract keywords from the given text."""
        words = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        # Stopwords bahasa Indonesia menggunakan Sastrawi
        factory = StopWordRemoverFactory()
        stop_words_id = factory.get_stop_words()

        # Gabungkan stopwords Bahasa Inggris dan Indonesia
        stop_words.update(stop_words_id)
        stop_words.update(stopwords.words('norwegian'))  # Add Norwegian stop words

        keywords = [word for word in words if word.isalnum() and word not in stop_words]
        most_common = Counter(keywords).most_common(3)
        return [kw[0] for kw in most_common]

    def get_sentiment_label(self, content):
        """Analyze sentiment of the given content."""
        try:
            sentiment = TextBlob(content).sentiment.polarity
            if sentiment > 0:
                return "Positive"
            elif sentiment < 0:
                return "Negative"
            else:
                return "Neutral"
        except Exception as e:
            return f"Error analyzing sentiment: {e}"


    def get_publication_date(self, entry):
        """Retrieve the publication date of the feed entry."""
        return entry.get('published') or entry.get('updated') or "No Publication Date Available"


    def on_title_selected(self, event):
        """Display the content of the selected feed item."""
        selection = self.title_list.GetSelection()
        if selection == wx.NOT_FOUND or not hasattr(self, 'current_feed_entries'):
            return

        entry = self.current_feed_entries[selection]
        title_ = entry.get('title', "No Title Available")
        content = entry.get('summary', "No Content Available")
        content = self.remove_images_from_content(content)

        # Validate content
        title_ = title_.strip() or "No Title Available"
        content = content.strip() or "No Content Available"

        try:
            translated_title = GoogleTranslator(source='auto', target='id').translate(title_)
        except Exception as e:
            print(f"Translation Error (Title): {e}")
            translated_title = "Translation not available"

        try:
            translated_content = GoogleTranslator(source='auto', target='id').translate(content)
        except Exception as e:
            print(f"Translation Error (Content): {e}")
            translated_content = "Translation not available"

        link = entry.get('link', "#")
        pub_date = self.get_publication_date(entry)
        image = self.get_thumbnail(entry)
        sentiment_label = self.get_sentiment_label(content)
        if content == "No Content Available":
            keywords = self.get_keywords(title_)
        else:
            keywords = self.get_keywords(content)


        if title_ == translated_title or content == translated_content:
            # Construct HTML
            html_content = (
                f"<h1>{title_.title()}</h1>"
                f"<p><strong>Published:</strong> {pub_date}</p>"
                f"<p><strong>Keywords:</strong> {', '.join(keywords)}</p>"
                f"<p><strong>Sentiment:</strong> {sentiment_label}</p>"
                f"<p>{content}</p>"
            )
        else:
                        # Construct HTML
            html_content = (
                f"<h1>{title_.title()}</h1>"
                f"<h1>{translated_title.title()}</h1>"
                f"<p><strong>Published:</strong> {pub_date}</p>"
                f"<p><strong>Keywords:</strong> {', '.join(keywords)}</p>"
                f"<p><strong>Sentiment:</strong> {sentiment_label}</p>"
                f"<p>{content}</p>"
                f"<p>{translated_content}</p>"
            )


        if image:
            html_content += f'<p><img src="{image}" alt="Thumbnail" style="max-width:100%;"></p>'
        html_content += f'<p><a href="{link}">Read more</a></p>'

        self.content_html.SetPage(html_content, "")


    def create_title_panel(self, parent):
        """Create the middle panel for displaying feed titles."""
        panel = wx.Panel(parent)
        self.title_list = wx.ListBox(panel, style=wx.LB_SINGLE)
        self.title_list.Bind(wx.EVT_LISTBOX, self.on_title_selected)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title_list, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)

        return panel

    def create_content_panel(self, parent):
        """Create the right panel for displaying feed content."""
        panel = wx.Panel(parent)
        self.content_html = wx.html2.WebView.New(panel)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.content_html, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)

        return panel

    def on_feed_selected(self, event):
        """Fetch and display feed titles for the selected feed URL."""
        item = self.feed_url_tree.GetSelection()
        if not item.IsOk():
            return

        selected_feed_url = self.feed_url_tree.GetItemData(item)
        if not selected_feed_url:
            return

        try:
            # Parse the feed
            feed = feedparser.parse(selected_feed_url)

            # Clear existing data
            self.title_list.Clear()
            self.content_html.SetPage("<html><body></body></html>", "")

            # Populate titles
            self.current_feed_entries = feed.entries
            for item in feed.entries:
                title = item.get('title', "No Title Available")
                self.title_list.Append(title)

        except Exception as e:
            wx.MessageBox(f"Error fetching feed: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def update_feed_url_tree(self):
        """Update the feed URL tree with the loaded URLs."""
        self.feed_url_tree.DeleteAllItems()
        root = self.feed_url_tree.AddRoot("Feeds")

        for url, description in self.feed_urls:
            item = self.feed_url_tree.AppendItem(root, description)
            self.feed_url_tree.SetItemData(item, url)

        self.feed_url_tree.Expand(root)

    def on_remove_category(self, event):
        """Remove a selected category."""
        item = self.feed_url_tree.GetSelection()
        category = self.feed_url_tree.GetItemText(item)

        # Confirm removal
        confirm = wx.MessageBox(
            f"Are you sure you want to remove the category '{category}' and all its feeds?",
            "Confirm",
            wx.YES_NO | wx.ICON_WARNING,
        )
        if confirm == wx.YES:
            # Remove all feeds in this category
            self.feed_urls = [(url, desc, cat) for url, desc, cat in self.feed_urls if cat != category]
            self.update_feed_url_tree()
            self.save_feed_urls()

    def on_add_category(self, event):
        """Add a new category."""
        dialog = wx.TextEntryDialog(self, "Enter new category name:", "Add Category")
        if dialog.ShowModal() == wx.ID_OK:
            category = dialog.GetValue().strip()
            if category:
                # Ensure category doesn't already exist
                if category not in [cat for _, _, cat in self.feed_urls]:
                    self.feed_urls.append(("", "", category))
                    self.update_feed_url_tree()
                    self.save_feed_urls()
        dialog.Destroy()

    def on_tree_right_click(self, event):
        """Show a context menu when an item in the tree is right-clicked."""
        item = event.GetItem()
        if not item.IsOk():
            return

        self.feed_url_tree.SelectItem(item)
        is_root = item == self.feed_url_tree.GetRootItem()
        is_category = not self.feed_url_tree.GetItemData(item)

        # Create a context menu
        menu = wx.Menu()
        if is_root or is_category:
            # Category-related options
            menu.Append(wx.ID_ADD, "Add Category")
            menu.Append(wx.ID_EDIT, "Edit Category")
            menu.Append(wx.ID_DELETE, "Remove Category")
        else:
            # Feed URL-related options
            menu.Append(wx.ID_EDIT, "Edit Feed URL")
            menu.Append(wx.ID_DELETE, "Remove Feed URL")

        # Bind menu options
        menu.Bind(wx.EVT_MENU, self.on_edit_category, id=wx.ID_EDIT)
        menu.Bind(wx.EVT_MENU, self.on_remove_url, id=wx.ID_DELETE)

        # Show the menu
        self.PopupMenu(menu)
        menu.Destroy()


    def on_add_url(self, event):
        """Add a new feed URL under a selected category."""
        # Ensure a category is selected
        item = self.feed_url_tree.GetSelection()
        if not item.IsOk():
            wx.MessageBox("Please select a category first.", "Error", wx.OK | wx.ICON_ERROR)
            return

        category = self.feed_url_tree.GetItemText(item)

        # Prompt user for the feed URL
        dialog = wx.TextEntryDialog(self, "Enter Feed URL:", "Add Feed URL")
        if dialog.ShowModal() == wx.ID_OK:
            url = dialog.GetValue().strip()
            if url:
                try:
                    # Parse the feed using feedparser
                    feed = feedparser.parse(url)
                    if feed.bozo:  # Check for parsing errors
                        wx.MessageBox("Invalid feed URL. Please try again.", "Error", wx.OK | wx.ICON_ERROR)
                        return

                    # Fetch the description from the first item's title
                    description = feed.feed.title if 'title' in feed.feed else "No Title Available"
                    
                    # Add the URL and description to the feed list
                    self.feed_urls.append((url, description, category))
                    self.update_feed_url_tree()
                    self.save_feed_urls()
                except Exception as e:
                    wx.MessageBox(f"Error fetching feed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            else:
                wx.MessageBox("The URL cannot be empty.", "Error", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()


    def on_remove_url(self, event):
        """Remove the selected feed URL."""
        item = self.feed_url_tree.GetSelection()
        feed_url = self.feed_url_tree.GetItemData(item)

        # Confirm removal
        confirm = wx.MessageBox(
            f"Are you sure you want to remove this feed URL?",
            "Confirm",
            wx.YES_NO | wx.ICON_WARNING,
        )
        if confirm == wx.YES:
            self.feed_urls = [(url, desc, cat) for url, desc, cat in self.feed_urls if url != feed_url]
            self.update_feed_url_tree()
            self.save_feed_urls()

    def on_edit_category(self, event):
        """Edit the selected category name."""
        item = self.feed_url_tree.GetSelection()
        old_category = self.feed_url_tree.GetItemText(item)

        dialog = wx.TextEntryDialog(self, "Edit Category Name:", "Edit Category", old_category)
        if dialog.ShowModal() == wx.ID_OK:
            new_category = dialog.GetValue().strip()
            if new_category and new_category != old_category:
                # Update category name
                self.feed_urls = [
                    (url, desc, new_category if cat == old_category else cat)
                    for url, desc, cat in self.feed_urls
                ]
                self.update_feed_url_tree()
                self.save_feed_urls()
        dialog.Destroy()

    def get_feed_description(self, url):
        """Fetch the description of the feed from the URL."""
        feed = feedparser.parse(url)
        return feed.feed.get('title', 'No Title Available')

    def load_feed_urls(self):
        """Load feed URLs, descriptions, and categories from a file."""
        feed_urls_file = 'feed_urls.txt'
        if os.path.exists(feed_urls_file):
            with open(feed_urls_file, 'r') as f:
                return [tuple(line.strip().split('|')) for line in f.readlines()]
        return []

    def save_feed_urls(self):
        """Save feed URLs, descriptions, and categories to a file."""
        feed_urls_file = 'feed_urls.txt'
        with open(feed_urls_file, 'w') as f:
            for url, description, category in self.feed_urls:
                f.write(f"{url}|{description}|{category}\n")

    def update_feed_url_tree(self):
        """Update the feed URL tree with the loaded URLs, descriptions, and categories."""
        self.feed_url_tree.DeleteAllItems()
        root = self.feed_url_tree.AddRoot("Feeds")

        # Group feeds by category
        categories = defaultdict(list)
        for url, description, category in self.feed_urls:
            categories[category].append((url, description))

        # Populate the tree by category
        for category, feeds in categories.items():
            category_item = self.feed_url_tree.AppendItem(root, category)
            for url, description in feeds:
                feed_item = self.feed_url_tree.AppendItem(category_item, description)
                self.feed_url_tree.SetItemData(feed_item, url)

        self.feed_url_tree.Expand(root)

    def on_edit_url(self, event):
        """Edit the selected feed URL and description."""
        item = self.feed_url_tree.GetSelection()
        current_url = self.feed_url_tree.GetItemData(item)

        # Find the corresponding feed
        for url, description, category in self.feed_urls:
            if url == current_url:
                dialog = wx.TextEntryDialog(
                    self,
                    "Edit Feed URL|Description:",
                    "Edit Feed URL",
                    f"{url}|{description}",
                )
                if dialog.ShowModal() == wx.ID_OK:
                    updated_entry = dialog.GetValue().split('|')
                    if len(updated_entry) == 2:
                        updated_url, updated_description = updated_entry
                        self.feed_urls = [
                            (updated_url, updated_description, category)
                            if url == current_url else (url, desc, cat)
                            for url, desc, cat in self.feed_urls
                        ]
                        self.update_feed_url_tree()
                        self.save_feed_urls()
                dialog.Destroy()
                break

if __name__ == '__main__':
    app = wx.App()
    frame = RSSReaderFrame(None, title="RSS Reader github.com/dms-codes")
    app.MainLoop()
