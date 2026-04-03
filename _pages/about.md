---
permalink: /
title: "About"
excerpt: "About me"
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

I'm an early career researcher in labour econonics with a focus on non-wage amenities and compensation inequality. My interest also include trade and gender economics. I aim to shed light on these interconnected fields, providing valuable insights into their real-world impact. Feel free to contact me at [giulian@etinginfrati.com](mailto:giulian@etinginfrati.com).

<div style="margin-top: 40px;"></div>

## Recent research

<ul>
  {% assign sorted_papers = site.research | sort: 'date' | reverse %}
  {% for paper in sorted_papers limit:2 %}
    <li><a href="{{ paper.url }}">{{ paper.title }}</a><br><i>{{ paper.venue }} ({{ paper.date | date: "%Y" }})</i></li>
  {% endfor %}
</ul> 
<p style="text-align: right;"><a href="/research/">All papers &rarr;</a></p> 

## Recent blog posts

<ul>
  {% for post in site.posts limit:2 %}
    <li><a href="{{ post.url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>
<p style="text-align: right;"><a href="/blog/">All posts &rarr;</a></p>

