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
equipments_master = []       # Will collect all unique equipment codes + names
hospital_equipment_records = []   # Will collect each hospital's equipment + count info

# Get detail information for each hospital using id
start_idx = 31370
request_count = 0
batch_size = 5000
for id in ids[start_idx:]:
    ## Log request count
    if request_count >= batch_size:
      break
    request_count += 1
    print(f"[{request_count}/{batch_size}]")
    try:
        time.sleep(0.1)
        ## API CALL (HOSP_DETAIL)
        detail_response = call_api(base_url=API_BASE_URLS[ApiService.HOSP_DETAIL], endpoint=API_ENDPOINTS[ApiService.HOSP_DETAIL]["EQUIPMENT_INFO"], params={
            "serviceKey": "Fbq4OmxpKYD/RUVgN0+nZgm02P3BojouPbc4z3JApBzD39BllVOYadxrCb8evD0XHNbQUSSt8nwZanr5Vw7qDQ==",
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
                                              "oftCd": "equipment_code",
                                              "oftCdNm": "equipment_name",
                                              "oftCnt": "equipment_count"
                                              })
        detail_df_clean["hospital_id"] = id # retain hospital ID for join

        # Collect unique equipments codes and names
        equipments_master.append(detail_df_clean[["equipment_code", "equipment_name"]])

         # Collect hospital-equipments mapping
        hospital_equipment_records.append(detail_df_clean[["hospital_id", "equipment_code", "equipment_count"]])

    except RequestException as e:
        print(f"⚠️ Request failed for {id}: {e}")
        continue
    except Exception as e:
        print(f"❌ Unexpected error for {id}: {e}")
        continue

# # Combine and deduplicate equipment codes
equipments_df = pd.concat(equipments_master).drop_duplicates().reset_index(drop=True)

# # Combine all hospital-equipment relations
hospital_equipments_df = pd.concat(hospital_equipment_records).reset_index(drop=True)

# ---- Step 4: Upload data to database
# # Upload equipments codes
upload_dataframe_ignore_dups(equipments_df, table_name="equipments", pk=["equipment_code"])
# # Upload hospital-equipment relations
upload_dataframe_ignore_dups(hospital_equipments_df, table_name="hospital_equipments", pk=["hospital_id", "equipment_code"])

