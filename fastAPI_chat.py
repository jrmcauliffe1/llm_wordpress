from fastapi import FastAPI, HTTPException, Request
import os
from openai import OpenAI
from dotenv import load_dotenv
import requests

load_dotenv()  # take environment variables from .env.

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

app = FastAPI()

@app.post("/generate-and-post-poem")
async def generate_and_post_poem(request: Request, title: str, author: str, date: str, format: str):
    try:
        # Extract user content from the request body
        data = await request.json()
        user_content = data.get("user_content")

        # Send a request to the OpenAI API to generate a poem
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a author writing an article for an online blog."},
                {"role": "user", "content": user_content}
            ]
        )

        # Check if the request was successful
        if completion.choices[0].message:
            poem = completion.choices[0].message

            # Prepare data for creating a post on WordPress
            post_data = {
                "title": title,
                "content": poem,
                "author": author,
                "date": date,
                "format": format
            }

            # Send a request to the WordPress API to create a post
            response = requests.post(
                "https://public-api.wordpress.com/rest/v1.1/sites/tipstricksandimmortaljellyfish.wordpress.com/posts/new",
                json=post_data,
                auth=(os.environ.get("WORDPRESS_USERNAME"), os.environ.get("WORDPRESS_PASSWORD"))
            )

            # Check if the request was successful
            if response.status_code == 201:
                # Return the response from WordPress API
                return {"poem": poem, "wordpress_response": response.json()}
            else:
                # If the request was not successful, raise an HTTPException with appropriate status code and message
                raise HTTPException(status_code=response.status_code, detail="Failed to create post on WordPress")
        else:
            # If the request to ChatGPT was not successful, raise an HTTPException with appropriate status code and message
            raise HTTPException(status_code=500, detail="Failed to generate poem from ChatGPT")
    except Exception as e:
        # If an exception occurs during the request, raise an HTTPException with status code 500 and error message
        raise HTTPException(status_code=500, detail=str(e))
