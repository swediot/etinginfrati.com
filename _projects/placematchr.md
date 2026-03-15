---
title: "placematchr"
collection: projects
date: 2026-01-05
excerpt: "An R package for mapping messy user-generated locations to official NUTS regions."
---

**placematchr** is an R package for mapping messy, user-generated location strings to official [NUTS](https://ec.europa.eu/eurostat/web/nuts) regions. It handles the usual problems — ambiguous city names ("Frankfurt" could be Main or Oder), neighborhood-level inputs that need rolling up to their parent city, vague descriptions, and foreign locations that should be filtered out. Under the hood it uses aggressive regex normalization followed by a hierarchical lookup against both NUTS3 region names and the LAU (Local Administrative Units) dataset, with a fuzzy matching step for typos.

I go into much more detail on the approach in the [blog post](/place-matching/).

- [GitHub](https://github.com/swediot/placematchr)
- [CRAN](https://cran.r-project.org/package=placematchr)
