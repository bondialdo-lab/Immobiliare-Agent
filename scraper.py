#!/usr/bin/env python3
"""
Agente di monitoraggio annunci immobiliari - San Lorenzo, Roma
================================================================

Cosa fa:
  1. Scarica le pagine di risultati di ricerca già filtrate (URL configurati
     in config.py) da Immobiliare.it, Idealista.it e Casa.it.
  2. Estrae per ogni annuncio: titolo, prezzo, superficie, link.
  3. Scarta gli annunci di "nuda proprietà" (teniamo solo piena proprietà).
  4. Scarta gli annunci sotto la superficie minima configurata.
  5. Calcola il prezzo al mq.
  6. Confronta con l'elenco degli annunci già visti (seen_listings.json)
     e individua solo i NUOVI annunci.
  7. Se ci sono nuovi annunci, invia un'email di riepilogo.
  8. Aggiorna e salva seen_listings.json (committato dal workflow GitHub Actions).

IMPORTANTE - leggi il README.md:
  - Devi impostare tu gli URL di ricerca in config.py (vedi istruzioni).
  - I portali immobiliari possono modificare il loro HTML in qualsiasi
    momento: se lo script smette di trovare annunci, i selettori CSS in
    questo file vanno aggiornati (istruzioni nel README).
  - Lo script fa richieste moderate (una ogni pochi secondi, User-Agent
    realistico) e rispetta un uso personale leggero. Non aggira captcha
    o blocchi anti-bot attivi: se un sito blocca la richiesta, quel sito
    viene semplicemente saltato in quel run (e viene loggato un avviso).
"""

import json
import os
import re
import sys
import time
import smtplib
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config import SEARCH_URLS, MIN_SQM, EXCLUDE_KEYWORDS, REQUEST_DELAY_SECONDS

SEEN_FILE = Path(__file__).parent / "seen_listings.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9",
}


@dataclass
class Listing:
    id: str
    site: str
    title: str
    price_eur: Optional[float]
    surface_sqm: Optional[float]
    url: str

    @property
    def price_per_sqm(self) -> Optional[float]:
        if self.price_eur and self.surface_sqm:
            return round(self.price_eur / self.surface_sqm)
        return None


