# Web Data Scrape

Web Data Scrape is a microservice designed for efficiently scraping data from web pages, including static and JavaScript-rendered content. Built using Python, it utilizes libraries like `requests` for static content and `Playwright` for handling dynamic web applications. This project aims to provide an easy-to-use API for fetching and processing data from various websites.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## Features

- Fetch static web content using `requests`.
- Fetch dynamic content rendered by JavaScript using `Playwright`.
- Support for optional proxy configuration for scraping.
- Ability to parse HTML content and extract specific elements using CSS selectors.

## Getting Started

To get started with Web Data Scrape, clone the repository and install the necessary dependencies.

### Prerequisites

Make sure you have the following installed:

- Python 3.8 or higher
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/tancincozach/web-data-scrape.git
   cd web-data-scrape
