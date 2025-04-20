# Test imports to verify environment setup
def test_imports():
    # Data processing imports
    import pandas as pd
    import numpy as np
    from sklearn import datasets

    # Web scraping imports
    from bs4 import BeautifulSoup
    import requests
    # feedparser removed due to Python 3.13 compatibility issues

    # NLP imports
    import nltk
    from textblob import TextBlob
    from transformers import pipeline

    print("All data processing, web scraping, and NLP imports successful!")
    print("Note: Some packages (FastAPI, feedparser) temporarily disabled due to Python 3.13 compatibility")

if __name__ == "__main__":
    test_imports()
