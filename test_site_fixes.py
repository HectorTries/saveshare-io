#!/usr/bin/env python3
"""Focused checks for the five saveshare.io review fixes. Run: python3 test_site_fixes.py"""
import glob
import re
import unittest

ROOT_PAGES = ["index.html", "analytics.html"]
BLOG_POSTS = sorted(p for p in glob.glob("blog/*.html") if not p.endswith("blog/index.html"))
ALL_PAGES = ROOT_PAGES + sorted(glob.glob("blog/*.html")) + sorted(glob.glob("p/*.html"))


def read(path):
    return open(path, encoding="utf-8").read()


class TestSharedChrome(unittest.TestCase):
    def test_stylesheet_exists_and_linked_everywhere(self):
        self.assertTrue(glob.glob("styles.css"), "styles.css missing")
        for page in ALL_PAGES:
            self.assertIn("styles.css", read(page), page)

    def test_unified_nav_and_mobile_menu(self):
        for page in ALL_PAGES:
            html = read(page)
            nav = re.search(r"<nav.*?</nav>", html, re.S)
            self.assertIsNotNone(nav, page)
            labels = re.findall(r">([^<]+)</a>", nav.group(0))
            for want in ("Home", "Blog", "Analytics"):
                self.assertIn(want, labels, page)
            self.assertIn("nav-toggle", html, page)
            self.assertIn("aria-expanded", html, page)

    def test_no_em_dash_anywhere(self):
        for page in ALL_PAGES:
            self.assertNotIn("\u2014", read(page), page)


class TestCountsCurrencyTopics(unittest.TestCase):
    def test_creator_count_single_source(self):
        total = len(glob.glob("p/*.html"))
        self.assertEqual(total, 92)
        for page in ROOT_PAGES:
            self.assertIn(str(total), read(page), page)

    def test_analytics_currency_matches_region(self):
        html = read("analytics.html")
        rows = re.findall(r'<tr data-region="(uk|us)"[^>]*>(.*?)</tr>', html, re.S)
        self.assertGreater(len(rows), 50)
        for region, body in rows:
            m = re.search(r'class="num">([^<]+)', body)
            if not m:
                continue
            amount = m.group(1).strip()
            want = "£" if region == "uk" else "$"
            self.assertTrue(amount.startswith(want), f"{region} row shows {amount}")

    def test_homepage_topics_collapsed_and_one_cta(self):
        html = read("index.html")
        m = re.search(r'<select id="topic".*?</select>', html, re.S)
        options = re.findall(r"<option", m.group(0))
        self.assertLessEqual(len(options), 9, "topic filter must be All plus about 8 groups")
        hero = re.search(r'<div class="hero-ctas">(.*?)</div>', html, re.S).group(1)
        self.assertEqual(hero.count('class="btn'), 1, "hero must have one primary CTA")


class TestAnalytics(unittest.TestCase):
    def test_no_css_inside_script_and_no_duplicated_region_dom(self):
        html = read("analytics.html")
        for body in re.findall(r"<script[^>]*>(.*?)</script>", html, re.S):
            self.assertIsNone(re.search(r"\.(ts-grid|ts-card|spark)\s*\{", body))
        self.assertNotIn("data-rv=", html)

    def test_takeaways_keyboard_and_text_equivalents(self):
        html = read("analytics.html")
        self.assertGreaterEqual(html.count('class="takeaway"'), 5)
        self.assertIn("tabindex=", html)
        self.assertIn("chart-text", html)
        self.assertIn('type="application/json"', html)


class TestBlogPosts(unittest.TestCase):
    def test_every_post_structure(self):
        self.assertEqual(len(BLOG_POSTS), 20)
        for page in BLOG_POSTS:
            html = read(page)
            self.assertGreaterEqual(len(re.findall(r"<h2", html)), 2, page)
            self.assertIn("key-numbers", html, page)
            self.assertIn("<time datetime=", html, page)
            self.assertIn('"@type": "Article"', html.replace('": "', '": "'), page)
            self.assertNotIn("\ufffd", html, page)


if __name__ == "__main__":
    unittest.main(verbosity=2)
