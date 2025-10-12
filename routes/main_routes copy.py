from flask import Blueprint, render_template, request,jsonify
from Utils.Packages import *
from Utils.Common import *
from CONSTANT import *
from models.Models import *
project_id = os.getenv("GCP_PROJECT_ID")
dataset = os.getenv("BQ_DATASET")
table = os.getenv("BQ_TABLE")
credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# Create a Blueprint instance
main_bp = Blueprint('main', __name__)
engine=engine = get_engine(
    "bigquery",
    credentials_path=credentials
)



db = LainChain_engine(credentials_path=credentials, 
                      include_tables=Include_tables,
                      engine=engine)


llm = ChatGoogleGenerativeAI(model=os.getenv("MODEL_NAME"),
                              google_api_key=os.getenv("GOOGLE_API_KEY"),
                                temperature=0)
llm_corr=ChatGoogleGenerativeAI(model=os.getenv("MODEL_NAME"),
                              google_api_key=os.getenv("GOOGLE_API_KEY"),
                                temperature=0)

chain = create_sql_query_chain(llm, db)
last_dataframe = None  
# @main_bp.route('/', methods=['GET', 'POST'])
# def home():
#     global last_dataframe
#     """This route handles both the input form and displaying the results."""
#     if request.method == 'POST':
#         user_input = request.form.get('user_input')
#         result = chain.invoke({"question": user_input})
#         corrected_sql = correct_sql_query(result, llm_corrector=llm_corr)
#         data = get_data(query=corrected_sql, engine=engine, db_type="bigquery", credentials_path=credentials)
#         last_dataframe=data
#         # Convert DataFrame to HTML
        

# # Convert float columns to int where applicable
#         # Apply formatter to numeric columns except 'year'
#         for col in data.select_dtypes(include='number').columns:
#             if col != "year":
#                 data[col] = data[col].map(number_formate)
#         html_table = data.to_html(
#         index=False,
#         classes="dataframe-table",
#         escape=False  # keeps commas as-is
#         )

#         # Pass the HTML string to the template
#         return render_template('display.html', user_input=html_table)
    
#     return render_template('index.html')


from flask import session

def process_user_input(user_input):
    # 1. Get LLM SQL suggestion
    result = chain.invoke({"question": user_input})
    
    # 2. Correct SQL
    corrected_sql = correct_sql_query(result, llm_corrector=llm_corr)
    
    # 3. Get DataFrame
    data = get_data(
        query=corrected_sql, 
        engine=engine, 
        db_type="bigquery", 
        credentials_path=credentials
    )
    return corrected_sql, data


def format_dataframe(df):
    for col in df.select_dtypes(include='number').columns:
        if col != "year":
            df[col] = df[col].apply(number_formate)
    return df











# @main_bp.route('/chat', methods=['GET', 'POST'])d
# def chat():
#     global last_dataframe

#     if "chat_history" not in session:
#         session["chat_history"] = []

#     if request.method == 'POST':
#         user_input = request.form.get('user_input')

#         # Save user query
#         session["chat_history"].append({"role": "user", "content": user_input})
#         user_input = chain.invoke({"question": user_input})
#         # ✅ Check query validity
#         if is_valid_sql(user_input):
#             corrected_sql = user_input  # already valid
#         else:
#             corrected_sql =  correct_sql_query(user_input, llm_corrector=llm_corr)#llm_corr(user_input)  # use LLM to fix

#         # Process SQL + Data
#         corrected_sql, data = process_user_input(corrected_sql)
#         data = format_dataframe(data)

#         # Save latest DataFrame (not in session!)
#         last_dataframe = data

#         # Save only text in history
#         session["chat_history"].append({"role": "ai", "content": "Here’s your table result:"})
#         session.modified = True

#         return render_template(
#             'form.html',
#             chat_history=session["chat_history"],
#             last_dataframe=data.to_html(index=False, classes="dataframe-table", escape=False)
#         )

#     return render_template('form.html', chat_history=session.get("chat_history", []))



# @main_bp.route('/chat', methods=['GET', 'POST'])
# def chat():
#     global last_dataframe

#     if "chat_history" not in session:
#         session["chat_history"] = []

#     if request.method == 'POST':
#         user_input = request.form.get('user_input')

#         # Save user query
#         session["chat_history"].append({"role": "user", "content": user_input})

#         # Process AI + SQL + Data
#         corrected_sql, data = process_user_input(user_input)
#         data = format_dataframe(data)

