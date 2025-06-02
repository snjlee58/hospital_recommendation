from db_utils import get_hospital_ids
from api import call_api
from api_config import ApiService, API_BASE_URLS, API_ENDPOINTS, API_PARAMS
from data_utils import extract_items_from_response, clean_dataframe
import pandas as pd
from db_utils import upload_dataframe
import time

ids = get_hospital_ids()
    
# ---- Step 3: For each hospital, get hospital detail info by id and attach to table
hospital_operating_hours_records = [] 

# Get detail information for each hospital using id
start_idx = 37173
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
        detail_response = call_api(base_url=API_BASE_URLS[ApiService.HOSP_DETAIL], endpoint=API_ENDPOINTS[ApiService.HOSP_DETAIL]["OPERATING_HOURS"], params={
            "serviceKey": "Fbq4OmxpKYD/RUVgN0+nZgm02P3BojouPbc4z3JApBzD39BllVOYadxrCb8evD0XHNbQUSSt8nwZanr5Vw7qDQ==",
            "ykiho": id,
            "pageNo": 1,
            "numOfRows": 1000,
            "_type": "json"
        })
        print(f"Detail response for {id}: {detail_response}")

        detail_df = extract_items_from_response(detail_response)
        if detail_df.empty:
            print(f"No data returned for hospital {id}")
            continue

        column_mapping = {
            "trmtMonStart": "monday_start",
            "trmtMonEnd": "monday_end",
            "trmtTueStart": "tuesday_start",
            "trmtTueEnd": "tuesday_end",
            "trmtWedStart": "wednesday_start",
            "trmtWedEnd": "wednesday_end",
            "trmtThuStart": "thursday_start",
            "trmtThuEnd": "thursday_end",
            "trmtFriStart": "friday_start",
            "trmtFriEnd": "friday_end",
            "trmtSatStart": "saturday_start",
            "trmtSatEnd": "saturday_end",
            "trmtSunStart": "sunday_start",
            "trmtSunEnd": "sunday_end",

            "lunchWeek": "lunch_weekday",
            "lunchSat": "lunch_saturday",

            "noTrmtSun": "closed_sunday",
            "noTrmtHoli": "closed_holiday",

            "emyDayYn": "emergency_open_day",
            "emyNgtYn": "emergency_open_night",
        }
        drop_columns = ["plcDir", "plcNm", "plcDist", "parkQty", "rcvSat", "rcvWeek", "parkXpnsYn", "parkEtc", "emyDayTelNo1", "emyDayTelNo2", "emyNgtTelNo1", "emyNgtTelNo2"]
        operating_hrs_df = clean_dataframe(detail_df, 
                                          column_mapping=column_mapping, 
                                          drop_columns=drop_columns,
                                          convert_bool_cols=["emergency_open_day", "emergency_open_night"])
        operating_hrs_df["hospital_id"] = id # retain hospital ID for join
        hospital_operating_hours_records.append(operating_hrs_df)

    except Exception as e:
        print(f"Failed to fetch details for {id}: {e}")

# ---- Step 4: Upload data to database
if hospital_operating_hours_records:
    combined_operating_hrs_df = pd.concat(hospital_operating_hours_records).reset_index(drop=True)
    upload_dataframe(combined_operating_hrs_df, table_name="hospital_operating_hours")



