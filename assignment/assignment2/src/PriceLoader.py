# PriceLoader.py
import os
import time
import requests
import pandas as pd
import yfinance as yf

class PriceLoader:
    def __init__(self, data_dir = "data"):
        self.data_dir = data_dir
        self.all_tickers = list()
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_sp500_tickers(self):
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers = headers)

        if response.status_code == 200:
            tables = pd.read_html(response.text)
            sp500_table = tables[0]
            tickers = sp500_table['Symbol'].tolist()
            tickers = [ticker.replace('.', '-') for ticker in tickers]
            return tickers
    
    def download_batch(self, tickers: list, start_date: str, end_date: str, batch_delay = 1) -> pd.DataFrame:
        data = yf.download(
            tickers,
            start = start_date,
            end = end_date,
            group_by = 'ticker',
            auto_adjust = True,
            threads = True,
            progress = True
        )
        
        # Add delay to respect API limits
        time.sleep(batch_delay)

        return data

    def download_all_sp500(self, start_date: str, end_date: str, batch_size = 50) -> pd.DataFrame:
        all_tickers = self.get_sp500_tickers()
        self.all_tickers = all_tickers
        all_data = pd.DataFrame()
        
        for i in range(0, len(all_tickers), batch_size):
            batch_num = i // batch_size + 1
            batch_tickers = all_tickers[i:i + batch_size]
            
            try:
                print(f"\nProcessing batch {batch_num}: {', '.join(batch_tickers)}")
                batch_data = self.download_batch(batch_tickers, start_date, end_date)

                if all_data.empty:
                    all_data = batch_data
                else:
                    all_data = pd.concat([all_data, batch_data], axis = 1)
                
            except Exception as e:
                print(f"Error processing batch {batch_num}: {e}")
                continue
        
        return all_data

    def save_to_parquet(self, dataframe: pd.DataFrame):
        save_count = 0
        for ticker in self.all_tickers:
            ticker_data = dataframe[ticker]['Close'].to_frame()
            ticker_filename = f"{ticker}.parquet"
            filepath = os.path.join(self.data_dir, ticker_filename)
            ticker_data.to_parquet(filepath)
            if save_count % 100 == 0:
                print(f"Saved {save_count + 1}/{len(self.all_tickers)}: {ticker_filename}")
            save_count += 1

    def load_from_parquet(self, filename: str):
        filepath = os.path.join(self.data_dir, filename)
        return pd.read_parquet(filepath)
    
    def load_all(self):
        """
        Helper func for Strategy Comparison notebook to aggregate parquets into single DataFrame of close prices.
        """
        prices = {}
        for filename in os.listdir(self.data_dir):
            if (filename.endswith('.parquet')) and (filename != 'sp500_data.parquet'):
                ticker = filename.replace('.parquet', '')
                df = pd.read_parquet(os.path.join(self.data_dir, filename))
                prices[ticker] = df['Close']
        return pd.DataFrame(prices)

def main():
    loader = PriceLoader(data_dir = "data")

    print("Starting S&P 500 data download...")
    print("=" * 60)
    
    sp500_data = loader.download_all_sp500(
        start_date = '2005-01-01',
        end_date = '2025-01-01',
        batch_size = 50
    )

    loader.save_to_parquet(sp500_data)
    
    # Show summary
    print("\n" + "=" * 60)
    print("Download complete!")
    print(f"Date range: {sp500_data.index[0]} to {sp500_data.index[-1]}")
    print(f"Number of tickers: {len(sp500_data.columns)}")
    print(f"Number of trading days: {len(sp500_data)}")
    print(f"\nFirst few rows:")
    print(sp500_data.head())
    print(f"\nData info:")
    print(sp500_data.info())


if __name__ == "__main__":
    main()