def _to_number(text: str) -> Optional[float]:
    """Converte stringhe tipo '250.000 €' o '65 m²' in float."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d,]", "", text).replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def fetch(url: str) -> Optional[BeautifulSoup]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            print(f"  [AVVISO] {url} -> status {resp.status_code}, salto questo sito.")
            return None
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"  [AVVISO] Errore scaricando {url}: {e}")
        return None


def parse_immobiliare(soup: BeautifulSoup, base_url: str) -> list[Listing]:
    listings = []
    cards = soup.select("li[class*='nd-list__item'] a[class*='in-card']") or \
            soup.select("div[class*='in-realEstateListCard']")
    for card in cards:
        try:
            title_el = card.select_one("[class*='in-card__title']") or card
            title = title_el.get_text(strip=True)
            price_el = card.select_one("[class*='in-realEstateListCard__price']")
            price = _to_number(price_el.get_text()) if price_el else None
            surface_el = card.select_one("[class*='in-feat__data'], [class*='in-card__surface']")
            surface = _to_number(surface_el.get_text()) if surface_el else None
            href = card.get("href") or ""
            if href and not href.startswith("http"):
                href = "https://www.immobiliare.it" + href
            listing_id = re.sub(r"\D", "", href)[-10:] or href
            if href:
                listings.append(Listing(listing_id, "Immobiliare.it", title, price, surface, href))
        except Exception:
            continue
    return listings


def parse_idealista(soup: BeautifulSoup, base_url: str) -> list[Listing]:
    listings = []
    cards = soup.select("article.item")
    for card in cards:
        try:
            link_el = card.select_one("a.item-link")
            title = link_el.get_text(strip=True) if link_el else ""
            href = link_el.get("href") if link_el else None
            if href and not href.startswith("http"):
                href = "https://www.idealista.it" + href
            price_el = card.select_one("span.item-price")
            price = _to_number(price_el.get_text()) if price_el else None
            details = card.select("span.item-detail")
            surface = None
            for d in details:
                if "m" in d.get_text():
                    surface = _to_number(d.get_text())
                    break
            listing_id = card.get("data-element-id") or href
            if href:
                listings.append(Listing(listing_id, "Idealista.it", title, price, surface, href))
        except Exception:
            continue
    return listings


def parse_casa(soup: BeautifulSoup, base_url: str) -> list[Listing]:
    listings = []
    cards = soup.select("div[class*='listing-item'], article[class*='annuncio']")
    for card in cards:
        try:
            link_el = card.select_one("a[href*='/immobili/'], a[href*='/vendita/']")
            href = link_el.get("href") if link_el else None
            if href and not href.startswith("http"):
                href = "https://www.casa.it" + href
            title_el = card.select_one("[class*='title']")
            title = title_el.get_text(strip=True) if title_el else ""
            price_el = card.select_one("[class*='price']")
            price = _to_number(price_el.get_text()) if price_el else None
            surface_el = card.select_one("[class*='surface'], [class*='mq']")
            surface = _to_number(surface_el.get_text()) if surface_el else None
            listing_id = href
            if href:
                listings.append(Listing(listing_id, "Casa.it", title, price, surface, href))
        except Exception:
            continue
    return listings


PARSERS = {
    "immobiliare.it": parse_immobiliare,
    "idealista.it": parse_idealista,
    "casa.it": parse_casa,
}


def scrape_all() -> list[Listing]:
    all_listings: list[Listing] = []
    for url in SEARCH_URLS:
        domain = next((d for d in PARSERS if d in url), None)
        if not domain:
            print(f"  [AVVISO] Nessun parser per {url}, salto.")
            continue
        print(f"Scarico: {url}")
        soup = fetch(url)
        time.sleep(REQUEST_DELAY_SECONDS)
        if soup is None:
            continue
        found = PARSERS[domain](soup, url)
        print(f"  -> trovati {len(found)} annunci grezzi")
        all_listings.extend(found)
    return all_listings


def filter_listings(listings: list[Listing]) -> list[Listing]:
    result = []
    for l in listings:
        text = (l.title or "").lower()
        if any(kw.lower() in text for kw in EXCLUDE_KEYWORDS):
            continue  # es. nuda proprieta'
        if l.surface_sqm is not None and l.surface_sqm < MIN_SQM:
            continue
        result.append(l)
    return result


def load_seen() -> dict:
    if SEEN_FILE.exists():
        return json.loads(SEEN_FILE.read_text())
    return {}


def save_seen(seen: dict):
    SEEN_FILE.write_text(json.dumps(seen, indent=2, ensure_ascii=False))


def send_email(new_listings: list[Listing]):
    email_user = os.environ.get("EMAIL_USER")
    email_pass = os.environ.get("EMAIL_PASS")
    email_to = os.environ.get("EMAIL_TO")

    if not all([email_user, email_pass, email_to]):
        print("[ERRORE] Variabili EMAIL_USER / EMAIL_PASS / EMAIL_TO mancanti, email non inviata.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏠 {len(new_listings)} nuovi annunci a San Lorenzo, Roma"
    msg["From"] = email_user
    msg["To"] = email_to

    lines_html = []
    lines_txt = []
    for l in new_listings:
        ppsqm = f"{l.price_per_sqm:,} €/mq".replace(",", ".") if l.price_per_sqm else "n/d"
        price = f"{l.price_eur:,.0f} €".replace(",", ".") if l.price_eur else "n/d"
        surface = f"{l.surface_sqm:.0f} mq" if l.surface_sqm else "n/d"
        lines_html.append(
            f"<li><b>{l.title}</b> ({l.site})<br>"
            f"Prezzo: {price} — Superficie: {surface} — <b>Prezzo/mq: {ppsqm}</b><br>"
            f"<a href='{l.url}'>{l.url}</a></li><br>"
        )
        lines_txt.append(f"{l.title} ({l.site})\n{price} - {surface} - {ppsqm}\n{l.url}\n")

    html = f"<html><body><h2>Nuovi annunci - San Lorenzo, Roma</h2><ul>{''.join(lines_html)}</ul></body></html>"
    text = "\n\n".join(lines_txt)

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_user, email_pass)
        server.sendmail(email_user, email_to, msg.as_string())
    print(f"Email inviata a {email_to} con {len(new_listings)} annunci.")


def main():
    print("=== Avvio controllo annunci San Lorenzo, Roma ===")
    raw = scrape_all()
    filtered = filter_listings(raw)
    print(f"Annunci dopo i filtri (piena proprietà, min {MIN_SQM} mq): {len(filtered)}")

    seen = load_seen()
    new_listings = [l for l in filtered if l.id not in seen]

    if new_listings:
        print(f"Trovati {len(new_listings)} nuovi annunci. Invio email...")
        send_email(new_listings)
    else:
        print("Nessun nuovo annuncio rispetto all'ultimo controllo.")

    for l in filtered:
        seen[l.id] = asdict(l)
    save_seen(seen)
    print("=== Fine ===")


if __name__ == "__main__":
    main()
