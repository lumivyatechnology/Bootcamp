import pandas as pd      # Data manipulation and analysis
import numpy as np       # Numerical operations
import os
from sqlalchemy import create_engine
import logging

logger = logging.getLogger(__name__)


def run_etl(data_file: str):
    # ===========================================
    # LOAD RAW DATA
    # ===========================================
    # The CSV file contains scraped Samsung phone data from Amazon
    # Path is relative to this notebook's location


    # Load the CSV file into a pandas DataFrame
    df = pd.read_csv(data_file)


    # ===========================================
    # HANDLE MISSING PRICES
    # ===========================================
    missing_price_mask = df['price'].isna()
    num_missing = missing_price_mask.sum()

    logger.info(f"🔍 Found {num_missing} products with missing prices")

    # Generate random prices only for missing values
    if num_missing > 0:
        np.random.seed(42)  # Set seed for reproducibility
        random_prices = np.random.randint(300, 1001, size=num_missing)
        df.loc[missing_price_mask, 'price'] = random_prices
        logger.info(f"✅ Filled {num_missing} missing prices with random values ($300-$1000)")


    # ===========================================
    # DATA CLEANING
    # ===========================================
    # Create a copy of the DataFrame to preserve the original data
    df_clean = df.copy()

    # -----------------------------------------
    # 1. Handle Missing Categorical Values
    # -----------------------------------------
    # Drop rows where brand is empty or NaN (required field)
    df_clean = df_clean[df_clean['brand'].notna() & (df_clean['brand'] != '')]
    # df_clean['brand'] = df_clean['brand'].fillna('Not Specified')
    df_clean['operating_system'] = df_clean['operating_system'].fillna('Not Specified')
    df_clean['ram'] = df_clean['ram'].fillna('Not Specified')
    df_clean['cpu_model'] = df_clean['cpu_model'].fillna('Not Specified')
    df_clean['cpu_speed'] = df_clean['cpu_speed'].fillna('Not Specified')

    # -----------------------------------------
    # 2. Clean Ratings Count
    # -----------------------------------------
    # ratings_count may contain values like "(1,234)" 
    # We need to extract just the numeric part

    def clean_ratings(val):
        """
        Extract numeric value from ratings string.
        
        Examples:
            "(1,234)" -> 1234
            "500"     -> 500
            NaN       -> 0
        """
        if pd.isna(val):
            return 0
        # Remove parentheses and commas, then convert to int
        cleaned = str(val).replace('(', '').replace(')', '').replace(',', '')
        try:
            return int(cleaned)
        except ValueError:
            return 0

    df_clean['ratings_count'] = df_clean['ratings_count'].apply(clean_ratings)


    # ===========================================
    # TABLE 1: BRANDS (Lookup Table)
    # ===========================================
    # Extract unique brand names and assign IDs
    # This creates a reference table for brand information

    brands = df_clean['brand'].unique()
    brands_df = pd.DataFrame({
        'brand_id': range(1, len(brands) + 1),  # Primary Key (1, 2, 3, ...)
        'brand_name': brands                      # Brand name
    })

    # ===========================================
    # TABLE 2: OPERATING SYSTEMS (Lookup Table)
    # ===========================================
    # Extract unique operating system names and assign IDs

    operating_systems = df_clean['operating_system'].unique()
    os_df = pd.DataFrame({
        'os_id': range(1, len(operating_systems) + 1),  # Primary Key
        'os_name': operating_systems                      # OS name
    })

    # ===========================================
    # TABLE 3: CPU MODELS (Lookup Table)
    # ===========================================
    # Extract unique CPU model names and assign IDs

    cpu_models = df_clean['cpu_model'].unique()
    cpu_df = pd.DataFrame({
        'cpu_id': range(1, len(cpu_models) + 1),  # Primary Key
        'cpu_model': cpu_models                     # CPU model name
    })


    # ===========================================
    # TABLE 4: PHONES (Main Product Table)
    # ===========================================
    # This is the main table containing product information
    # It references the lookup tables via foreign keys

    # Create mapping dictionaries for foreign key lookups
    # These map the original values to their corresponding IDs
    brand_mapping = dict(zip(brands_df['brand_name'], brands_df['brand_id']))
    os_mapping = dict(zip(os_df['os_name'], os_df['os_id']))
    cpu_mapping = dict(zip(cpu_df['cpu_model'], cpu_df['cpu_id']))

    # Create the phones table with foreign keys
    phones_df = pd.DataFrame({
        'phone_id': range(1, len(df_clean) + 1),              # Primary Key
        'name': df_clean['name'].values,                       # Product name
        'price': df_clean['price'].values,                     # Price in USD
        'brand_id': df_clean['brand'].map(brand_mapping),      # FK -> brands.brand_id
        'os_id': df_clean['operating_system'].map(os_mapping), # FK -> operating_systems.os_id
        'ratings_count': df_clean['ratings_count'].values,     # Number of ratings
        'url': df_clean['url'].values                          # Product URL
    })

    # ===========================================
    # TABLE 5: PHONE SPECIFICATIONS (Technical Details)
    # ===========================================
    # This table stores technical specifications for each phone
    # It has a one-to-one relationship with the phones table

    phone_specs_df = pd.DataFrame({
        'spec_id': range(1, len(df_clean) + 1),                # Primary Key
        'phone_id': range(1, len(df_clean) + 1),               # FK -> phones.phone_id
        'ram': df_clean['ram'].values,                          # RAM specification
        'cpu_id': df_clean['cpu_model'].map(cpu_mapping),       # FK -> cpu_models.cpu_id
        'cpu_speed': df_clean['cpu_speed'].values               # CPU speed
    })

    # ===========================================
    # STEP 7: SAVE TO POSTGRESQL DATABASE
    # ===========================================
    # Export all normalized tables directly to a PostgreSQL database
    # Connection parameters are loaded from a .env file for security

    # -----------------------------------------
    # Load Environment Variables
    # -----------------------------------------
    # The .env file should contain:
    #   DB_HOST=localhost
    #   DB_PORT=5432
    #   DB_NAME=your_database
    #   DB_USER=your_username
    #   DB_PASSWORD=your_password

    # Get database connection parameters
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

    # Validate that all required variables are set
    required_vars = {'DB_HOST': DB_HOST, 'DB_PORT': DB_PORT, 'DB_NAME': DB_NAME, 'DB_USER': DB_USER, 'DB_PASSWORD': DB_PASSWORD}
    missing_vars = [k for k, v in required_vars.items() if not v]

    if missing_vars:
        logger.info(f"❌ Missing environment variables: {', '.join(missing_vars)}")
    else:
        # -----------------------------------------
        # Create Database Connection
        # -----------------------------------------
        # Connection string format: postgresql://user:password@host:port/database
        connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
        logger.info(f"🔗 Connecting to PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}/{DB_USER}")
        
        try:
            engine = create_engine(connection_string)
            
            # Test connection
            with engine.connect() as conn:
                logger.info("✅ Database connection successful!")
            
            # -----------------------------------------
            # Save Tables to Database
            # -----------------------------------------
            # Using if_exists='replace' to overwrite existing tables
            # Change to 'append' to add data to existing tables
            
            logger.info("\n📤 Uploading tables to database...")
            
            brands_df.to_sql('brands', engine, if_exists='replace', index=False)
            logger.info("   ✅ brands table created")
            
            os_df.to_sql('operating_systems', engine, if_exists='replace', index=False)
            logger.info("   ✅ operating_systems table created")
            
            cpu_df.to_sql('cpu_models', engine, if_exists='replace', index=False)
            logger.info("   ✅ cpu_models table created")
            
            phones_df.to_sql('phones', engine, if_exists='replace', index=False)
            logger.info("   ✅ phones table created")
            
            phone_specs_df.to_sql('phone_specs', engine, if_exists='replace', index=False)
            logger.info("   ✅ phone_specs table created")
            
            logger.info("\n" + "=" * 50)
            logger.info("DATABASE EXPORT COMPLETE")
            logger.info("=" * 50)
            logger.info("\n✅ All normalized tables saved to PostgreSQL!")
            logger.info(f"\n🗄️ Database: {DB_NAME}")
            logger.info("\n📋 Tables created:")
            logger.info(f"   1. brands ({len(brands_df)} records)")
            logger.info(f"   2. operating_systems ({len(os_df)} records)")
            logger.info(f"   3. cpu_models ({len(cpu_df)} records)")
            logger.info(f"   4. phones ({len(phones_df)} records)")
            logger.info(f"   5. phone_specs ({len(phone_specs_df)} records)")

        except Exception as e:
            logger.info(f"❌ Database connection failed: {e}")
            logger.info("\n💡 Make sure:")
            logger.info("   1. PostgreSQL server is running")
            logger.info("   2. Database exists")
            logger.info("   3. Credentials are correct")
