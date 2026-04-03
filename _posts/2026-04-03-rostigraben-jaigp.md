---
title: 'Writing an Economics Paper with Claude: An Experiment in AI-Generated Research'
date: 2026-04-03
tags:
author: Giulian Etingin-Frati
---

![Diagram of AI-assisted research process](/files/image-rostigraben.png)

Last week, Nicolas Marti and I submitted our paper, [*The Cultural Cost of Overwork: Evidence from Switzerland's Röstigraben*](/files/2026%20-%20Rostigraben.pdf), to the [Journal for AI Generated Papers](https://jaigp.org/) (JAIGP). The paper was written almost entirely with Claude and Gemini. This post explains what JAIGP is, how we used AI throughout the research process, and what we learned along the way.

## What is the Journal for AI Generated Papers?

JAIGP is a new open-access, multidisciplinary journal created by [César A. Hidalgo](https://chidalgo.com/) (Toulouse School of Economics). Its premise is simple: AI systems are the authors, and humans are the prompters. Rather than treating AI involvement as something to hide or disclaim, JAIGP makes it the entire point. The journal exists as an open experiment to understand what AI-generated research looks like, where it works, and where it falls short. JAIGP is designed to find out by creating a structured space for this kind of work rather than leaving it in a gray zone across traditional journals.

### The Review Process

JAIGP uses a multi-stage pipeline that is itself partly AI-powered:

1. **Screening.** Every submission is automatically screened by AI for basic academic substance.
2. **Endorsement.** A verified ORCID scholar endorses the paper, signaling that it merits deeper review.
3. **AI Review.** Multiple AI reviewers (via [Reviewer3.com](https://reviewer3.com/)) evaluate the paper. Authors can revise and respond for up to three rounds.
4. **Community Comments.** The paper is publicly visible throughout, and anyone can comment.

A formal human peer review stage will also be intorudced at some point in the future. The entire process is transparent: all reviews and revisions are visible to the community.

## The Paper: Culture and Overwork at the Röstigraben

The research question is straightforward: does culture shape how burdensome overtime feels? Switzerland provides a natural experiment. French- and German-speaking workers share the same federal labor laws, tax structures, and macroeconomic environment, but inherit very different attitudes toward work and leisure. The linguistic border, the *Röstigraben*, runs through several cantons, creating a sharp cultural discontinuity without an institutional one.

Using 25 waves of the [Swiss Household Panel](https://forscenter.ch/projects/swiss-household-panel/) (1999–2023), we show that each extra hour beyond the contract raises work-life interference significantly more for German-speaking workers than for French-speaking workers. The effect represents a 152% amplification of the French-speaking baseline. German-speaking norms, which place a premium on strict boundary compliance between work and leisure (the *Feierabend* principle), generate a higher psychological penalty per hour of contract violation.

Three findings stood out:

* **The cultural penalty is concentrated among part-time workers.** Part-time contracts more explicitly mark the work-leisure boundary. For full-time men, the cultural interaction is near zero.

* **The effect is specific to contractual hours.** When we measure the hours gap relative to *habitual* hours instead of *contractual* hours, the cultural amplification disappears entirely. This is consistent with the contract serving as a reference point whose psychological prominence is culturally modulated.

* **Despite higher psychological costs, German-speaking workers do not adjust their labor supply differently.** They do not correct overwork episodes faster, do not bunch more tightly at contractual hours, and do not switch jobs at higher rates. The cultural penalty is real but does not translate into observable behavioral differences at the annual horizon.

## How We Used AI

### Hypothesis Development and Literature Review

We started with a broad question about cultural differences in labor supply and pointed Claude at the existing Röstigraben literature: Eugster et al. (2017) on unemployment duration, Steinhauer (2018) on female labor-force participation, Brügger et al. (2009) on the linguistic border. The AI was useful here not for discovering papers we did not know about, but for rapidly synthesizing connections across literatures. The link between reference-dependent preferences (Kőszegi and Rabin, 2006) and contractual salience, which became the paper's main theoretical mechanism, emerged from an iterative conversation rather than from reading any single paper.

### Empirical Analysis

The coding was done primarily with Claude and the Swiss Household Panel documentation. Claude wrote the data cleaning pipeline, the panel regressions, and the various robustness checks. We reviewed every specification, and all final methodological decisions were made by us. 

### Drafting and Revision

The first full draft was produced by Claude based on our outlined structure and the regression output. The revision process was mostly about cutting rather than adding, removing the filler and sharpening the claims. We also used AI-generated referee reports (via Refine.ink and Reviewer3.com) to identify weaknesses before submission.  The AI referees pushed us on whether the results could be explained by differential compensation rather than cultural norms (we added an income analysis). 

## Why This Matters

This is an experiment. We do not know whether AI-generated research will eventually meet the standards of top field journals, or whether it will remain a useful but limited tool for exploratory work and side projects. JAIGP provides the infrastructure to find out. For researchers, the practical takeaway is that AI collaboration can meaningfully accelerate the research process, particularly for data-heavy empirical work with well-defined identification strategies. 
