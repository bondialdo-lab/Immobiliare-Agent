# Agente annunci San Lorenzo, Roma

Controlla periodicamente Immobiliare.it, Idealista.it e Casa.it per nuovi
annunci di appartamenti in **piena proprietà**, **San Lorenzo (Roma)**,
**minimo 30 mq**, e ti manda un'**email** con i nuovi annunci e il **prezzo
al mq** calcolato.

## 1. Crea un repository GitHub

1. Vai su github.com, crea un repository nuovo (anche privato).
2. Carica tutti i file di questa cartella nel repository (via web upload,
   oppure `git init && git add . && git commit -m "init" && git push`).

## 2. Imposta gli URL di ricerca (IMPORTANTE, fallo prima di tutto)

Apri `config.py` e sostituisci gli URL in `SEARCH_URLS` con quelli che
ottieni tu stesso impostando i filtri manualmente sul sito (zona San
Lorenzo, Roma, superficie minima 30 mq, escludendo la nuda proprietà se il
sito lo permette) e poi copiando l'URL della pagina risultati dal browser.
Le istruzioni dettagliate sono nei commenti del file.

## 3. Configura l'invio email (Gmail)

Dato che userai **bondialdotest@gmail.com** come mittente:

1. Vai su https://myaccount.google.com/apppasswords
2. Crea una "Password per le app" (serve avere l'autenticazione a due
   fattori attiva sull'account Google). Copiala: userai questa, NON la
   password normale dell'account.
3. Nel repository GitHub vai su **Settings → Secrets and variables →
   Actions → New repository secret** e crea questi 3 secret:
   - `EMAIL_USER` → bondialdotest@gmail.com
   - `EMAIL_PASS` → intb uxgn ngvs ltfv
   - `EMAIL_TO` → bondialdotest@gmail.com (o un altro indirizzo se vuoi
     ricevere lì gli avvisi)

## 4. Attiva il workflow

Il file `.github/workflows/check_listings.yml` è già pronto: gira
automaticamente **ogni 6 ore**. Per cambiare la frequenza, modifica la
riga `cron` (es. `0 */12 * * *` per ogni 12 ore, `0 8 * * *` per una volta
al giorno alle 8 UTC).

Per un primo test immediato, senza aspettare 6 ore: vai nel repository su
GitHub → tab **Actions** → seleziona il workflow → **Run workflow**.

## 5. Manutenzione: i selettori potrebbero rompersi

I portali immobiliari cambiano il codice HTML delle loro pagine di tanto
in tanto. Se lo script smette di trovare annunci (lo vedrai nei log della
tab Actions, dove dice "trovati 0 annunci grezzi"), significa che i
selettori CSS in `scraper.py` (funzioni `parse_immobiliare`,
`parse_idealista`, `parse_casa`) vanno aggiornati:

1. Apri la pagina di ricerca nel browser, tasto destro su un annuncio →
   "Ispeziona".
2. Guarda i nomi delle classi CSS della card dell'annuncio, del prezzo e
   della superficie.
3. Aggiorna i selettori corrispondenti in `scraper.py`.

Se mi incolli l'HTML aggiornato posso aiutarti a sistemarli di nuovo.

## Note

- Lo script fa richieste moderate (con pause) e non aggira captcha o
  blocchi anti-bot attivi: se un sito blocca la richiesta in un dato run,
  quel sito viene semplicemente saltato (vedrai un avviso nei log) e lo
  script continua con gli altri.
- L'uso è pensato per un controllo personale leggero. Verifica sempre i
  termini di servizio dei siti prima di un uso più intensivo o prolungato.
