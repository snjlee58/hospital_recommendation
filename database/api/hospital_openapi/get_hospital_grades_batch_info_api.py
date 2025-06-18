import math
import time

import pandas as pd
from requests.exceptions import RequestException

from api import call_api
from api_config import ApiService, API_BASE_URLS, API_ENDPOINTS
from data_utils import extract_items_from_response, clean_dataframe
from db_utils import get_hospital_ids, upload_dataframe_ignore_dups

def fetch_all_hospital_grades(batch_size: int = 10, sleep_between: float = 0.1):
    """
    Fetch every page from the hospital-grades endpoint, concatenate, clean, and return a DataFrame.
    We'll then upload via upsert (ignoring duplicates on 'hospital_id').
    """
    # 1) First call: pageNo = 1
    page_no   = 1
    per_page  = batch_size  # number of rows per page (max the API lets you request)
    master_df = []

    while True:
        print(f"🔄 Fetching GRADES page {page_no} …")

        # 2) Build params for this page
        params = {
            "pageNo": page_no,
            "numOfRows": per_page,
            # We do NOT supply ykiho here, because this endpoint returns a list of *all* hospitals
        }

        try:
            # 3) Call the API
            response_json = call_api(
                base_url=API_BASE_URLS[ApiService.HOSP_GRADES],
                endpoint=API_ENDPOINTS[ApiService.HOSP_GRADES]["GRADES"],
                params=params
            )
            print("Raw JSON:", response_json)

            # 4) Extract DataFrame of the 'item' list
            page_df = extract_items_from_response(response_json)
            if page_df.empty:
                print("⚪️  This page returned no items. Stopping early.")
                break

            master_df.append(page_df)

            # 5) Determine if there are more pages
            body = response_json["response"]["body"]
            total_count = int(body.get("totalCount", 0))
            # Compute how many pages in total
            last_page = math.ceil(total_count / per_page)

            print(f"    • Retrieved {len(page_df)} rows (total so far = {sum(len(df) for df in master_df)})")
            print(f"    • totalCount = {total_count}, last_page = {last_page}\n")

            if page_no >= last_page:
                # we have fetched the final page
                break

            page_no += 1
            time.sleep(sleep_between)

        except RequestException as e:
            print(f"⚠️ Request exception on page {page_no}: {e}. Retrying in 5s …")
            time.sleep(5)
            continue
        except RuntimeError as re:
            print(f"🚨 Runtime error on page {page_no}: {re}. Aborting.")
            break

    # 6) Concatenate all pages
    if not master_df:
        print("❌ No grades data was fetched.")
        return pd.DataFrame() 

    all_grades_df = pd.concat(master_df, ignore_index=True)
    return all_grades_df


if __name__ == "__main__":
    raw_df = fetch_all_hospital_grades(batch_size=1000, sleep_between=0.1)
    if raw_df.empty:
        print("Nothing to clean / upload. Exiting.")
        exit()

    # 7) Clean column names, drop unwanted columns
    grades_df_clean = clean_dataframe(
        raw_df,
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
        },
        drop_columns=["addr", "clCd", "clCdNm", "yadmNm"]
    )

    # 1) Load the set of valid hospital IDs
    valid_ids = set(get_hospital_ids())

    # 2) Filter out any grades whose hospital_id isn’t in hospitals
    filtered = grades_df_clean[grades_df_clean["hospital_id"].isin(valid_ids)]

    print(f"⚪️ Dropping {len(grades_df_clean) - len(filtered)} rows with missing hospital_id in hospitals")
    

    # 8) Upsert into DB, ignoring duplicate hospital_ids
    #    (Assumes you have an upsert-capable utility, e.g. upload_dataframe_ignore_dups)
    upload_dataframe_ignore_dups(
        filtered,
        table_name="hospital_grades",
        pk=["hospital_id"]
    )

    print("✅ All hospital grades fetched, cleaned, and upserted.")
