---
permalink: /reading/
title: "Reading"
author_profile: true
---

{% if site.data.books.year_count %}
I read a lot, usually fiction but not always. Always happy to talk about books and get recommendations. So far, I have read {{ site.data.books.year_count }} books this year. For the complete list, see my StoryGraph [profile](https://app.thestorygraph.com/profile/swediot).
{% endif %}

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

## Recent Five Star Reads

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

<style>
.book-grid {
  display: grid;
   /* Responsive grid: min 150px, fill available space */
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
  max-width: 130px; /* Limit max size */
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
