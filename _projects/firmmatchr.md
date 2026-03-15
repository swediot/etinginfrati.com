---
title: "firmmatchr"
collection: projects
date: 2025-10-10
excerpt: "An R package for matching messy company names to official firm registries."
---

**firmmatchr** is an R package for linking messy, user-generated company names to official firm registries like [Zefix](https://www.zefix.ch/en/search/entity/welcome) and Orbis. It implements a "waterfall" matching strategy — moving from exact matches after normalization, through token-based and fuzzy string matching, to LLM-assisted verification for uncertain cases. The normalization is tuned for the DACH market (umlauts, German legal forms like GmbH/AG, etc.) but the logic generalises to other countries.

I go into much more detail on the approach in the [blog post](/company-matching/).

- [GitHub](https://github.com/swediot/firmmatchr)
- [CRAN](https://cran.r-project.org/package=firmmatchr)
