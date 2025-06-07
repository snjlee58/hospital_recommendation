from db_utils import get_hospital_ids
from api import call_api
from api_config import ApiService, API_BASE_URLS, API_ENDPOINTS, API_PARAMS
from data_utils import extract_items_from_response, clean_dataframe
import pandas as pd
from db_utils import upload_dataframe_ignore_dups
import time
from requests.exceptions import RequestException

ids = get_hospital_ids()
    
# ---- Step 3: For each hospital, get hospital detail info by id and attach to table
department_master = []       # Will collect all department codes + names
hospital_dept_records = []   # Will collect each hospital's dept + count info

# Get detail information for each hospital using id
start_idx = 51600
request_count = 0
batch_size = 2000
for id in ids[start_idx:]:
    ## Log request count
    if request_count >= batch_size:
      break
    request_count += 1
    print(f"[{request_count}/{batch_size}]")
    try:
        time.sleep(0.1)

        ## API CALL (HOSP_DETAIL)
        detail_response = call_api(base_url=API_BASE_URLS[ApiService.HOSP_DETAIL], endpoint=API_ENDPOINTS[ApiService.HOSP_DETAIL]["SPECIALIST_COUNT_BY_DEPARTMENT"], params={
            "ykiho": id,
            "pageNo": 1,
            "numOfRows": 1000,
            "_type": "json"
        })
        print(f"Detail response for {id}: {detail_response}")

        detail_df = extract_items_from_response(detail_response)
        if detail_df.empty:
            print(f"ℹ️ No items for {id}, skipping.")
            continue
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
    except RuntimeError as e:
        msg = str(e)
        # detect “22” in the HTTP status or in the message
        if "22" in msg or "quota" in msg.lower() or "limited" in msg.lower():
            print(f"🔴 API quota exceeded at hospital_id={id}. Stopping early.")
            break
        else:
            print(f"⚠️ Runtime error for {id}: {e}. Skipping.")
            continue
    except RequestException as e:
        print(f"⚠️ Request failed for {id}: {e}")
        continue
    except Exception as e:
        print(f"❌ Unexpected error for {id}: {e}")
        continue

# Get review information for each hospital using Naver Blog API
# for name in df_clean["name"]:
#     print(f"🔍 Searching reviews for: {name}") # DEBUG
#     blog_posts = search_naver_blog(f"{name} 후기")

#     for post in blog_posts:
#         print("📝 Title:", post["title"])
#         print("🔗 Link:", post["link"])
#         print("📄 Desc:", post["description"])

#         content = get_blog_post_content(post["link"])
#         if content:
#             print("📝 Content Preview:", content[:200], "...")  # Print first 200 characters for preview
#         else:
#             print("📝 No content found.")
#         print("-" * 60)

# close_driver()


# # Combine and deduplicate department codes
departments_df = pd.concat(department_master).drop_duplicates().reset_index(drop=True)

# # Combine all hospital-department relations
hospital_departments_df = pd.concat(hospital_dept_records).reset_index(drop=True)


# ---- Step 4: Upload data to database
# # Upload department codes
upload_dataframe_ignore_dups(departments_df, table_name="departments", pk=["department_code"])
# # Upload hospital-department relations
upload_dataframe_ignore_dups(hospital_departments_df, table_name="hospital_departments", pk=["hospital_id", "department_code"])