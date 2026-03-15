---
title: "econ-updater"
collection: projects
date: 2026-03-15
excerpt: "Automated weekly digest of economics working papers and conferences, scored for relevance using an LLM."
---

**econ-updater** sends me an automated weekly digest of new economics working papers and European conferences, scored for relevance to my research profile using an LLM.

Every Monday morning, it pulls new working papers from NBER, arXiv (econ), CEPR, IZA, and the Federal Reserve banks, plus conference listings from INOMICS, WikiCFP, conference-service.com, EEA/RES, and NBER. It then scores each paper against my research interests using Claude Haiku — a combination of keyword filtering and LLM-based relevance scoring — and delivers an HTML email with papers organised by relevance (Must Read / Should Read / Worth a Look) alongside upcoming conferences.

The whole thing runs on a GitHub Actions cron job with duplicate detection so I don't see the same papers twice.

If you're interested, feel free to fork the repository, update the research profile in `config.yaml` to match your own interests, and run it yourself — either locally or via GitHub Actions.

- [GitHub](https://github.com/swediot/econ-updater)
