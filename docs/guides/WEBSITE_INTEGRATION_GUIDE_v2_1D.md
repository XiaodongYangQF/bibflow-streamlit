# BibFlow Version 2.1D — Website Integration Guide

This step adds BibFlow to your personal website's **Interactive Tools** page.

## 1. Files to edit

Most likely files:

```text
_pages/interactive-tools/index.md
assets/css/interactive-tools.css
```

Your website may use:

```text
_pages/interactive-tools/index.md
```

as the main Interactive Tools page.

## 2. Add the BibFlow card

Open:

```bash
code _pages/interactive-tools/index.md
```

Find:

```html
<section class="tools-grid">
```

Paste the BibFlow card inside this section.

Use the file:

```text
BIBFLOW_CARD_v2_1D.html
```

## 3. Replace the Streamlit URL

In the card, replace:

```text
https://YOUR-BIBFLOW-STREAMLIT-APP-URL
```

with your deployed Streamlit app URL.

Before deployment, you can temporarily use the GitHub repo URL, for example:

```text
https://github.com/YOUR-USERNAME/bibflow-streamlit
```

## 4. Optional CSS polish

Open:

```bash
code assets/css/interactive-tools.css
```

Append the contents of:

```text
INTERACTIVE_TOOLS_CSS_ADDITIONS_v2_1D.css
```

This adds:

- small metadata line under each card
- featured style for BibFlow
- dark-mode friendly styling

## 5. Preview locally

Run your Jekyll site locally:

```bash
bundle exec jekyll serve
```

Then open:

```text
http://127.0.0.1:4000/interactive-tools/
```

## 6. Commit

```bash
git status
git add _pages/interactive-tools/index.md assets/css/interactive-tools.css
git commit -m "Add BibFlow to Interactive Tools page"
git push
```

## Suggested card text

Title:

```text
BibFlow
```

Description:

```text
A Streamlit app for cleaning BibTeX references, managing research libraries, matching AJG/ABS-style journal rankings, and tracking literature-review progress.
```

Tags:

```text
Streamlit · BibTeX · AJG/ABS · FT50 · Literature Review
```

## Note

If you have not deployed BibFlow yet, keep the link pointing to the GitHub repository first.
After Streamlit deployment, replace it with the app URL.
