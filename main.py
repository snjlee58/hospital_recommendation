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

params = {
    "pageNo": 1,
    "numOfRows": 100,
    "_type": "json"
}

response = call_api(
    base_url=base_url,
    endpoint=endpoint,
    params=params
)

# ---- Step 2: Extract and clean
df = extract_items_from_response(response)

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
df_clean = clean_dataframe(df, column_mapping=column_mapping, drop_columns=drop_columns, convert_float_cols=["lat", "lon"], fillna_text_cols=["name", "address", "tel"])

print(df_clean.head(20))

# ---- Step 3: For each hospital, get hospital detail info by id and attach to table
department_master = []       # Will collect all department codes + names
hospital_dept_records = []   # Will collect each hospital's dept + count info

for id in df_clean["id"]:
    service = ApiService.HOSP_DETAIL
    endpoint_key = "SPECIALIST_COUNT_BY_DEPARTMENT"
    endpoint = API_ENDPOINTS[service][endpoint_key]
    base_url = API_BASE_URLS[service]

    detail_params = {
        "ykiho": id,
        "pageNo": 1,
        "numOfRows": 100,
        "_type": "json"
    }

    try:
        detail_response = call_api(base_url=base_url, endpoint=endpoint, params=detail_params)
        # print(f"Detail response for {ykiho}: {detail_response}")

        detail_df = extract_items_from_response(detail_response)
        detail_df_clean = clean_dataframe(detail_df, 
                                          column_mapping={
                                              "dgsbjtCd": "department_code",
                                              "dgsbjtCdNm": "department_name",
                                              "dtlSdrCnt": "specialist_count"
                                              })
        detail_df_clean["hospital_id"] = id # retain hospital ID for join

        # Collect unique department codes and names
        department_master.append(detail_df_clean[["department_code", "department_name"]])

         # Collect hospital-department mapping
        hospital_dept_records.append(detail_df_clean[["hospital_id", "department_code", "specialist_count"]])

    except Exception as e:
        print(f"Failed to fetch details for {id}: {e}")

# Combine and deduplicate department codes
departments_df = pd.concat(department_master).drop_duplicates().reset_index(drop=True)
print(departments_df.head(20))

# Combine all hospital-department relations
hospital_departments_df = pd.concat(hospital_dept_records).reset_index(drop=True)
print(hospital_departments_df.head(20))

# ---- Step 4: Upload data to database
# Upload cleaned hospital metadata
# upload_dataframe(df_clean, table_name="hospitals")
# Upload department codes
upload_dataframe(departments_df, table_name="departments")
# Upload hospital-department relations
upload_dataframe(hospital_departments_df, table_name="hospital_departments")