#         # Save latest DataFrame (not in session!)
#         last_dataframe = data

#         # Save only text in history (fast)
#         session["chat_history"].append({"role": "ai", "content": "Here’s your table result:"})
#         session.modified = True

#         return render_template(
#             'form.html',
#             chat_history=session["chat_history"],
#             last_dataframe=data.to_html(index=False, classes="dataframe-table", escape=False)
#         )

#     return render_template('form.html', chat_history=session.get("chat_history", []))

import pandas as pd
import pandas as pd
import re

# def get_llm_generated_html(data: pd.DataFrame, llm_chain):
#     """
#     Generates an HTML representation of a DataFrame using an LLM,
#     allowing the LLM to choose between a table or a paragraph.
    
#     Args:
#         data: The pandas DataFrame to be converted.
#         llm_chain: The LLM chain object to invoke.
        
#     Returns:
#         A string containing the generated HTML.
#     """
#     if data.empty:
#         return "<p>No data to display.</p>"

#     # Convert the DataFrame to a JSON string
#     data_json = data.to_json(orient='records', date_format='iso')

#     # Use the flexible prompt to let the LLM decide the best format
#     llm_html_prompt = f"""
# You are a data presentation expert. Analyze the following JSON data and determine the most effective way to represent it for a user.
# **Instructions:**
# - If the data is best suited for a table (e.g., structured rows and columns), generate a clean, well-structured HTML table. The table should have the class "dataframe-table" for styling.
# - If the data is better represented as a paragraph or summary (e.g., key metrics or a single finding), generate a concise and descriptive paragraph.
# 1.  **Analyze the Data**: Carefully examine the JSON keys to determine the most appropriate and user-friendly column headers.
# 2.  **Generate `<thead>`**: Create the table header (`<thead>`) using the inferred column names.
# 3.  **Generate `<tbody>`**: Create the table body (`<tbody>`) and populate it with the data from the JSON, row by row.
# 4.  **Format**: The table must have the class `"dataframe-table"`. **Do not include any code block indicators like ```html or any extra text or explanations.**
# 5.  **Output**: Return only the complete HTML `<table>...</table>` block.
# **JSON Data:**
# {data_json}
# """

#     # Invoke the LLM with the prompt
#     llm_response = llm_chain.invoke({"question": llm_html_prompt})
    
#     # Use regex to remove any code block indicators from the beginning and end of the string
#     clean_html = re.sub(r'```(?:html)?\s*', '', llm_response.strip(), count=1)
#     clean_html = re.sub(r'```\s*$', '', clean_html, count=1)

#     return clean_html

import pandas as pd
import re
from langchain_google_genai import ChatGoogleGenerativeAI
import os

def     get_llm_generated_html(data: pd.DataFrame, llm_model):
    """
    Generates an HTML representation of a DataFrame using an LLM,
    allowing the LLM to choose between a table or a paragraph.
    
    Args:
        data: The pandas DataFrame to be converted.
        llm_model: The LLM model object to invoke.
        
    Returns:
        A string containing the generated HTML.
    """
    if data.empty:
        return "<p>No data to display.</p>"

    # Convert the DataFrame to a JSON string
    data_json = data.to_json(orient='records', date_format='iso')

    # Use the flexible prompt to let the LLM decide the best format
    llm_html_prompt = f"""
You are a data presentation expert. Analyze the following JSON data and present the information in a way that feels natural, conversational, and user-friendly — similar to how ChatGPT would explain insights.

Instructions:

Examine the JSON keys and values to identify meaningful insights.

Present the data in polished HTML that resembles a ChatGPT-style response — clear, approachable, and easy to read.

Use semantic HTML such as <p>, <ul>, <li>, <strong>, or styled <div> blocks for structure. If needed, you may use a simple table, but the main focus should be on readability and insight rather than raw data.

Summarize highlights, trends, or patterns instead of listing every detail unless necessary.

Do not include code block indicators, explanations, or extra text outside the HTML. Return only the HTML content.

Output: A clean, user-friendly HTML summary that looks like it could be part of a ChatGPT conversation.
{data_json}
"""
    
    # Invoke the LLM with the prompt
    # CORRECTED: Use the provided llm_model argument directly
    # llm_response = llm_model.invoke({"question": llm_html_prompt})
    llm_response = llm_model.invoke(llm_html_prompt)
    # Use regex to remove any code block indicators from the beginning and end of the string
    # clean_html = re.sub(r'```(?:html)?\s*', '', llm_response.strip(), count=1)
    # clean_html = re.sub(r'```\s*$', '', clean_html, count=1)

    return llm_response

