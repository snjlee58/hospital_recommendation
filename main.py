from api import call_api
from api_config import ApiService, API_BASE_URLS, API_ENDPOINTS, API_PARAMS
from data_utils import extract_items_from_response, clean_dataframe
import pandas as pd
from db_utils import upload_dataframe
from naver_api import search_naver_blog
from naver_blog_crawler import get_blog_post_content, close_driver

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
    "numOfRows": 5,
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

# print(df_clean.head(20))

# ---- Step 3: For each hospital, get hospital detail info by id and attach to table
department_master = []       # Will collect all department codes + names
hospital_dept_records = []   # Will collect each hospital's dept + count info
hospital_grade_records = [] # To collect each hospital's grade info

# Get detail information for each hospital using id
for id in df_clean["id"]:
    try:
        ## API CALL (HOSP_DETAIL)
        detail_response = call_api(base_url=API_BASE_URLS[ApiService.HOSP_DETAIL], endpoint=API_ENDPOINTS[ApiService.HOSP_DETAIL]["SPECIALIST_COUNT_BY_DEPARTMENT"], params={
            "ykiho": id,
            "pageNo": 1,
            "numOfRows": 10,
            "_type": "json"
        })
        print(f"Detail response for {id}: {detail_response}")

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

         ## API CALL (HOSP_GRADES)
        grade_response = call_api(
            base_url=API_BASE_URLS[ApiService.HOSP_GRADES],
            endpoint=API_ENDPOINTS[ApiService.HOSP_GRADES]["GRADES"],
            params={
                "serviceKey": "GTDvWSPwxWuonrDpSoJFdpfsGL10NYvxqG3hCEwNTdMp39xqNkgVUXR7+ywZsErmVoAtkLW18guG1SgF6Dcnaw==",
                "pageNo": 1,
                "numOfRows": 10,
                "ykiho": id,
                "_type": "json"
            }
        )
        print(f"Grade response for {id}: {grade_response}")
        grades_df = extract_items_from_response(grade_response)
        grades_df_clean = clean_dataframe(
            grades_df,
            column_mapping={
                "ykiho": "hospital_id",
                "asmGrd01": "asmgrd01",
                "asmGrd02": "asmgrd02",
                "asmGrd03": "asmgrd03",
                "asmGrd04": "asmgrd04",
                "asmGrd05": "asmgrd05",
                "asmGrd06": "asmgrd06",
                "asmGrd07": "asmgrd07",
                "asmGrd08": "asmgrd08",
                "asmGrd09": "asmgrd09",
                "asmGrd10": "asmgrd10",
                "asmGrd11": "asmgrd11",
                "asmGrd12": "asmgrd12",
                "asmGrd13": "asmgrd13",
                "asmGrd14": "asmgrd14",
                "asmGrd15": "asmgrd15",
                "asmGrd16": "asmgrd16",
                "asmGrd17": "asmgrd17",
                "asmGrd18": "asmgrd18",
                "asmGrd19": "asmgrd19",
                "asmGrd20": "asmgrd20",
                "asmGrd21": "asmgrd21",
                "asmGrd22": "asmgrd22",
                "asmGrd23": "asmgrd23",
                "asmGrd24": "asmgrd24",
                # You can add more mappings if you need to rename asmGrdXX fields
            },
            drop_columns=["addr", "clCd", "clCdNm", "yadmNm"]
        )
        hospital_grade_records.append(grades_df_clean)

    except Exception as e:
        print(f"Failed to fetch details for {id}: {e}")

# Get review information for each hospital using Naver Blog API
for name in df_clean["name"]:
    print(f"🔍 Searching reviews for: {name}") # DEBUG
    blog_posts = search_naver_blog(f"{name} 후기")

    for post in blog_posts:
        print("📝 Title:", post["title"])
        print("🔗 Link:", post["link"])
        print("📄 Desc:", post["description"])

        content = get_blog_post_content(post["link"])
        if content:
            print("📝 Content Preview:", content[:200], "...")  # Print first 200 characters for preview
        else:
            print("📝 No content found.")
        print("-" * 60)

close_driver()


# Combine and deduplicate department codes
departments_df = pd.concat(department_master).drop_duplicates().reset_index(drop=True)
# print(departments_df.head(20))

# Combine all hospital-department relations
hospital_departments_df = pd.concat(hospital_dept_records).reset_index(drop=True)
# print(hospital_departments_df.head(20))

combined_grades_df = pd.concat(hospital_grade_records).reset_index(drop=True) 

# ---- Step 4: Upload data to database
# # Upload cleaned hospital metadata
# upload_dataframe(df_clean, table_name="hospitals")
# # Upload department codes
# upload_dataframe(departments_df, table_name="departments")
# # Upload hospital-department relations
# upload_dataframe(hospital_departments_df, table_name="hospital_departments")
# # Upload hospital grades
# upload_dataframe(combined_grades_df, table_name="hospital_grades") 
