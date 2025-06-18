"""
RAG (Retrieval-Augmented Generation) analysis for hospital recommendation
"""
import time
from typing import List, Dict, Any
from app.ai.openai_client import OpenAIClient
from app.core.hospital_search import HospitalSearchEngine
from app.core.similarity_calculator import SimilarityCalculator


class RAGAnalyzer:
    """RAG analyzer for hospital recommendation service"""
    
    def __init__(self, openai_client: OpenAIClient = None, 
                 search_engine: HospitalSearchEngine = None):
        """
        Initialize RAG analyzer
        
        Args:
            openai_client: OpenAI client instance (optional)
            search_engine: Hospital search engine instance (optional)
        """
        self.openai_client = openai_client or OpenAIClient()
        self.search_engine = search_engine or HospitalSearchEngine()
        self.similarity_calculator = SimilarityCalculator(openai_client)
    
    def perform_rag_analysis(self, hospital_info: Dict[str, Any], 
                           query: str) -> Dict[str, Any]:
        """
        Perform RAG analysis for a single hospital
        
        Args:
            hospital_info: Hospital information with review
            query: User query
            
        Returns:
            Dict[str, Any]: Analysis result
        """
        hospital_name = hospital_info['name']
        review_summary = hospital_info['review']
        
        try:
            analysis = self.openai_client.analyze_with_rag(
                hospital_name, review_summary, query
            )
            
            return {
                'hospital_name': hospital_name,
                'analysis': analysis
            }
            
        except Exception as e:
            print(f"Error in RAG analysis for {hospital_name}: {str(e)}")
            return {
                'hospital_name': hospital_name,
                'analysis': "분석 중 오류가 발생했습니다."
            }
    
    def analyze_hospitals(self, hospitals: List[Dict[str, Any]], 
                         query: str, max_analysis: int = 3) -> List[Dict[str, Any]]:
        """
        Analyze multiple hospitals using RAG
        
        Args:
            hospitals: List of hospital information
            query: User query
            max_analysis: Maximum number of hospitals to analyze
            
        Returns:
            List[Dict[str, Any]]: Analysis results
        """
        print(f"\n=== 병원 분석 시작 ===")
        print(f"검색된 병원 수: {len(hospitals)}")
        
        if not hospitals:
            print("분석할 병원이 없습니다.")
            return []
        
        # Get hospital reviews for similarity calculation
        hospital_ids = [h['id'] for h in hospitals]
        print(f"\n1. 병원 리뷰 요약 데이터 조회 중...")
        
        hospital_reviews = self.search_engine.get_hospital_reviews(hospital_ids)
        if not hospital_reviews:
            print("리뷰 요약 데이터가 없습니다.")
            return []
        
        print(f"리뷰 요약 데이터 조회 완료: {len(hospital_reviews)}개")
        
        # Calculate similarity
        print(f"\n2. 유사도 계산 중...")
        similarity_results = self.similarity_calculator.calculate_similarity(
            query, hospital_reviews, top_k=len(hospital_reviews)
        )
        print("유사도 계산 완료")
        
        # Perform RAG analysis on top hospitals
        print(f"\n3. 상위 {max_analysis}개 병원 RAG 분석 시작...")
        results = []
        
        for i, sim_result in enumerate(similarity_results[:max_analysis]):
            hospital_name = sim_result['name']
            print(f"\n{i+1}순위 병원 분석 중: {hospital_name}")
            
            # Find original hospital info
            original_hospital = next(
                (h for h in hospitals if str(h['id']) == sim_result['hospital_id']), 
                None
            )
            if not original_hospital:
                print(f"원본 병원 정보를 찾을 수 없음: {sim_result['hospital_id']}")
                continue
            
            # Perform RAG analysis
            print(f"- RAG 분석 수행 중...")
            rag_analysis = self.perform_rag_analysis(sim_result, query)
            
            # Combine results
            result = {
                **original_hospital,
                'similarity': sim_result['similarity'],
                'rag_analysis': rag_analysis['analysis']
            }
            results.append(result)
            print(f"- 분석 완료 (유사도: {result['similarity']})")
            
            # Rate limiting
            if i < max_analysis - 1:
                time.sleep(2)
        
        print(f"\n=== 병원 분석 완료 ===")
        print(f"분석된 병원 수: {len(results)}")
        return results
    
    def analyze_with_similarity_and_rag(self, query: str, 
                                      city: str, district: str, 
                                      hospital_type: str, department: str,
                                      max_analysis: int = 3) -> List[Dict[str, Any]]:
        """
        Complete analysis pipeline: search → similarity → RAG
        
        Args:
            query: User query
            city: City name
            district: District name
            hospital_type: Hospital type
            department: Department name
            max_analysis: Maximum number of hospitals to analyze
            
        Returns:
            List[Dict[str, Any]]: Complete analysis results
        """
        # Step 1: Search hospitals
        hospitals = self.search_engine.search_hospitals(
            city, district, hospital_type, department
        )
        
        if not hospitals:
            print("검색된 병원이 없습니다.")
            return []
        
        # Step 2: Analyze with RAG
        return self.analyze_hospitals(hospitals, query, max_analysis) 