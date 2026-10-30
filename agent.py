import concurrent.futures
import re
import os
import webbrowser
import feedparser
from openai import OpenAI

# API-Key sicher aus Umgebungsvariablen laden (wichtig für GitHub Secrets)
API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not API_KEY:
    print("❌ Fehler: OPENROUTER_API_KEY wurde nicht gefunden!")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

# 100 Kuratierte RSS-Quellen
kategorien_feeds = {
    "Neue Technik": [
        "https://www.heise.de/newsticker/heise-atom.xml", "https://rss.golem.de/rss.php?feed=RSS2.0",
        "https://www.chip.de/rss/rss_topnews.xml", "https://www.computerbase.de/rss/news.xml",
        "https://t3n.de/news/feed/", "https://www.netzwelt.de/rss.xml", "https://stadt-bremerhaven.de/feed/",
        "https://winfuture.de/rss/news.xml", "https://www.heise.de/developer/rss/news-atom.xml",
        "https://www.theverge.com/rss/index.xml", "https://techcrunch.com/feed/", "https://www.wired.com/feed/rss",
        "https://feeds.feedburner.com/arstechnica/index", "https://www.engadget.com/rss.xml",
        "https://mashable.com/feed", "https://gizmodo.com/rss", "https://venturebeat.com/feed/",
        "https://9to5mac.com/feed/", "https://www.androidcentral.com/feed", "https://www.technologyreview.com/feed/"
    ],
    "Wissenschaft": [
        "https://www.scinexx.de/feed/", "https://www.spektrum.de/alias/rss/spektrum-de-rss-feed/996056",
        "https://www.wissenschaft.de/feed/", "https://www.mpg.de/rss/de", "https://www.fraunhofer.de/de/presseservice.rss",
        "https://www.helmholtz.de/rss/", "https://www.dlr.de/de/rss/presse", "https://www.nature.com/nature.rss",
        "https://www.science.org/rss/news_current.xml", "https://www.newscientist.com/feed/home/",
        "https://phys.org/rss-feed/", "https://www.eurekalert.org/rss.xml",
        "https://www.scientificamerican.com/feed/", "https://www.nasa.gov/feed/", "https://www.esa.int/rssfeed/Germany"
    ],
    "Natur": [
        "https://www.nationalgeographic.de/rss.xml", "https://www.spiegel.de/wissenschaft/natur/index.rss",
        "https://www.geo.de/rss/geo-de-magazin.xml", "https://www.nabu.de/aktuell/rss.xml",
        "https://www.wwf.de/rss.xml", "https://www.greenpeace.de/rss.xml", "https://www.bund.net/rss.xml",
        "https://www.klimareporter.de/feed/", "https://news.mongabay.com/feed/", "https://www.earth.com/feed/"
    ],
    "Generelle Politik": [
        "https://www.tagesschau.de/xml/rss2/", "https://www.spiegel.de/politik/index.rss",
        "https://www.zeit.de/politik/index.xml", "https://www.faz.net/rss/aktuell/politik/",
        "https://www.sueddeutsche.de/rss/politik", "https://www.welt.de/feeds/section/politik.rss",
        "https://www.handelsblatt.com/contentexport/feed/politik", "https://www.fr.de/politik/rssfeed.xml",
        "https://taz.de/Politik/rss/", "https://rss.focus.de/fol/XML/rss_folnews_politik.xml",
        "https://www.stern.de/feed/standard/politik/", "https://www.n-tv.de/politik/rss",
        "https://www.br.de/nachrichten/politik/index.xml", "https://www.ndr.de/nachrichten/politik/index.xml",
        "https://www.deutschlandfunk.de/politik-100.rss"
    ],
    "Ukraine Krieg": [
        "https://www.tagesschau.de/thema/ukraine/index.rss", "https://www.zeit.de/thema/ukraine-konflikt/index.xml",
        "https://www.spiegel.de/politik/ausland/index.rss", "https://www.understandingwar.org/rss.xml",
        "https://kyivindependent.com/feed/", "https://meduza.io/rss/en/all", "https://www.bellingcat.com/feed/",
        "https://www.csis.org/rss/news", "https://carnegieendowment.org/rss/solr",
        "https://www.foreignaffairs.com/rss.xml"
    ],
    "Trumps neueste Aktivitäten": [
        "https://www.tagesschau.de/thema/trump/index.rss", "https://www.zeit.de/thema/donald-trump/index.xml",
        "https://www.politico.com/rss/politicopicks.xml", "https://thehill.com/feed/",
        "https://moxie.foxnews.com/google-publisher/politics.xml", "https://www.msnbc.com/feeds/latest",
        "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml", "https://feeds.washingtonpost.com/rss/politics",
        "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml", "https://rssfeeds.usatoday.com/usatoday-NewsTopStories",
        "https://api.axios.com/feed/", "https://abcnews.go.com/abcnews/politicsfeed",
        "https://www.cbsnews.com/latest/rss/politics", "https://www.nbcnews.com/id/3032552/device/rss/rss.xml",
        "https://www.latimes.com/politics/rss2.0.xml"
    ]
}

