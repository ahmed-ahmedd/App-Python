User Input : The user enters a product name, its price, and the currency (USD or EGP).
Price Comparison : The app searches for the product on several websites and collects their prices.
Results Display : It shows the user how the entered price compares to prices from other sellers.
Export Option : Users can export the results to an Excel file for further analysis.

# Stages of Implementation
Stage 1: Understanding the Problem
Goal : Build a tool to help users compare product prices across different websites.
Why : To make informed decisions about pricing and stay competitive in the market.
Key Features :

Search products on Amazon, eBay, Walmart, and Jumia.


Compare prices in USD and EGP.
Export results for reporting.


Stage 2: Planning the Solution
Approach :
Use web scraping to extract product data from websites.
Convert all prices to USD for consistent comparison.
Display results in a user-friendly web interface.



Tools Used :
Flask : A Python framework to create the web application.
BeautifulSoup : A library to parse HTML and extract data from websites.
Requests : A library to send HTTP requests to websites.
Pandas : A library to handle data and export it to Excel.


-----


Stage 3: Building the Application
Scraping Data :


Wrote functions to scrape product details (title, price, URL) from Amazon, eBay, Walmart, and Jumia.


Handled website structure changes by using updated CSS selectors .


Converted prices from EGP to USD for consistent comparison.

![Screenshot 2025-04-29 162047](https://github.com/user-attachments/assets/9aff064e-b27f-4c1e-8d7c-86d7d7ec4ef6)
![Screenshot 2025-04-29 162233](https://github.com/user-attachments/assets/7e885ded-a40a-4889-805c-ec1329287dd5)
![Screenshot 2025-04-29 162443](https://github.com/user-attachments/assets/35b32d58-afb4-4053-8c33-4eff8c00a9b8)





