from openai import OpenAI

def generate_updated_prompt(user_prompt: str, selected_fields) -> str:
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key="your_api_key_here")

    enabled_params = [key for key, value in selected_fields.items() if value]
    param_list_str = ", ".join(enabled_params)

    message = f"""
        Rewrite the user's original prompt into a clear, concise, and structured instruction optimized for Firecrawl web scraping. Follow these guidelines precisely:

        Explicitly include all the required fields listed: {param_list_str}.

        If the original prompt specifies any numerical count, strictly preserve that exact count in the rewritten instruction.

        Format the final instruction so it can be directly executed by Firecrawl.dev to extract data efficiently from the internet, avoiding ambiguity. Ensure that no field remains empty; provide meaningful values for each required field.

        User's Original Prompt:
        {user_prompt}
    """

    completion = client.chat.completions.create(
        extra_headers={"HTTP-Referer": "https://your-site-url.com", "X-Title": "Firecrawl Lead Extractor"},
        model="mistral/ministral-8b",
        messages=[{"role": "user", "content": message}]
    )
    return completion.choices[0].message.content
