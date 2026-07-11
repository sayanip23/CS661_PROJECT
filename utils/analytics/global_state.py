import pandas as pd
import threading
from utils.database import run_query
from utils.logger import get_logger

logger = get_logger(__name__)

class GlobalDataset:
    _instance = None
    _lock = threading.Lock()
    
    _df = None
    _companies = None
    _sectors = None
    _company_to_sector = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GlobalDataset, cls).__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Loads and precomputes the entire dataset into memory once."""
        logger.info("Initializing GlobalDataset (Memory Load)...")
        try:
            query = """
                SELECT 
                    Company, 
                    Sector, 
                    Date, 
                    Close, 
                    Volume, 
                    Turnover 
                FROM clean_stock_data 
                WHERE Close IS NOT NULL 
                ORDER BY Company, Date
            """
            df = run_query(query)
            if df.empty:
                logger.warning("GlobalDataset loaded an empty DataFrame.")
                self._df = pd.DataFrame()
                return

            df["Date"] = pd.to_datetime(df["Date"])
            df["Volume"] = df["Volume"].fillna(0)
            if "Turnover" in df.columns:
                df["Turnover"] = df["Turnover"].fillna(0)
                
            # Pre-compute Daily Return globally
            df["Daily_Return"] = df.groupby("Company")["Close"].pct_change()
            
            # Make it read-only-ish by storing it
            self._df = df
            
            # Cache metadata
            self._companies = sorted(df["Company"].unique().tolist())
            self._sectors = sorted(df["Sector"].dropna().unique().tolist())
            
            # Company -> Sector mapping
            self._company_to_sector = df.drop_duplicates(subset=["Company"]).set_index("Company")["Sector"].to_dict()
            
            logger.info(f"GlobalDataset initialized with {len(df)} rows.")
            
        except Exception as e:
            logger.error(f"Failed to initialize GlobalDataset: {e}")
            self._df = pd.DataFrame()

    def get_data(self) -> pd.DataFrame:
        """Returns a reference to the global dataframe. Do not mutate."""
        if self._df is None:
            self._initialize()
        return self._df
        
    def get_companies(self) -> list:
        if self._companies is None:
            self._initialize()
        return self._companies or []
        
    def get_sectors(self) -> list:
        if self._sectors is None:
            self._initialize()
        return self._sectors or []
        
    def get_company_sector_map(self) -> dict:
        if self._company_to_sector is None:
            self._initialize()
        return self._company_to_sector or {}

# Singleton Accessor
def get_global_data() -> pd.DataFrame:
    return GlobalDataset().get_data()

def get_global_company_sector_map() -> dict:
    return GlobalDataset().get_company_sector_map()
