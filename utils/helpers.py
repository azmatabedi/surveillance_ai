import cv2
from config import JPEG_QUALITY
from flask import Flask, render_template, request, redirect, url_for, session,current_app
from flask_mysqldb import MySQL
import MySQLdb.cursors
from sqlalchemy import text
import os
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy import text
from langchain.chains import create_sql_query_chain
from langchain_google_genai import ChatGoogleGenerativeAI
import re
import urllib.parse
import re
import datetime


# import face_recognition
import numpy as np
import cv2
import base64
from io import BytesIO
from PIL import Image
from flask import request, session, render_template, redirect, url_for
from sqlalchemy import text
def encode_jpeg(frame, quality=JPEG_QUALITY):
    params = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
    ok, buf = cv2.imencode('.jpg', frame, params)
    if not ok:
        ok, buf = cv2.imencode('.jpg', frame)
    return buf.tobytes() if ok else None


from sqlalchemy import create_engine
import urllib.parse

def get_engine():
    """
    Creates and returns a SQLAlchemy engine for connecting to the MySQL database.
    """

    # Database configuration
    user = "root"
    password = "Azm123at@1"
    host = "127.0.0.1"
    port = "3306"
    database = "surveillance"

    # Ensure required parameters are provided
    if not all([user, password, host, database]):
        raise ValueError("MySQL requires user, password, host, and database")

    # Encode password for safe URL usage
    encoded_password = urllib.parse.quote_plus(password)

    # Build connection string
    conn_str = f"mysql+pymysql://{user}:{encoded_password}@{host}:{port}/{database}"

    # Create and return engine
    engine = create_engine(conn_str,future=True)
    print("Database engine created successfully.")
    return engine



import os
import datetime
import cv2

def save_frame_to_file(basepath, frame, cameraip=None, directory="alerts"):
    """Saves a frame to a file and returns the path."""
    basepath="/static/alerts/10.25.78.240"
    # Check if the frame is a valid NumPy array and not empty
    if frame is None or frame.size == 0:
        print("Error: The frame is empty or invalid.")
        return None

    # Construct the full directory path
    full_directory_path = os.path.join(basepath, directory, cameraip)
    
    # Create the directory if it doesn't exist
    os.makedirs(full_directory_path, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    filename = f"alert_{timestamp}.jpg"
    
    # Construct the full file path
    filepath = os.path.join(full_directory_path, filename)

    # Attempt to write the file and check the return value
    success = cv2.imwrite(filepath, frame)
    if success:
        print(f"Image saved successfully to {filepath}")
        return filepath
    else:
        print(f"Error: Could not save the image to {filepath}.")
        return None
    
def save_alert_to_db(engine, ip, filepath):
    """Saves the camera IP, image path, and timestamp to the database."""

    query = text("""
        INSERT INTO tbl_event (cameraip, image_url, createddate)
        VALUES (:cameraip, :image_url, :created_at)
    """)

    data = {
        "cameraip": ip,
        "image_url": filepath,
        "created_at": datetime.datetime.now()
    }

    # Begin + auto commit when block exits
    with engine.begin() as conn:
        conn.execute(query, data)

    print("✅ Alert saved to DB")