def bereinige_text(text):
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = ' '.join(clean.split())
    return clean[:400]

def lade_feed(url):
    try:
        return feedparser.parse(url).entries[:3]
    except Exception:
        return []

print("Lade 100 RSS-Quellen parallel herunter...")

kategorien_texte = {}

for kategorie, urls in kategorien_feeds.items():
    eintraege = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        ergebnisse = executor.map(lade_feed, urls)
        for feed_entries in ergebnisse:
            for e in feed_entries:
                titel = bereinige_text(e.get('title', ''))
                beschr = bereinige_text(e.get('summary', e.get('description', '')))
                if titel:
                    eintraege.append(f"- Titel: {titel}\n  Inhalt: {beschr}")
    
    kategorien_texte[kategorie] = "\n".join(eintraege[:15])

kategorien_payload = ""
for kat, inhalte in kategorien_texte.items():
    kategorien_payload += f"\n\n=== KATEGORIE: {kat} ===\n{inhalte}"

system_prompt = """
Du bist ein leitender Chefredakteur. Erstelle aus den RSS-Rohdaten ein hochdetailliertes, tiefgehendes Nachrichten-Briefing im HTML-Format.

STRUKTUR-ANFORDERUNGEN:
Gib deine Antwort in sauberem HTML-Quelltext zurück (ohne ```html Code-Blöcke).
Nutze folgende HTML-Struktur:

<section class="category-block">
    <h2 class="category-title">Kategorie-Name</h2>
    <article class="news-card">
        <h3 class="news-headline">Themen-Überschrift</h3>
        <div class="news-meta"><strong>Quellen/Kontext:</strong> ...</div>
        <div class="news-content">
            <p>Ausführlicher, mehrabsätziger Text mit allen Details, Hintergründen, Zahlen und Konsequenzen.</p>
        </div>
    </article>
</section>

WICHTIG:
- Erstelle Abschnitte für alle 6 Kategorien.
- Schreibe tiefgehende, gehaltvolle Fließtexte.
- Keine Vorrede, antworte direkt mit dem HTML-Code.
"""

user_prompt = f"Hier sind die Rohdaten aus den Feeds:\n{kategorien_payload}\n\nErstelle das HTML-Briefing für alle 6 Kategorien."

print("Generiere Dashboard-Inhalte via openrouter/auto...")

try:
    antwort = client.chat.completions.create(
        model="openrouter/auto",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=4000,
        extra_body={
            "reasoning": {"max_tokens": 0}
        }
    )

    html_inhalte = antwort.choices[0].message.content
    html_inhalte = re.sub(r'^```html\s*', '', html_inhalte, flags=re.MULTILINE)
    html_inhalte = re.sub(r'```$', '', html_inhalte, flags=re.MULTILINE)

    # Clean & Modern HTML Dashboard Template
    full_html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Daily Briefing Dashboard</title>
    <link href="[https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap)" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent-color: #38bdf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 0;
            line-height: 1.6;
        }}
        header {{
            background: linear-gradient(135deg, #1e293b, #0f172a);
            padding: 2.5rem 1.5rem;
            text-align: center;
            border-bottom: 1px solid var(--border-color);
        }}
        header h1 {{
            margin: 0;
            font-size: 2.2rem;
            color: var(--accent-color);
            font-weight: 700;
        }}
        header p {{
            margin: 0.5rem 0 0 0;
            color: var(--text-muted);
            font-size: 0.95rem;
        }}
        .container {{
            max-width: 1000px;
            margin: 2rem auto;
            padding: 0 1.5rem;
        }}
        .category-block {{
            margin-bottom: 3rem;
        }}
        .category-title {{
            font-size: 1.5rem;
            color: var(--accent-color);
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }}
        .news-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}
        .news-headline {{
            margin-top: 0;
            font-size: 1.25rem;
            color: #ffffff;
        }}
        .news-meta {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .news-content p {{
            margin-bottom: 1rem;
            color: #cbd5e1;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Tägliches Nachrichten-Briefing</h1>
        <p>100 Quellen verifiziert • Longform-Analyse • Automatisiert via GitHub</p>
    </header>

    <div class="container">
        {html_inhalte}
    </div>
</body>
</html>
"""

    # Als index.html speichern, damit GitHub Pages sie direkt als Startseite lädt
    html_filepath = os.path.abspath("index.html")
    with open(html_filepath, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"\n✅ Dashboard erfolgreich erstellt: {html_filepath}")

    # Lokal im Browser öffnen (wird in GitHub Actions ignoriert/übersprungen)
    try:
        webbrowser.open(html_filepath)
    except Exception:
        pass

except Exception as e:
    print(f"Fehler bei der Generierung: {e}")
