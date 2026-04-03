---
permalink: /reading/
title: "Reading"
author_profile: true
---

I read a lot, usually fiction but not always. Always happy to talk about books and get recommendations. I have read {{ site.data.books.year_count }} book{% if site.data.books.year_count != '1' %}s{% endif %} this year and have {% include format_number.html number=site.data.books.to_read_count %} books in my [to-read pile](https://app.thestorygraph.com/to-read/swediot). For the complete list, see my StoryGraph [profile](https://app.thestorygraph.com/profile/swediot). I get most of my books from [Vastela Books](https://www.vastelabooks.com/) in Zurich.

{% if site.data.books.currently_reading and site.data.books.currently_reading.size > 0 %}
## Currently Reading

<div class="book-grid">
  {% for book in site.data.books.currently_reading %}
    <div class="book-item">
      <a href="{{ book.url }}">
        <img src="{{ book.image }}" alt="{{ book.title }}">
      </a>
      <p><strong>{{ book.title }}</strong><br>
      <em>{{ book.author }}</em></p>
    </div>
  {% endfor %}
</div>
{% endif %}

## Recently Read

<div class="book-grid">
  {% for book in site.data.books.recently_read %}
    <div class="book-item">
      <a href="{{ book.url }}">
        <img src="{{ book.image }}" alt="{{ book.title }}">
      </a>
      <p><strong>{{ book.title }}</strong><br>
      <em>{{ book.author }}</em></p>
    </div>
  {% endfor %}
</div>

<div style="text-align: right;">
  <a href="https://app.thestorygraph.com/books-read/swediot" class="btn btn--info">More recently read &rarr;</a>
</div>

## Five Star Reads

<div class="book-grid">
  {% for book in site.data.books.recent_five_star %}
    <div class="book-item">
      <a href="{{ book.url }}">
        <img src="{{ book.image }}" alt="{{ book.title }}">
      </a>
      <p><strong>{{ book.title }}</strong><br>
      <em>{{ book.author }}</em></p>
    </div>
  {% endfor %}
</div>

<div style="text-align: right;">
  <a href="https://app.thestorygraph.com/five_star_reads/swediot" class="btn btn--info">More five star reads &rarr;</a>
</div>

