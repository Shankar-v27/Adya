# Product Requirements Document (PRD)

## LinkedIn Mention Extraction System

## 1. Overview

The goal of this project is to build an automated system that extracts LinkedIn posts mentioning a specific individual and Adya AI within the last six months. The system will collect relevant metadata and generate a structured dataset that can be analyzed or shared with stakeholders.

---

## 2. Problem Statement

Monitoring mentions of founders and companies on LinkedIn is important for understanding brand presence, partnerships, and industry discussions. However, manually searching and tracking these mentions is time-consuming and inefficient.

This system will automate the process of identifying and collecting relevant LinkedIn posts.

---

## 3. Objectives

The system should:

- Extract LinkedIn posts mentioning Adya AI
- Extract posts mentioning the founder’s name
- Limit results to posts from the last 6 months
- Store results in structured format
- Generate a report of all collected posts

---

## 4. Key Features

### 4.1 Post Discovery

The system should automatically search and identify LinkedIn posts containing:

- "Adya AI"
- the founder’s name
- both together

### 4.2 Data Extraction

For each post, extract:

- Author Name
- Author Profile Link
- Post Content
- Post URL
- Post Date
- Number of Reactions
- Number of Comments
- Hashtags

### 4.3 Filtering

Posts must be filtered by:

- Date (last 6 months)
- Relevance of content
- Duplicate removal

### 4.4 Data Storage

The extracted data should be stored in:

- MongoDB
- PostgreSQL
- CSV or JSON file

### 4.5 Reporting

Generate a structured report containing:

- list of posts
- links to posts
- engagement metrics

Optional: A dashboard interface to view results.

---

## 5. System Architecture

The system will consist of:

1. Scraper Module
2. Processing Module
3. Storage Module
4. Reporting Module

---

## 6. Technology Stack

Backend:
Python

Scraping:
Playwright / Selenium / BeautifulSoup

Database:
MongoDB / PostgreSQL

Output:
CSV / JSON

Optional UI:
Streamlit / Flask / React

---

## 7. Output Format

Example JSON

{
  "author_name": "John Doe",
  "post_content": "Excited about the innovation happening at Adya AI",
  "post_url": "https://linkedin.com/...",
  "post_date": "2026-01-10",
  "reactions": 120,
  "comments": 15
}

---

## 8. Success Criteria

The system will be considered successful if:

- It extracts all relevant posts from the past 6 months
- The data is accurate and structured
- The system can be executed easily
- Results can be exported in a readable format

---

## 9. Deliverables

- Source Code
- Scraper Script
- Output Dataset
- Documentation