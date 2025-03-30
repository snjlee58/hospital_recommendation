from enum import Enum

class ApiService(Enum):
    HOSP_BASIC = "hosp_basic_info"
    HOSP_DETAIL = "hosp_detail_info"

API_BASE_URLS = {
    ApiService.HOSP_BASIC: "http://apis.data.go.kr/B551182/hospInfoServicev2", # 병원정보서비스 (https://www.data.go.kr/data/15001698/openapi.do#/)
    ApiService.HOSP_DETAIL: "http://apis.data.go.kr/B551182/MadmDtlInfoService2.7", # 의료기관별상세정보서비스 Medical Administration Detail Information (https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15001699)
}

API_ENDPOINTS = {
    ApiService.HOSP_BASIC: {
        "LIST": "/getHospBasisList", # 병원기본목록 
    },
    ApiService.HOSP_DETAIL: {
        "SPECIALIST_COUNT_BY_DEPARTMENT": "/getSpcSbjtSdrInfo2.7" # 전문과목별 전문의 수
    }
}

# Required (excluding ServiceKey) and optional parameters for each endpoint
API_PARAMS = {
    "/getHospBasisList": {
        "required": [],
        "optional": ["pageNo", "numOfRows", "sidoCd", "sgguCd", "emdongNm", "yadmNm", "zipCd", "clCd", "dgsbjtCd", "xPos", "yPos", "radius"]
    },

    "/getSpcSbjtSdrInfo2.7": {
        "required": ["ykiho"],
        "optional": ["pageNo", "numOfRows", "_type"]
    },

}