#---it is wroing fine--#
# @main_bp.route('/chat', methods=['GET', 'POST'])
# def chat():
#     global last_dataframe

#     if "chat_history" not in session:
#         session["chat_history"] = []  # initialize history

#     if request.method == 'POST':
#         user_input = request.form.get('user_input')

#         # Save user input into history
#         session["chat_history"].append({"role": "user", "content": user_input})

#         # AI response
#         result = chain.invoke({"question": user_input})
#         result_querry=correct_and_format_sql_no_llm(result)
    
#         if is_valid_sql(result_querry):
#             data = get_data(query=result_querry, engine=engine, db_type="mysql", credentials_path=credentials)
#         else:
           
#             corrected_sql = correct_sql_query(result, llm_corrector=llm_corr)
#             data = get_data(query=corrected_sql, engine=engine, db_type="mysql", credentials_path=credentials)
#         last_dataframe = data

#         # Format numeric columns except year
#         for col in data.select_dtypes(include='number').columns:
#             if col != "year":
#                 data[col] = data[col].map(number_formate)

#         html_table = data.to_html(
#             index=False,
#             classes="dataframe-table",
#             escape=False
#         )

#         # Save AI response in history
#         session["chat_history"].append({"role": "ai", "content": html_table})

#         # Persist session
#         session.modified = True

#         return render_template('form.html', chat_history=session["chat_history"])

#     return render_template('form.html')

# @main_bp.route('/chat', methods=['GET', 'POST'])
# def chat():
#     global last_dataframe

#     if "chat_history" not in session:
#         session["chat_history"] = []

#     if request.method == 'POST':
#         user_input = request.form.get('user_input')
#         session["chat_history"].append({"role": "user", "content": user_input})

#         result = chain.invoke({"question": user_input})
#         result_querry = correct_and_format_sql_no_llm(result)

#         if is_valid_sql(result_querry):
#             data = get_data(query=result_querry, engine=engine, db_type="mysql", credentials_path=credentials)
                  
#         else:

#             corrected_sql = correct_sql_query(result, llm_corrector=llm_corr)
#             corrected_sql=correct_and_format_sql_no_llm(corrected_sql)
#             print("in-valid",result_querry)
#             data = get_data(query=corrected_sql, engine=engine, db_type="mysql", credentials_path=credentials)
#         for col in data.select_dtypes(include='number').columns:
#             if col != "year":
#                 data[col] = data[col].map(number_formate)
#         last_dataframe = data
        
#         # Call the new function to generate the HTML
#         # html_table = get_llm_generated_html(data=last_dataframe, llm_model=chain)
#         html_table = get_llm_generated_html(data=data, llm_model=llm_corr)
#         print(html_table.content)
#         # Save AI response in history
       
#         session["chat_history"].append({"role": "ai", "content": html_table.content})

#         session.modified = True
#         return render_template('form.html', chat_history=session["chat_history"])

#     return render_template('form.html')

#it is working fine too

# from flask import redirect, url_for
# @main_bp.route('/chat', methods=['GET', 'POST'])
# def chat():
#     global last_dataframe

#     if "chat_history" not in session:
#         session["chat_history"] = []

#     if request.method == 'POST':
#         user_input = request.form.get('user_input')
#         session["chat_history"].append({"role": "user", "content": user_input})

#         result = chain.invoke({"question": user_input})
#         result_query = correct_and_format_sql_no_llm(result)

#         # Run SQL query
#         if is_valid_sql(result_query):
#             data = get_data(query=result_query, engine=engine, db_type="mysql", credentials_path=credentials)
#         else:
#             corrected_sql = correct_sql_query(result, llm_corrector=llm_corr)
#             corrected_sql = correct_and_format_sql_no_llm(corrected_sql)      #recrusive /count 
#                                                                               #global cacha 
#             print("Invalid SQL, corrected:", result_query)
#             data = get_data(query=corrected_sql, engine=engine, db_type="mysql", credentials_path=credentials)

#         # Format numeric columns
#         for col in data.select_dtypes(include='number').columns:
#             if col != "year":
#                 data[col] = data[col].map(number_formate)

#         last_dataframe = data   #| after this it will go to fronted  

