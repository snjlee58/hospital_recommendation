"""
Hospital search functionality for recommendation service
"""
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.engine import Engine
from app.utils.database import get_database_connection


class HospitalSearchEngine:
    """Hospital search engine for recommendation service"""
    
    def __init__(self, engine: Engine = None):
        """
        Initialize hospital search engine
        
        Args:
            engine: SQLAlchemy engine instance (optional)
        """
        self.engine = engine or get_database_connection()
    
    def search_hospitals(self, city_name: str, district_name: str, 
                        hospital_type_name: str, department_name: str, 
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search hospitals matching the specified filters
        
        Args:
            city_name: City name
            district_name: District name
            hospital_type_name: Hospital type name
            department_name: Department name
            limit: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: List of hospital information
        """
        query = text("""
            SELECT h.name, h.address, h.tel, h.url, h.id
            FROM hospitals h
            JOIN city c ON h.city_code = c.code
            JOIN district d ON h.district_code = d.code
            JOIN hospital_type ht ON h.type_code = ht.code
            JOIN hospital_departments hd ON h.id = hd.hospital_id
            JOIN departments dp ON hd.department_code = dp.department_code
            WHERE c.name = :city
              AND d.name = :district
              AND ht.name = :hospital_type
              AND dp.department_name = :department
            LIMIT :limit
        """)

        with self.engine.connect() as conn:
            result = conn.execute(query, {
                "city": city_name,
                "district": district_name,
                "hospital_type": hospital_type_name,
                "department": department_name,
                "limit": limit
            })
            return result.mappings().all()
    
    def get_hospital_reviews(self, hospital_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Get hospital review summaries with embeddings
        
        Args:
            hospital_ids: List of hospital IDs
            
        Returns:
            List[Dict[str, Any]]: List of hospital review information
        """
        if not hospital_ids:
            return []
            
        query = text("""
            SELECT rs.hospital_id as hospital_id, h.name as name, 
                   rs.review as review, rs.embedding as embedding
            FROM review_summaries rs
            JOIN hospitals h ON rs.hospital_id = h.id
            WHERE rs.hospital_id IN :hospital_ids
        """)

        with self.engine.connect() as conn:
            result = conn.execute(query, {"hospital_ids": tuple(hospital_ids)})
            return result.mappings().all()
    
    def search_by_location_only(self, city_name: str, district_name: str, 
                               limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search hospitals by location only
        
        Args:
            city_name: City name
            district_name: District name
            limit: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: List of hospital information
        """
        query = text("""
            SELECT h.name, h.address, h.tel, h.url, h.id
            FROM hospitals h
            JOIN city c ON h.city_code = c.code
            JOIN district d ON h.district_code = d.code
            WHERE c.name = :city
              AND d.name = :district
            LIMIT :limit
        """)

        with self.engine.connect() as conn:
            result = conn.execute(query, {
                "city": city_name,
                "district": district_name,
                "limit": limit
            })
            return result.mappings().all()


# Backward compatibility function
def search_hospitals(city_name: str, district_name: str, 
                    hospital_type_name: str, department_name: str, 
                    engine: Engine) -> List[Dict[str, Any]]:
    """
    Backward compatibility function for hospital search
    
    Args:
        city_name: City name
        district_name: District name
        hospital_type_name: Hospital type name
        department_name: Department name
        engine: SQLAlchemy engine instance
        
    Returns:
        List[Dict[str, Any]]: List of hospital information
    """
    search_engine = HospitalSearchEngine(engine)
    return search_engine.search_hospitals(city_name, district_name, 
                                        hospital_type_name, department_name) 