# Tunisia Distributed Scraping System

Système de scraping distribué pour 8 sites tunisiens : **Aziza, MG, Carrefour Tunisie, Glovo Tunisie, Mytek, Tunisianet, Spacenet, Ben Yaghlane**.

## Architecture livrée

- **Scheduler** (`core/scheduler.py`) : planifie les jobs initiaux (discovery, page/product scraping, PDF).
- **Queue** (`core/queue.py`) : service de queue en mémoire avec retries, backoff exponentiel et DLQ.
- **Workers** (`jobs/workers.py`) :
  - discovery worker
  - page scraping worker
  - product scraping worker
  - pdf fetch worker
  - ocr worker
  - diff worker
- **Stockage brut** (`core/storage.py`) : stockage local de blobs (`data/blob`).
- **Stockage structuré** (`core/storage.py`) : JSONL pour `product_snapshot`, `pdf_snapshot`, `change_event`, `job_run` (`data/structured`).
- **Moteur de décision** (`decision_engine.py`) : calcule les fréquences optimales et génère `scrape_plan.json` + `worker_plan.json`.
- **Schéma SQL PostgreSQL** (`sql/schema.sql`) : tables `product_snapshot`, `pdf_snapshot`, `change_event`, `job_run`.

## Arborescence

```text
core/            # scheduler, queue, modèles, config, stockage
jobs/            # implémentations workers
sites/           # extension future pour extracteurs par site
configs/sites/   # configuration par site (8 fichiers)
scripts/         # scripts de simulation et notes de déploiement
sql/             # schéma PostgreSQL
tests/           # tests unitaires
decision_engine.py
```

## Exécution locale

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python scripts/run_campaign.py --cycles 4
python decision_engine.py
```

Résultats générés :
- `data/structured/job_run.jsonl`
- `data/structured/product_snapshot.jsonl`
- `data/structured/pdf_snapshot.jsonl`
- `data/structured/change_event.jsonl`
- `scrape_plan.json`
- `worker_plan.json`

## Campagne 14 jours (simulation)

Le scheduler peut être exécuté de façon répétée (cron/Timer) pendant 14 jours.
Ensuite, lancer `decision_engine.py` pour estimer les fréquences optimales selon :

- moyenne des intervalles de changement (
  \(\mu\)
)
- écart type (
  \(\sigma\)
)
- formule :
  \(I_{raw} = max(\mu - k\sigma, I_{min})\)
- poids méthode : HTML=1, API=1.2, HEADLESS=6, OCR=8
- arrondi vers {1h, 2h, 4h, 8h, 12h, 24h}

## Déploiement Azure (résumé)

Voir `scripts/bootstrap_azure.md` pour les étapes.

- Queue de prod: Azure Service Bus (une file par job + DLQ).
- Workers légers : Azure Container Apps autoscalées sur la longueur des files.
- Workers lourds (headless + OCR local) : VM Spot Scale Set.
- Scheduler : VM pay-as-you-go ou job planifié Container Apps.

## Remarques

- Le système est conçu pour être portable : local d'abord, puis substitution des adaptateurs (queue in-memory vers Service Bus/RabbitMQ, stockage local vers Blob+PostgreSQL).
- `sites/` est prêt pour intégrer les extracteurs spécifiques (CSS selectors / API endpoints / logique Playwright).
