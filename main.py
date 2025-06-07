from api import call_api
from api_config import ApiService, API_BASE_URLS, API_ENDPOINTS, API_PARAMS
from data_utils import extract_items_from_response, clean_dataframe
import pandas as pd
from db_utils import upload_dataframe

# Function to check API parameters
def get_api_data(service_enum, endpoint_key, user_params):
    endpoint = API_ENDPOINTS[service_enum][endpoint_key]
    base_url = API_BASE_URLS[service_enum]
    user_params["_type"] = "json"
    return call_api(service_enum.value, endpoint, user_params)

# ---- Step 1: Get basic hospital info API
service = ApiService.HOSP_BASIC
endpoint_key = "LIST"
endpoint = API_ENDPOINTS[service][endpoint_key]
base_url = API_BASE_URLS[service]

totalCount = 78779
numOfRows = 500
# totalPages = 2
totalPages = (totalCount // numOfRows) + (1 if totalCount % numOfRows > 0 else 0)
dataframes = []

for page in range(1, totalPages + 1):
    params = {
        "pageNo": page,
        "numOfRows": numOfRows,
        "_type": "json",
    }
    response = call_api(base_url, endpoint, params)
    df_page = extract_items_from_response(response)
    dataframes.append(df_page)
    print(f"Fetched page {page} of {totalPages}")
    print(df_page)

combined_df = pd.concat(dataframes, ignore_index=True)
print(combined_df)
combined_df.to_csv("all_data.csv", index=False)

# params = {
#     "pageNo": 1,
#     "numOfRows": 5,
#     "_type": "json"
# }

# response = call_api(
#     base_url=base_url,
#     endpoint=endpoint,
#     params=params
# )

# ---- Step 2: Extract and clean
# df = extract_items_from_response(response)

column_mapping = {
        "ykiho": "id",
        "yadmNm": "name",
        "clCd": "type_code",
        "clCdNm": "type_name",
        "sidoCd": "city_code",
        "sidoCdNm": "city_name",
        "sgguCd": "district_code",
        "sgguCdNm": "district_name",
        "emdongNm": "town",
        "addr": "address",
        "telno": "tel",
        "hospUrl": "url",
        "YPos": "lat",
        "XPos": "lon",
    }
drop_columns = ["postNo", "estbDd", "drTotCnt", "mdeptGdrCnt", "mdeptIntnCnt", "mdeptResdntCnt", "mdeptSdrCnt", "detyGdrCnt", "detyIntnCnt", "detyResdntCnt", "detySdrCnt", "cmdcGdrCnt", "cmdcIntnCnt", "cmdcResdntCnt", "cmdcSdrCnt", "pnursCnt"]
df_clean = clean_dataframe(combined_df, column_mapping=column_mapping, drop_columns=drop_columns, convert_float_cols=["lat", "lon"], fillna_text_cols=["name", "address", "tel"])

# print(df_clean.head(20))

#Extract unique city, district, hospital_type records
city_df = df_clean[['city_code', 'city_name']].drop_duplicates().reset_index(drop=True)
district_df = df_clean[['district_code', 'district_name']].drop_duplicates().reset_index(drop=True)
hospital_type_df = df_clean[['type_code', 'type_name']].drop_duplicates().reset_index(drop=True)

# Rename columns to match database schema
city_df.rename(columns={"city_code": "code", "city_name": "name"}, inplace=True) 
district_df.rename(columns={"district_code": "code", "district_name": "name"}, inplace=True) 
hospital_type_df.rename(columns={"type_code": "code", "type_name": "name"}, inplace=True)

# Remove the name columns from the hospital dataframe
hospitals_df = df_clean.drop(columns=["city_name", "district_name", "type_name"])

# Upload cleaned city, district, hospital_type hospital metadata
upload_dataframe(city_df, table_name="city") 
upload_dataframe(district_df, table_name="district") 
upload_dataframe(hospital_type_df, table_name="hospital_type") 
upload_dataframe(hospitals_df, table_name="hospitals")


