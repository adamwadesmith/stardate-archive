# Pytest tests for the sitemap

import pytest
from app import scrape_stardate as scraper
from pathlib import Path

def test_fetch_podcast_sitemaps():
    expected = ['https://stardate.org/podcast-sitemap.xml', 'https://stardate.org/podcast-sitemap2.xml', 'https://stardate.org/podcast-sitemap3.xml']
    text = Path('tests/sitemap.xml').read_text()
    actual = scraper.fetch_podcast_sitemaps(text)
    assert expected == actual
