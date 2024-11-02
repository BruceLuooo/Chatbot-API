# Chatbot Application

## Table of Contents

- [About](#about)
- [How It Works](#how-it-works)
- [Issues and How They Were Resolved](#issues-and-how-they-were-resolved)
- [Setup Guide](#setup-guide)
- [Prerequisites](#prerequisites)

---

## About

This application is a backend server that provides a powerful API for generating responses to user requests using Google's advanced language model, Gemini. The application utilizes a search engine called Typesense to find videos within its database. By intelligently interpreting user queries, the server formats requests into usable JSON objects, allowing for seamless interaction. Beyond video searches, the application can also handle general inquiries, making it versatile and user-friendly.


## How It Works

At its core, the application leverages Google Cloud Platform's Gemini 1.0 Pro to process user requests. When a user submits a query, it is sent to Gemini along with a pre-written prompt designed to determine the intent behind the request. This process generates a JSON object containing the following fields:

```
{
  "intent": "string",
  "summary": "string",
  "response": "string"
}
```

Intent: This field identifies the action to be performed, whether it's retrieving videos from the database or providing a general response.
Summary: This maintains a record of the current chat history, enabling Gemini to sustain context throughout multiple interactions.
Response: This contains the primary output returned by Gemini based on the user's input.

If the identified intent is to find a video, an additional prompt is dispatched to Gemini, to de-structure the user's request into another JSON object. This object contains specific criteria to query the database via Typesense:

```
{
  "topic": "string",
  "view_count": "string",
  "release_date_before": "string",
  "release_date_after": "string"
}
```

This dual-layer approach not only enhances the accuracy of search results but also ensures that the application can dynamically adapt to varying user inquiries while maintaining a rich conversational context.


## Issues and How They Were Resolved

During the development of the application, I was faced with several challenges:

### 1. Handling Gemini's String Responses

**Issue**: Gemini's responses are returned as a string, which meant converting the string into a Python object to effectively utilize the data in the methods. Notably, the JSON data returned by Gemini always begins and ends with triple backticks.

**Resolution**: To extract the relevant JSON data, I implemented a Regex pattern to search for text between these triple backticks. This allowed me to isolate the JSON string. Once extracted, I used Python's `json.loads()` method to convert the string into a usable Python object, facilitating seamless data manipulation within our application.

### 2. Date Format Discrepancies

**Issue**: When querying videos based on date parameters ("release_date_before" and "release_date_after"), Gemini had difficulty returning the correct UNIX timestamps, which was how I was storing the release date of the videos in my datdabase. The reason why I was storing the release date as a UNIX timestamp was because querying UNIX time structure is quicker compared to ISO timestamps.

**Resolution**: To ensure accuracy, I instructed Gemini to return dates in ISO format. Subsequently, I created a dedicated method for converting these ISO timestamps into UNIX timestamps. This conversion method ensures that our database queries remain efficient while maintaining the integrity of the date data returned from Gemini.

These solutions not only resolved the immediate issues but also enhanced the overall robustness of the application, allowing for smoother interactions and more reliable data processing.


## Setup Guide

Follow these steps to set up the project on your local machine:

### Django Project Setup
1. Clone this repository
2. Create a virtual environment
    > python -m venv .venv
3. Activate the virtual environment (Windows PowerShell)
    > .venv\Scripts\activate
4. Install the required packages
    > pip install -r requirements.txt
5. Migration
    > python manage.py migrate
6. Run the server for testing (May not work without setting up typesense, see instructions below)
    > python manage.py runserver
7. Run the tests
    > python manage.py test
8. Note: Whenever there are changes in the model (i.e. added new fields for the video model), make sure to run this and then perform step 1:
    > python manage.py makemigrations

## Typesense Installation
1. To run the project, you must have typesense running locally. 
2. Follow this guide: https://typesense.org/docs/guide/install-typesense.html
3. After installation, you should be able to run this on your terminal:
   - ```curl http://localhost:8108/health```
   - And get the response: {"ok":true}
4. Make sure that the settings from your typesense config file matches the config.ini file in the project, especially the API key.
5. Now before you run the backend server, you must run the following commands:
   - ```python manage.py typesense_init```
   - ```python manage.py typesense_index```
6. Run the backend server as expected:
   - ```python manage.py runserver```
   

### Prerequisites

1. You must have a GCP account and access to GCP CLI. Enable GCP Vertex AI and select Gemini 1.0 pro, which is what is being used
2. Find a sample dataset which you can store as JSON documents in Typesense so that you can utilize the search engine


