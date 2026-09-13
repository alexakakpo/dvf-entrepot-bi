SHELL := /bin/bash
export DVF_DATA_DIR := $(CURDIR)/data
export DBT_PROFILES_DIR := $(CURDIR)/dbt

.DEFAULT_GOAL := help

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

download: ## Télécharge les fichiers DVF (Haute-Garonne, 2020-2025)
	python scripts/download.py

explore: ## Inspecte les fichiers téléchargés — À LANCER EN PREMIER
	python scripts/explore.py

dbt: ## Construit le modèle en étoile et lance les tests
	dbt build --project-dir dbt --profiles-dir dbt

export: ## Exporte le modèle en Parquet pour Power BI
	python scripts/export_powerbi.py --format parquet

export-csv: ## Exporte le modèle en CSV (secours)
	python scripts/export_powerbi.py --format csv

docs: ## Documentation dbt avec lineage cliquable
	dbt docs generate --project-dir dbt --profiles-dir dbt
	dbt docs serve --project-dir dbt --profiles-dir dbt

tout: download dbt export ## Chaîne complète

verifier: ## Quelques chiffres de contrôle sur l'entrepôt
	python scripts/verifier.py

clean: ## Supprime les artefacts générés (garde les CSV téléchargés)
	rm -rf dbt/target dbt/logs data/warehouse/*.duckdb powerbi/exports
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

.PHONY: help download explore dbt export export-csv docs tout verifier clean
