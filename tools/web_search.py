from playwright.sync_api import sync_playwright
import urllib.parse

def search_arxiv(query, max_results=2):
    """Busca papers en arXiv — fuente abierta de investigación técnica."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            url = f"https://arxiv.org/search/?searchtype=all&query={urllib.parse.quote(query)}&start=0"
            page.goto(url, timeout=15000)
            page.wait_for_timeout(2000)

            papers = page.eval_on_selector_all(
                "li.arxiv-result",
                """els => els.slice(0,5).map(e => ({
                    title: e.querySelector('.title')?.innerText || '',
                    abstract: e.querySelector('.abstract')?.innerText || '',
                    link: e.querySelector('a')?.href || ''
                }))"""
            )

            print(f"📚 {len(papers)} papers en arXiv para: {query}")
            for p_item in papers[:max_results]:
                if p_item['title']:
                    results.append({
                        "url": p_item['link'],
                        "title": p_item['title'].strip(),
                        "content": p_item['abstract'].strip()[:2000]
                    })
                    print(f"   ✅ {p_item['title'][:60]}")
        except Exception as e:
            print(f"⚠️  Error arXiv: {e}")
        finally:
            browser.close()
    return results

def search_wikipedia(query, lang="en"):
    """Busca en Wikipedia — fuente abierta y estructurada."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            url = f"https://{lang}.wikipedia.org/w/index.php?search={urllib.parse.quote(query)}"
            page.goto(url, timeout=15000)
            page.wait_for_timeout(2000)

            # Si redirige directo al artículo
            if "/wiki/" in page.url and "search" not in page.url:
                content = page.eval_on_selector_all(
                    "#mw-content-text p",
                    "els => els.map(e => e.innerText).filter(t => t.length > 60).slice(0,10).join('\\n')"
                )
                title = page.title()
                if content:
                    results.append({
                        "url": page.url,
                        "title": title,
                        "content": content[:3000]
                    })
                    print(f"   ✅ Wikipedia: {title[:60]}")
            else:
                # Página de resultados — tomar primer resultado
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
    """Combina arXiv + Wikipedia para investigación técnica."""
    print(f"\n🔍 Buscando: {query}")
    results = []
    results += search_arxiv(query, max_results=2)
    results += search_wikipedia(query, lang="en")
    print(f"✅ Total fuentes obtenidas: {len(results)}")
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
    results = search_web("multi-agent AI systems architecture 2024")
    print(format_results(results))
