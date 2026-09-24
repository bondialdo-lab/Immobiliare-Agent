# -*- coding: utf-8 -*-
"""
Configurazione dell'agente di monitoraggio annunci.

>>> COME IMPOSTARE SEARCH_URLS (fallo prima di avviare l'automazione) <<<

1. Vai su ciascun portale nel browser normale.
2. Imposta manualmente i filtri di ricerca:
   - Città: Roma
   - Zona/quartiere: San Lorenzo
   - Tipologia: Vendita, esclusa "Nuda proprietà" (se il sito ha questo filtro)
   - Superficie minima: 30 mq
3. Copia l'URL della pagina dei risultati (quello con tutti i parametri
   di ricerca già applicati) e incollalo qui sotto.

Esempi indicativi di come appaiono questi URL (i parametri esatti possono
cambiare nel tempo, per questo è meglio copiarli direttamente dal browser):
  - https://www.immobiliare.it/vendita-case/roma/san-lorenzo/?superficieMinima=30
  - https://www.idealista.it/vendita-case/roma/san-lorenzo/con-superficie-min_30/
  - https://www.casa.it/vendita/residenziale/roma/san-lorenzo/
"""

SEARCH_URLS = [
    "https://www.immobiliare.it/search-list/?idContratto=1&idCategoria=1&superficieMinima=40&tipoProprieta=1&criterio=rilevanza&noAste=1&__lang=it&vrt=41.89304%2C12.515661%3B41.896672%2C12.511154%3B41.901042%2C12.519147%3B41.898615%2C12.520607%3B41.89737%2C12.519791%3B41.89304%2C12.515661&pag=1",

    "https://www.idealista.it/vendita-case/roma/nomentano-tiburtino/tiburtino-san-lorenzo/con-dimensione_40,aste_no/",

    "https://www.casa.it/srp/?tr=vendita&propertyTypeGroup=casa&q=f1362495&mq=40-&isUnderConstruction=false",
]

# Superficie minima in mq (doppio controllo oltre al filtro nell'URL,
# utile se un sito non supporta bene quel parametro)
MIN_SQM = 30

# Annunci che contengono queste parole nel titolo vengono ESCLUSI
# (serve a filtrare la nuda proprietà e tenere solo la piena proprietà)
EXCLUDE_KEYWORDS = [
    "nuda proprietà",
    "nuda proprieta",
    "usufrutto",
]

# Pausa in secondi tra una richiesta e l'altra (per non sovraccaricare i siti)
REQUEST_DELAY_SECONDS = 3
