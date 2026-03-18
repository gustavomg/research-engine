from playwright.sync_api import sync_playwright
import urllib.parse
import re

def clean_query(query):
    """Limpia la query para búsquedas técnicas en inglés."""
    # Eliminar prefijos de beads
    query = re.sub(r'^.*SUBTEMA-\d+:\s*', '', query).strip()
    # Quedarse solo con términos en inglés si hay mezcla
    query = query[:80]
    return query

def search_arxiv(query, max_results=2):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            url = f"https://arxiv.org/search/?searchtype=all&query={urllib.parse.quote(query)}&start=0"
            page.goto(url, timeout=15000)
            page.wait_for_timeout(3000)

            papers = page.eval_on_selector_all(
                "li.arxiv-result",
                """els => els.slice(0,5).map(e => ({
                    title: e.querySelector('.title') ? e.querySelector('.title').innerText : '',
                    abstract: e.querySelector('.abstract') ? e.querySelector('.abstract').innerText : '',
                    link: e.querySelector('a') ? e.querySelector('a').href : ''
                }))"""
            )

            print(f"📚 {len(papers)} papers en arXiv para: {query[:50]}")
            for item in papers[:max_results]:
                if item['title'] and len(item['title']) > 5:
                    results.append({
                        "url": item['link'],
                        "title": item['title'].strip(),
                        "content": item['abstract'].strip()[:2000]
                    })
                    print(f"   ✅ {item['title'][:60]}")
        except Exception as e:
            print(f"⚠️  Error arXiv: {e}")
        finally:
            browser.close()
    return results

def search_wikipedia(query, lang="en"):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            url = f"https://{lang}.wikipedia.org/w/index.php?search={urllib.parse.quote(query)}"
            page.goto(url, timeout=15000)
            page.wait_for_timeout(2000)

            if "/wiki/" in page.url and "search" not in page.url:
                content = page.eval_on_selector_all(
                    "#mw-content-text p",
                    "els => els.map(e => e.innerText).filter(t => t.length > 60).slice(0,10).join('\\n')"
                )
                if content:
                    results.append({
                        "url": page.url,
                        "title": page.title(),
                        "content": content[:3000]
                    })
                    print(f"   ✅ Wikipedia: {page.title()[:60]}")
            else:
                first = page.query_selector(".mw-search-result-heading a")
                if first:
                    href = f"https://{lang}.wikipedia.org" + first.get_attribute("href")
                    page.goto(href, timeout=10000)
                    page.wait_for_timeout(1500)
                    content = page.eval_on_selector_all(
                        "#mw-content-text p",
                        "els => els.map(e => e.innerText).filter(t => t.length > 60).slice(0,10).join('\\n')"
                    )
                    if content:
                        results.append({
                            "url": page.url,
                            "title": page.title(),
                            "content": content[:3000]
                        })
                        print(f"   ✅ Wikipedia: {page.title()[:60]}")
        except Exception as e:
            print(f"⚠️  Error Wikipedia: {e}")
        finally:
            browser.close()
    return results

def search_web(query, max_results=3):
    print(f"\n🔍 Buscando: {query[:60]}")
    # Limpiar prefijos de Beads y usar query directamente
    query_clean = re.sub(r'^.*SUBTEMA-\d+:\s*', '', query).strip()[:100]
    results = []
    results += search_arxiv(query_clean, max_results=2)
    results += search_wikipedia(query_clean, lang="en")
    print(f"✅ Total fuentes: {len(results)}")
    return results[:max_results]

def format_results(results):
    if not results:
        return "No se encontraron resultados web."
    formatted = ""
    for i, r in enumerate(results, 1):
        formatted += f"\n--- Fuente {i}: {r['title']} ---\n"
        formatted += f"URL: {r['url']}\n"
        formatted += f"{r['content']}\n"
    return formatted

if __name__ == "__main__":
    results = search_web("software agents evolution applications 2024")
    print(format_results(results))
