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

## Recent publications

<ul>
  {% assign sorted_papers = site.publications | sort: 'date' | reverse %}
  {% for paper in sorted_papers limit:2 %}
    <li><a href="{{ paper.url }}">{{ paper.title }}</a><br><i>{{ paper.venue }} {{ paper.date | date: "%Y" }}</i></li>
  {% endfor %}
</ul> 
<p style="text-align: right;"><a href="/publications/">All papers &rarr;</a></p> 

## Recent blog posts

<ul>
  {% for post in site.posts limit:2 %}
    <li><a href="{{ post.url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>
<p style="text-align: right;"><a href="/blog/">All posts &rarr;</a></p>

<style>
.book-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 20px;
  margin-top: 20px;
  margin-bottom: 40px;
}
.book-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  font-size: 0.9em;
}
.book-item img {
  width: 100%;
  max-width: 130px;
  height: auto;
  aspect-ratio: 2/3;
  object-fit: cover;
  border-radius: 4px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.15);
  margin-bottom: 10px;
  transition: transform 0.2s;
}
.book-item img:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.book-item a {
  text-decoration: none;
  color: inherit;
  display: block;
}
.book-item p {
    margin: 0;
    line-height: 1.2;
}
</style> 