#         # Decide response type
#         if len(data) < 10:
#             # Generate HTML using LLM
#             html_table = get_llm_generated_html(data=data, llm_model=llm_corr)
#             print(html_table.content)

#             session["chat_history"].append({"role": "ai", "content": html_table.content})
#         else:
#             # Add download link instead of auto-download
#             download_link = f'<a href="{url_for("main.download_excel")}" target="_blank">📥 Download Excel</a>'
#             session["chat_history"].append({"role": "ai", "content": download_link})

#         session.modified = True
#         return render_template('form.html', chat_history=session["chat_history"])

#     return render_template('form.html')


# from flask import Blueprint, request, render_template, session, url_for
# from langchain.globals import set_llm_cache
# from langchain.cache import InMemoryCache


# set_llm_cache(InMemoryCache())


# query_cache = {}
# last_dataframe = None


# @main_bp.route('/chat', methods=['GET', 'POST'])
# def chat():
#     global last_dataframe

#     if "chat_history" not in session:
#         session["chat_history"] = []

#     if request.method == 'POST':
#         user_input = request.form.get('user_input')
#         session["chat_history"].append({"role": "user", "content": user_input})

#         # Call LangChain chain (LLM side is cached automatically)
#         result = chain.invoke({"question": user_input})
#         result_query = correct_and_format_sql_no_llm(result)

#         if is_valid_sql(result_query):
#             if result_query in query_cache:
#                 print("Using cached result for query:", result_query)
#                 data = query_cache[result_query]
#             else:
#                 data = get_data(query=result_query, engine=engine, db_type="mysql", credentials_path=credentials)
#                 query_cache[result_query] = data
#         else:
#             corrected_sql = correct_sql_query(result, llm_corrector=llm_corr)
#             corrected_sql = correct_and_format_sql_no_llm(corrected_sql)

#             if corrected_sql in query_cache:
#                 print("Using cached result for corrected query:", corrected_sql)
#                 data = query_cache[corrected_sql]
#             else:
#                 data = get_data(query=corrected_sql, engine=engine, db_type="mysql", credentials_path=credentials)
#                 query_cache[corrected_sql] = data


#         for col in data.select_dtypes(include='number').columns:
#             if col != "year":
#                 data[col] = data[col].map(number_formate)

#         last_dataframe = data   # Store for frontend download


#         if len(data) < 10:
#             html_table = get_llm_generated_html(data=data, llm_model=llm_corr)
#             print(html_table.content)
#             session["chat_history"].append({"role": "ai", "content": html_table.content})
#         else:
#             download_link = f'<a href="{url_for("main.download_excel")}" target="_blank">📥 Download Excel</a>'
#             session["chat_history"].append({"role": "ai", "content": download_link})

#         session.modified = True
#         return render_template('form.html', chat_history=session["chat_history"])

#     return render_template('form.html')



# @main_bp.route('/', methods=['GET'])
# def index():
#     """This route serves the main chat application page."""
#     return render_template('form.html')

# @main_bp.route('/chat', methods=['POST'])
# def chat():
#     """
#     This route handles the chat API request.
#     It receives a JSON payload and returns a JSON response.
#     """
#     data = request.get_json()
#     user_message = data.get('message', '')

#     # This is where your actual GPT logic would go.
#     # For now, we'll just send a mock response.
#     if user_message:
#         bot_response = f"Hello! You asked: '{user_message}'. How can I help you further?"
#     else:
#         bot_response = "I'm sorry, I didn't receive your message. Can you try again?"

#     return jsonify({"response": bot_response})


@main_bp.route("/connection")
def connection():
    return jsonify({"response":test_connection(credentials, query=TEST_QUERY)})



# @main_bp.route('/download_excel')
# def download_excel():
#     global last_dataframe
#     if last_dataframe is None:
#         return "No data available to download", 400

#     # Convert DataFrame to Excel in memory
#     output = io.BytesIO()
#     with pd.ExcelWriter(output, engine='openpyxl') as writer:
#         last_dataframe.to_excel(writer, index=False, sheet_name="Data")
#     output.seek(0)

#     return send_file(
#         output,
#         as_attachment=True,
#         download_name="retail_gpt_output.xlsx",
#         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )



@main_bp.route("/download_excel")
def download_excel():
    global last_dataframe
    if last_dataframe is None:
        return "No data available", 404

    output = io.BytesIO()
    last_dataframe.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="data.xlsx", as_attachment=True)