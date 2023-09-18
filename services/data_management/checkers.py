# --- check missing columns
import pandas as pd


def validate_columns(df, required_columns):
    if not set(required_columns).issubset(df.columns):
        missing_columns = list(set(required_columns) - set(df.columns))
        return missing_columns
    return None


def data_preprocessing(df,df_name):
    # Check for missing values
    missing_values_index = []
    duplicate_values_index = []


    if df.isnull().values.any():
        if df_name == 'responses':
            # Define the required columns
            required_columns = ['utter_name', 'text']
            missing_values_index =  df[df[required_columns].isnull().any(axis=1)].index.tolist()
            df.dropna(subset=required_columns, inplace=True)

        else:

            # Get the index of rows with missing values
            missing_values_index =  df[df.isnull().any(axis=1)].index.values.tolist()
            # # Handle missing values by  removing them
            df.dropna(inplace=True)

    # Check for duplicate rows
    if df.duplicated().any():
        # Get the index of rows with duplicate values
        duplicate_values_index =  df[df.duplicated()].index.values.tolist()
        # # Handle duplicate rows by removing them
        df.drop_duplicates(inplace=True)
        print(f"Type of df after reading CSV drop dupl: {type(df)}")
        # Ensure that df is always a DataFrame, even if it's empty
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame()
    return df,missing_values_index, duplicate_values_index
