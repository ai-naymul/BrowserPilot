/**
 * Scrape templates — one-click starting points.
 *
 * A template pins only INPUTS (which site + what to ask), never the output
 * dashboard. The same generalized LLM render engine builds the UI at run time,
 * so templates give reliable, known-good demos without any per-template
 * hardcoding. Adding a template is a data change — a great "good first issue".
 */

export interface ScrapeTemplate {
  slug: string;        // stable id, also the future /templates/:slug SEO route
  emoji: string;
  title: string;
  oneliner: string;    // the outcome, in plain language
  category: string;
  urls: string[];      // empty = "bring your own URLs" (fills the form, waits)
  prompt: string;
}

export const SCRAPE_TEMPLATES: ScrapeTemplate[] = [
  {
    slug: "books-price-rating",
    emoji: "📚",
    title: "Books: price & rating",
    oneliner: "Turn a catalog into a price + rating dashboard",
    category: "Comparison",
    urls: ["https://books.toscrape.com/"],
    prompt:
      "Compare these books by price and rating and highlight the best value picks",
  },
  {
    slug: "hacker-news-jobs",
    emoji: "💼",
    title: "Who's hiring",
    oneliner: "A job board as a scannable dashboard",
    category: "Jobs",
    urls: ["https://news.ycombinator.com/jobs"],
    prompt:
      "Show these job postings as a dashboard I can scan by company and role",
  },
  {
    slug: "github-trending",
    emoji: "⭐",
    title: "GitHub trending",
    oneliner: "Today's trending repos, ranked and charted",
    category: "Dev",
    urls: ["https://github.com/trending"],
    prompt:
      "Compare today's trending repositories by stars, and group by language",
  },
  {
    slug: "hn-front-page",
    emoji: "📰",
    title: "Hacker News front page",
    oneliner: "The front page as a sortable dashboard",
    category: "News",
    urls: ["https://news.ycombinator.com/"],
    prompt:
      "Turn the Hacker News front page into a dashboard sorted by points",
  },
  {
    slug: "product-hunt-today",
    emoji: "🚀",
    title: "Product Hunt today",
    oneliner: "Today's launches, ranked by upvotes",
    category: "Products",
    urls: ["https://www.producthunt.com/"],
    prompt: "Show today's Product Hunt launches ranked by upvotes",
  },
  {
    slug: "price-comparison",
    emoji: "🛒",
    title: "Compare product prices",
    oneliner: "Paste a few product pages → best-value dashboard",
    category: "Comparison",
    urls: [], // bring-your-own: fills the prompt, waits for the user's URLs
    prompt:
      "Compare these products by price, rating and availability to find the best value",
  },
];
