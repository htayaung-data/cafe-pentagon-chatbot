"""
Data loader for Cafe Pentagon Chatbot
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from src.config.settings import get_settings
from src.config.constants import DATA_FILES
from src.data.models import (
    MenuItem, FAQItem, ReservationConfig, Event, JobsConfig,
    MenuCategoryEnum, LanguageEnum
)
from src.utils.logger import get_logger, log_performance, LoggerMixin


class DataLoader(LoggerMixin):
    """
    Data loader for managing JSON data files
    """
    
    def __init__(self):
        """Initialize data loader"""
        self.settings = get_settings()
        self.data_dir = Path("data")  # Data directory where JSON files are located
        self.cached_data: Dict[str, Any] = {}
        self.logger.info("data_loader_initialized")
    
    @log_performance
    def load_json_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load JSON file from disk
        
        Args:
            filename: Name of the JSON file
            
        Returns:
            Parsed JSON data or None if failed
        """
        try:
            # Handle both relative and absolute paths
            if filename.startswith("data/"):
                file_path = Path(filename)
            else:
                file_path = self.data_dir / filename
            
            if not file_path.exists():
                self.logger.error("file_not_found", filename=filename, file_path=str(file_path))
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info("json_file_loaded", filename=filename, size=len(str(data)))
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error("json_decode_error", filename=filename, error=str(e))
            return None
        except Exception as e:
            self.logger.error("file_load_error", filename=filename, error=str(e))
            return None
    
    @log_performance
    def load_menu_data(self) -> List[MenuItem]:
        """
        Load menu data from JSON file
        
        Returns:
            List of menu items
        """
        cache_key = "menu_data"
        
        # Check cache first
        if cache_key in self.cached_data:
            self.logger.debug("menu_data_cache_hit")
            return self.cached_data[cache_key]
        
        # Load from file
        raw_data = self.load_json_file(DATA_FILES["menu"])
        if not raw_data:
            return []
        
        menu_items = []
        for item_data in raw_data:
            try:
                # Convert category string to enum
                if "category" in item_data:
                    try:
                        item_data["category"] = MenuCategoryEnum(item_data["category"])
                    except ValueError:
                        self.logger.warning("invalid_menu_category", category=item_data["category"])
                        continue
                
                # Create MenuItem object
                menu_item = MenuItem(**item_data)
                menu_items.append(menu_item)
                
            except Exception as e:
                self.logger.error("menu_item_parse_error", item_id=item_data.get("id"), error=str(e))
                continue
        
        # Cache the result
        self.cached_data[cache_key] = menu_items
        
        self.logger.info("menu_data_loaded", item_count=len(menu_items))
        return menu_items
    
    @log_performance
    def load_faq_data(self) -> List[FAQItem]:
        """
        Load FAQ data from JSON file
        
        Returns:
            List of FAQ items
        """
        cache_key = "faq_data"
        
        # Check cache first
        if cache_key in self.cached_data:
            self.logger.debug("faq_data_cache_hit")
            return self.cached_data[cache_key]
        
        # Load from file
        raw_data = self.load_json_file(DATA_FILES["faq"])
        if not raw_data:
            return []
        
        faq_items = []
        for item_data in raw_data:
            try:
                faq_item = FAQItem(**item_data)
                faq_items.append(faq_item)
                
            except Exception as e:
                self.logger.error("faq_item_parse_error", item_id=item_data.get("id"), error=str(e))
                continue
        
        # Cache the result
        self.cached_data[cache_key] = faq_items
        
        self.logger.info("faq_data_loaded", item_count=len(faq_items))
        return faq_items
    
    @log_performance
    def load_reservation_config(self) -> Optional[ReservationConfig]:
        """
        Load reservation configuration from JSON file
        
        Returns:
            Reservation configuration or None
        """
        cache_key = "reservation_config"
        
        # Check cache first
        if cache_key in self.cached_data:
            self.logger.debug("reservation_config_cache_hit")
            return self.cached_data[cache_key]
        
        # Load from file
        raw_data = self.load_json_file(DATA_FILES["reservations"])
        if not raw_data:
            return None
        
        try:
            config = ReservationConfig(**raw_data)
            
            # Cache the result
            self.cached_data[cache_key] = config
            
            self.logger.info("reservation_config_loaded", table_count=len(config.table_configuration))
            return config
            
        except Exception as e:
            self.logger.error("reservation_config_parse_error", error=str(e))
            return None
    
    @log_performance
    def load_events_data(self) -> List[Event]:
        """
        Load events data from JSON file
        
        Returns:
            List of events
        """
        cache_key = "events_data"
        
        # Check cache first
        if cache_key in self.cached_data:
            self.logger.debug("events_data_cache_hit")
            return self.cached_data[cache_key]
        
        # Load from file
        raw_data = self.load_json_file(DATA_FILES["events"])
        if not raw_data:
            return []
        
        events = []
        events_list = raw_data.get("events", [])
        
        for event_data in events_list:
            try:
                event = Event(**event_data)
                events.append(event)
                
            except Exception as e:
                self.logger.error("event_parse_error", event_id=event_data.get("event_id"), error=str(e))
                continue
        
        # Cache the result
        self.cached_data[cache_key] = events
        
        self.logger.info("events_data_loaded", event_count=len(events))
        return events
    
    @log_performance
    def load_jobs_data(self) -> Optional[JobsConfig]:
        """
        Load jobs data from JSON file
        
        Returns:
            Jobs configuration or None
        """
        cache_key = "jobs_data"
        
        # Check cache first
        if cache_key in self.cached_data:
            self.logger.debug("jobs_data_cache_hit")
            return self.cached_data[cache_key]
        
        # Load from file
        raw_data = self.load_json_file(DATA_FILES["jobs"])
        if not raw_data:
            return None
        
        try:
            config = JobsConfig(**raw_data)
            
            # Cache the result
            self.cached_data[cache_key] = config
            
            self.logger.info("jobs_data_loaded", position_count=len(config.positions))
            return config
            
        except Exception as e:
            self.logger.error("jobs_data_parse_error", error=str(e))
            return None
    
    def get_menu_by_category(self, category: MenuCategoryEnum) -> List[MenuItem]:
        """
        Get menu items by category
        
        Args:
            category: Menu category
            
        Returns:
            List of menu items in the category
        """
        menu_items = self.load_menu_data()
        return [item for item in menu_items if item.category == category]
    
    def get_menu_item_by_id(self, item_id: int) -> Optional[MenuItem]:
        """
        Get menu item by ID
        
        Args:
            item_id: Menu item ID
            
        Returns:
            Menu item or None if not found
        """
        menu_items = self.load_menu_data()
        for item in menu_items:
            if item.id == item_id:
                return item
        return None
    
    def search_menu_items(self, query: str, language: LanguageEnum = LanguageEnum.ENGLISH) -> List[MenuItem]:
        """
        Search menu items by name or description
        
        Args:
            query: Search query
            language: Language to search in
            
        Returns:
            List of matching menu items
        """
        menu_items = self.load_menu_data()
        query_lower = query.lower()
        results = []
        
        for item in menu_items:
            # Search in English
            if language == LanguageEnum.ENGLISH:
                if (query_lower in item.english_name.lower() or 
                    query_lower in item.description_en.lower()):
                    results.append(item)
            # Search in Burmese
            elif language == LanguageEnum.BURMESE:
                if (query_lower in item.myanmar_name.lower() or 
                    query_lower in item.description_mm.lower()):
                    results.append(item)
        
        return results
    
    def get_faq_by_category(self, category: str) -> List[FAQItem]:
        """
        Get FAQ items by category
        
        Args:
            category: FAQ category
            
        Returns:
            List of FAQ items in the category
        """
        faq_items = self.load_faq_data()
        return [item for item in faq_items if item.category == category]
    
    def search_faq(self, query: str, language: LanguageEnum = LanguageEnum.ENGLISH) -> List[FAQItem]:
        """
        Search FAQ items by question or answer
        
        Args:
            query: Search query
            language: Language to search in
            
        Returns:
            List of matching FAQ items
        """
        faq_items = self.load_faq_data()
        query_lower = query.lower()
        results = []
        
        for item in faq_items:
            # Search in English
            if language == LanguageEnum.ENGLISH:
                if (query_lower in item.question_en.lower() or 
                    query_lower in item.answer_en.lower()):
                    results.append(item)
            # Search in Burmese
            elif language == LanguageEnum.BURMESE:
                if (query_lower in item.question_mm.lower() or 
                    query_lower in item.answer_mm.lower()):
                    results.append(item)
        
        # Sort by priority
        results.sort(key=lambda x: x.priority, reverse=True)
        return results
    
    def get_available_tables(self, party_size: int) -> List[Any]:
        """
        Get available tables for a party size
        
        Args:
            party_size: Number of people
            
        Returns:
            List of available tables
        """
        config = self.load_reservation_config()
        if not config:
            return []
        
        available_tables = []
        for table in config.table_configuration:
            if (table.status == "available" and 
                table.capacity >= party_size):
                available_tables.append(table)
        
        return available_tables
    
    def get_upcoming_events(self) -> List[Event]:
        """
        Get upcoming events
        
        Returns:
            List of upcoming events
        """
        events = self.load_events_data()
        # Filter for upcoming events (status == "upcoming")
        return [event for event in events if event.status == "upcoming"]
    
    def get_open_job_positions(self) -> List[Any]:
        """
        Get open job positions
        
        Returns:
            List of open job positions
        """
        config = self.load_jobs_data()
        if not config:
            return []
        
        return [position for position in config.positions if position.status == "open"]
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cached_data.clear()
        self.logger.info("data_cache_cleared")
    
    def reload_all_data(self):
        """Reload all data from files"""
        self.clear_cache()
        
        # Reload all data types
        self.load_menu_data()
        self.load_faq_data()
        self.load_reservation_config()
        self.load_events_data()
        self.load_jobs_data()
        
        self.logger.info("all_data_reloaded")
    
    def get_data_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded data
        
        Returns:
            Data statistics
        """
        stats = {
            "menu_items": len(self.load_menu_data()),
            "faq_items": len(self.load_faq_data()),
            "events": len(self.load_events_data()),
            "open_jobs": len(self.get_open_job_positions()),
            "cached_data_types": len(self.cached_data)
        }
        
        # Add reservation config stats if available
        config = self.load_reservation_config()
        if config:
            stats["total_tables"] = len(config.table_configuration)
            stats["restaurant_capacity"] = config.restaurant_info.seating_capacity
        
        return stats


# Global data loader instance
_data_loader: Optional[DataLoader] = None


def get_data_loader() -> DataLoader:
    """Get or create data loader instance"""
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
    return _data_loader 